from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent_service.graph.react_loop import DiagnosisReActLoop
from agent_service.graph.runtime import report_stage, trace_step
from agent_service.graph.specialists import SPECIALIST_AGENTS, specialist_for_skill
from agent_service.graph.state import AgentGraphState, SkillExecutionResult, ToolObservation
from agent_service.graph.tool_resolver import KNOWLEDGE_EVIDENCE_TYPES
from agent_service.llm.prompts.diagnosis import DIMENSION_LABELS
from agent_service.observability.trace import run_with_trace

_ANSWER_FIELDS = (
  "outcome",
  "finding_type",
  "observation",
  "difference_text",
  "hypothesis_text",
  "suggested_action",
  "evidence_refs",
  "confidence",
  "reason",
)


def diagnose_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
  """
  执行 Diagnosis Skill。外层确定性调度，单个 Skill 内允许有限 ReAct。

  三种模式：
  - 常规：按 plan / skills_to_run 并行跑 Specialist（可能带 Evaluator 的重试反馈）；
  - 定向复查（active_handoff）：被询问方回答一个具体问题。答复单独存进 ``handoff_answers``，
    **不覆盖**被询问方原本的完整诊断；然后进入回调；
  - 回调整合（pending_integration）：提问方拿着答复完成自己的结论，替换掉 NEEDS_CAPABILITY。
  """
  harness = config["configurable"]["harness"]
  harness_ctx = config["configurable"]["harness_ctx"]

  plan = list(state.get("plan") or [])
  pending_integration = state.get("pending_integration")
  active_handoff = None if pending_integration else state.get("active_handoff")
  mode = "integration" if pending_integration else ("targeted" if active_handoff else "normal")

  if mode == "integration":
    source_agent = str(pending_integration["source_agent"])
    skills = [item for item in plan if item.get("agent_id") == source_agent]
  else:
    requested_agents = list(state.get("agents_to_run") or [])
    requested_skills = list(state.get("skills_to_run") or [])
    if requested_agents:
      skills = [item for item in plan if item.get("agent_id") in requested_agents]
    else:
      skills = [item for item in plan if item["skill_key"] in (requested_skills or [row["skill_key"] for row in plan])]
  if not skills:
    return {"next_action": "evaluate", "done": False, "pending_integration": None, "active_handoff": None}

  retry_feedback = dict(state.get("retry_feedback") or {}) if mode == "normal" else {}

  with trace_step(
    state,
    "parallel_diagnosis_skills" if mode == "normal" else f"diagnosis_{mode}",
    input_summary=f"mode={mode} skills=" + ",".join(item["skill_key"] for item in skills),
  ) as step:
    job_context = state.get("job_context") or {}
    evidence_pack = state.get("evidence_pack") or {}
    prior_observations = list(state.get("tool_observations") or [])
    if mode == "normal" and not state.get("evaluation_results"):
      for skill in skills:
        report_stage(
          state,
          config,
          _stage_for_skill(skill["skill_key"]),
          _percent_for_skill(skill["skill_key"]),
          f"Running {skill['skill_key']}.",
        )
    skill_results = _run_skills(
      skills,
      state["job_id"],
      job_context,
      evidence_pack,
      harness,
      harness_ctx,
      active_handoff=active_handoff,
      handoff_answer=(pending_integration or {}).get("answer"),
      retry_feedback=retry_feedback,
      routing_history=list(state.get("routing_history") or []),
      max_agent_handoffs=int(state.get("max_agent_handoffs") or 2),
      prior_observations=prior_observations,
    )

    handoff_answers = list(state.get("handoff_answers") or [])
    next_pending: dict[str, Any] | None = None
    if mode == "targeted":
      # 被询问方的结果只作为“答复”，不替换它原本的 Finding
      new_findings: list[dict[str, Any]] = []
      answer = _build_answer(active_handoff or {}, skill_results)
      handoff_answers.append(answer)
      next_pending = {"source_agent": answer["from_agent"], "answer": answer}
    else:
      new_findings = [dict(item["finding"]) for item in skill_results if item.get("finding")]
      if mode == "integration":
        new_findings = [_attach_answer(finding, pending_integration["answer"]) for finding in new_findings]

    findings = _replace_findings(list(state.get("findings") or []), new_findings)
    evidence_refs = list(dict.fromkeys([ref for finding in findings for ref in finding.get("evidence_refs", [])]))
    knowledge_evidence_refs = list(
      dict.fromkeys([ref for finding in findings for ref in finding.get("knowledge_evidence_refs", [])])
    )
    evidence_gaps = [gap for finding in findings for gap in finding.get("evidence_gaps", [])]
    react_iterations = dict(state.get("react_iterations_by_skill") or {})
    skill_status = dict(state.get("skill_execution_status") or {})
    tool_observations: list[ToolObservation] = list(state.get("tool_observations") or [])
    knowledge_observations: list[ToolObservation] = list(state.get("knowledge_observations") or [])
    retrieval_traces = list(state.get("retrieval_traces") or [])
    traces = list(state.get("step_traces") or [])
    handoff_requests = list(state.get("handoff_requests") or [])
    agent_states = dict(state.get("agent_states") or {})
    for item in skill_results:
      skill_code = str(item.get("skill_code"))
      agent_id = str(item.get("agent_id") or specialist_for_skill(skill_code).agent_id)
      if mode != "targeted":  # 定向复查不改变被询问方自己的执行状态
        react_iterations[skill_code] = int(item.get("react_iterations") or 0)
        skill_status[skill_code] = str(item.get("status") or "")
      agent_states[agent_id] = {
        **dict(agent_states.get(agent_id) or {}),
        "skillCode": skill_code,
        "status": item.get("status") or "",
        "outcome": (item.get("specialist_result") or item.get("finding") or {}).get("outcome", ""),
        "reactIterations": int(item.get("react_iterations") or 0),
        "evidenceRefs": list(item.get("evidence_refs") or []),
        "lastMode": mode,
      }
      handoff_requests.extend(item.get("handoff_requests") or [])
      observations = list(item.get("observations") or [])
      tool_observations.extend(observations)
      for observation in observations:
        if observation.get("knowledge_evidence_refs"):
          knowledge_observations.append(observation)
        if observation.get("retrieval_trace"):
          retrieval_traces.append(dict(observation["retrieval_trace"]))
      traces.extend(item.get("step_traces") or [])

    observations = list(state.get("draft_observations", []))
    for finding in new_findings:
      label = DIMENSION_LABELS.get(finding.get("dimension", ""), finding.get("dimension", ""))
      observations.append(f"{label}:{finding.get('observation', '')}")

    step["output_summary"] = (
      f"mode={mode} skill_results={len(skill_results)} findings={len(new_findings)} gaps={len(evidence_gaps)}"
    )
    failed = [item for item in skill_results if item.get("status") == "FAILED"]
    update: dict[str, Any] = {
      "current_skill": skills[-1]["skill_key"],
      "agents_to_run": [next_pending["source_agent"]] if next_pending else [],
      "skills_to_run": [],
      "active_handoff": None,
      "pending_integration": next_pending,
      "handoff_answers": handoff_answers,
      "retry_feedback": {},
      "agent_states": agent_states,
      "handoff_requests": handoff_requests,
      "findings": findings,
      "draft_hypotheses": findings,
      "evidence_refs": evidence_refs,
      "knowledge_evidence_refs": knowledge_evidence_refs,
      "evidence_gaps": evidence_gaps,
      "react_iterations_by_skill": react_iterations,
      "tool_observations": tool_observations,
      "knowledge_observations": knowledge_observations,
      "retrieval_traces": retrieval_traces,
      "current_observation": tool_observations[-1] if tool_observations else state.get("current_observation"),
      "skill_execution_status": skill_status,
      "draft_observations": observations,
      "status": "RUNNING",
      "error": "; ".join(str(item.get("error")) for item in failed),
      # 定向复查之后不经过 Evaluator，直接回调提问方
      "next_action": "diagnose" if next_pending else "evaluate",
      "done": False,
      "step_traces": traces,
    }
    return update


def _build_answer(request: dict[str, Any], skill_results: list[SkillExecutionResult]) -> dict[str, Any]:
  result = skill_results[0] if skill_results else {}
  finding = dict(result.get("finding") or {})
  answered = result.get("status") == "COMPLETED" and finding.get("outcome") == "FINDING"
  return {
    "request_id": str(request.get("request_id") or ""),
    "from_agent": str(request.get("from_agent") or ""),
    "to_agent": str(result.get("agent_id") or ""),
    "target_capability": str(request.get("target_capability") or ""),
    "question": str(request.get("question") or ""),
    "status": "ANSWERED" if answered else "UNANSWERED",
    "error": str(result.get("error") or ""),
    "answer": {key: finding.get(key) for key in _ANSWER_FIELDS if key in finding},
  }


def _attach_answer(finding: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
  """把答复的证据并入提问方的结论，并留下可追溯的记录。"""
  merged = dict(finding)
  answer_refs = [str(ref) for ref in (answer.get("answer") or {}).get("evidence_refs") or []]
  if answer.get("status") == "ANSWERED" and answer_refs:
    merged["evidence_refs"] = list(dict.fromkeys([*list(merged.get("evidence_refs") or []), *answer_refs]))
  merged["handoff_answer"] = {
    "requestId": answer.get("request_id"),
    "toAgent": answer.get("to_agent"),
    "question": answer.get("question"),
    "status": answer.get("status"),
  }
  return merged


def _run_skills(
  skills: list[dict[str, Any]],
  job_id: str,
  job_context: dict[str, Any],
  evidence_pack: dict[str, Any],
  harness: Any,
  harness_ctx: Any,
  active_handoff: dict[str, Any] | None = None,
  handoff_answer: dict[str, Any] | None = None,
  retry_feedback: dict[str, list[str]] | None = None,
  routing_history: list[dict[str, Any]] | None = None,
  max_agent_handoffs: int = 2,
  prior_observations: list[ToolObservation] | None = None,
) -> list[SkillExecutionResult]:
  def build(skill: dict[str, Any]) -> DiagnosisReActLoop:
    seeded_observations = _observations_for_skill(skill["skill_key"], prior_observations or [])
    return DiagnosisReActLoop(
      skill=skill,
      agent=SPECIALIST_AGENTS.get(str(skill.get("agent_id"))),
      handoff=active_handoff,
      handoff_answer=handoff_answer,
      evaluator_feedback=list((retry_feedback or {}).get(skill["skill_key"]) or []),
      routing_history=list(routing_history or []),
      max_agent_handoffs=max_agent_handoffs,
      job_id=job_id,
      job_context=job_context,
      evidence_pack=dict(evidence_pack),
      harness=harness,
      harness_ctx=harness_ctx,
      observations=seeded_observations,
      seeded_observation_count=len(seeded_observations),
    )

  if len(skills) <= 1:
    return [build(skill).run() for skill in skills]

  results: list[SkillExecutionResult] = []
  with ThreadPoolExecutor(max_workers=len(skills)) as executor:
    # 三个专家并行跑在子线程里：把 trace_id / job_id 带过去，专家的日志也能按 agentRunId 搜到
    futures = [executor.submit(run_with_trace(build(skill).run)) for skill in skills]
    for future in as_completed(futures):
      results.append(future.result())

  order = {skill["skill_key"]: index for index, skill in enumerate(skills)}
  return sorted(results, key=lambda item: order.get(str(item.get("skill_code")), 999))


def _observations_for_skill(skill_key: str, observations: list[ToolObservation]) -> list[ToolObservation]:
  """Carry retry observations forward without leaking other skills' retrieved knowledge."""
  selected: list[ToolObservation] = []
  for observation in observations:
    if observation.get("observation_type") not in KNOWLEDGE_EVIDENCE_TYPES:
      selected.append(observation)
      continue
    trace = dict(observation.get("retrieval_trace") or {})
    if trace.get("skill_code") == skill_key:
      selected.append(observation)
  return selected


def _replace_findings(
  existing: list[dict[str, Any]],
  replacements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  by_skill = {str(item.get("skill_key")): item for item in existing}
  for item in replacements:
    by_skill[str(item.get("skill_key"))] = item
  return list(by_skill.values())


def _stage_for_skill(skill_key: str) -> str:
  return {
    "hook_analysis": "HOOK_ANALYSIS",
    "structure_rhythm_analysis": "STRUCTURE_RHYTHM_ANALYSIS",
    "value_delivery_analysis": "VALUE_DELIVERY_ANALYSIS",
  }.get(skill_key, "RUNNING")


def _percent_for_skill(skill_key: str) -> int:
  return {
    "hook_analysis": 70,
    "structure_rhythm_analysis": 76,
    "value_delivery_analysis": 82,
  }.get(skill_key, 75)
