from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_service.config import get_settings
from agent_service.graph.criteria import criteria_for_dimension
from agent_service.graph.diagnosis_skill import run_diagnosis_skill
from agent_service.graph.evidence_timeline import TARGET_ALIAS, has_text_evidence, parse_timeline
from agent_service.graph.result_contract import (
  evaluate_handoff_gate,
  make_abstain_result,
  normalize_specialist_result,
  rejected_handoff_to_abstain,
)
from agent_service.graph.rubric import job_category, rubric_items, rubric_query
from agent_service.graph.runtime import utc_now
from agent_service.graph.specialists import SpecialistAgentDefinition, specialist_for_skill
from agent_service.graph.state import (
  DiagnosisPlanItem,
  ReasoningDecision,
  SkillExecutionResult,
  StepTrace,
  ToolObservation,
)
from agent_service.graph.tool_resolver import (
  DOMAIN_KNOWLEDGE,
  FRAME_TEXT,
  JOB_EVIDENCE,
  KEY_FRAME,
  KNOWLEDGE_EVIDENCE_TYPES,
  RUBRIC,
  VIDEO_METADATA,
  ToolResolutionError,
  resolve_tool_request,
)
from agent_service.harness.context import harness_scope


@dataclass
class DiagnosisReActLoop:
  """Bounded local ReAct loop for one Diagnosis Skill."""

  skill: DiagnosisPlanItem
  job_id: str
  job_context: dict[str, Any]
  evidence_pack: dict[str, Any]
  harness: Any
  harness_ctx: Any
  agent: SpecialistAgentDefinition | None = None
  handoff: dict[str, Any] | None = None
  handoff_answer: dict[str, Any] | None = None
  evaluator_feedback: list[str] = field(default_factory=list)
  routing_history: list[dict[str, Any]] = field(default_factory=list)
  max_agent_handoffs: int = 2
  max_iterations: int | None = None
  observations: list[ToolObservation] = field(default_factory=list)
  seeded_observation_count: int = 0
  step_traces: list[StepTrace] = field(default_factory=list)

  def run(self) -> SkillExecutionResult:
    # 在本线程绑定 harness 作用域：之后的模型/工具调用都能知道是哪个 Specialist 发起的
    # （ContextVar 不会自动传进线程池，所以必须在线程内部绑定）。
    with harness_scope(self.harness, self.harness_ctx, agent_id=self._agent().agent_id):
      return self._run_loop()

  def _run_loop(self) -> SkillExecutionResult:
    limit = self.max_iterations or get_settings().max_react_iterations
    skill_key = self.skill["skill_key"]
    agent = self._agent()
    last_decision: ReasoningDecision | None = None

    for iteration in range(1, limit + 1):
      try:
        decision = self._record_reason(iteration)
      except Exception as exc:  # noqa: BLE001 - Specialist 边界：LLM/解析失败只让本维度失败，不拖垮整个 run
        return self._failed(iteration, f"Specialist reasoning failed: {exc}")
      last_decision = decision

      if decision["status"] == "FINAL":
        finding = normalize_specialist_result(dict(decision.get("finding") or {}), self.skill)
        gate = evaluate_handoff_gate(
          result=finding,
          agent=agent,
          routing_history=self.routing_history,
          max_agent_handoffs=self.max_agent_handoffs,
          # 定向复查（回答别人的问题）和整合答复（回调）阶段都不允许再发起新的交接
          active_handoff=self.handoff or self.handoff_answer,
        )
        handoff_requests = [gate.request] if gate.accepted and gate.request else []
        if finding.get("outcome") == "NEEDS_CAPABILITY" and not gate.accepted:
          self._record_simple_step("HANDOFF_GATE_REJECTED", iteration, "SUCCESS", gate.reason)
          finding = rejected_handoff_to_abstain(self.skill, finding, gate.reason)
        elif gate.accepted:
          self._record_simple_step("HANDOFF_GATE_ACCEPTED", iteration, "SUCCESS", gate.reason)
        self._record_simple_step("SPECIALIST_RESULT", iteration, "SUCCESS", str(finding.get("outcome") or ""))
        if finding.get("outcome") == "ABSTAIN":
          self._record_simple_step("ABSTAIN", iteration, "SUCCESS", str(finding.get("reason") or ""))
        self._record_simple_step("FINAL", iteration, "SUCCESS", decision.get("reasoning_summary", ""))
        return {
          "agent_id": agent.agent_id,
          "skill_code": skill_key,
          "specialist_result": finding,
          "finding": finding,
          "observations": self._new_observations(),
          "evidence_refs": list(finding.get("evidence_refs") or []),
          "knowledge_evidence_refs": list(finding.get("knowledge_evidence_refs") or []),
          "handoff_requests": handoff_requests,
          "react_iterations": iteration,
          "status": "COMPLETED",
          "step_traces": list(self.step_traces),
        }

      if decision["status"] == "FAILED":
        return self._failed(iteration, decision.get("reasoning_summary") or "Skill reasoning failed.")

      if decision["status"] == "RETRY":
        self._record_simple_step("RETRY", iteration, "SUCCESS", decision.get("reasoning_summary", ""))
        continue

      if decision["status"] == "NEED_TOOL":
        try:
          observation = self._execute_requested_tool(decision, iteration)
        except Exception as exc:  # noqa: BLE001 - local skill boundary
          return self._failed(iteration, str(exc))
        self.observations.append(observation)
        if not observation.get("success"):
          return self._failed(iteration, observation.get("error") or "Tool observation failed.")
        continue

    summary = "Exceeded max_react_iterations"
    if last_decision:
      summary = f"{summary}: {last_decision.get('reasoning_summary', '')}"
    finding = make_abstain_result(self.skill, summary, self._collect_refs())
    self._record_simple_step("ABSTAIN", limit, "SUCCESS", summary)
    return {
      "agent_id": agent.agent_id,
      "skill_code": skill_key,
      "specialist_result": finding,
      "finding": finding,
      "observations": self._new_observations(),
      "evidence_refs": list(finding.get("evidence_refs") or []),
      "knowledge_evidence_refs": [],
      "handoff_requests": [],
      "react_iterations": limit,
      "status": "COMPLETED",
      "step_traces": list(self.step_traces),
    }

  def _record_reason(self, iteration: int) -> ReasoningDecision:
    decision = self._reason()
    agent = self._agent()
    self.step_traces.append(
      {
        "node": "skill_react",
        "agent_id": agent.agent_id,
        "skill": self.skill["skill_key"],
        "step_type": "REASON",
        "start": utc_now(),
        "end": utc_now(),
        "status": decision["status"],
        "iteration": iteration,
        "tool_calls": [],
        "requested_evidence": decision.get("requested_evidence_type", ""),
        "input_summary": self._observation_summary(),
        "output_summary": decision.get("reasoning_summary", ""),
      }
    )
    return decision

  def _reason(self) -> ReasoningDecision:
    skill_key = self.skill["skill_key"]
    target = self.evidence_pack.get("targetEvidence") or {}

    if skill_key == "hook_analysis":
      if not self._has_text_evidence():
        if self._has_attempted_evidence(FRAME_TEXT):
          return self._abstain_decision("Opening text evidence remains unavailable after OCR/ASR tool attempt.")
        return self._need_tool(FRAME_TEXT, "Need opening visual text or transcript to judge the first-three-second hook.")
      if not target.get("keyframes"):
        if self._has_attempted_evidence(KEY_FRAME):
          return self._abstain_decision("Opening key frame evidence remains unavailable after frame tool attempt.")
        return self._need_tool(KEY_FRAME, "Need opening key frame evidence to anchor hook finding.")

    if skill_key == "structure_rhythm_analysis":
      if not target.get("keyframes"):
        if self._has_attempted_evidence(KEY_FRAME):
          return self._abstain_decision("Key frame evidence remains unavailable after frame tool attempt.")
        return self._need_tool(KEY_FRAME, "Need key frames to reason about structure and rhythm.")
      if not target.get("sceneJson"):
        if self._has_attempted_evidence(VIDEO_METADATA):
          return self._abstain_decision("Scene metadata remains unavailable after metadata tool attempt.")
        return self._need_tool(VIDEO_METADATA, "Need scene or metadata evidence to reason about rhythm.")

    if skill_key == "value_delivery_analysis":
      if not self._has_text_evidence():
        if self._has_attempted_evidence(FRAME_TEXT):
          return self._abstain_decision("Value text evidence remains unavailable after OCR/ASR tool attempt.")
        return self._need_tool(FRAME_TEXT, "Need visible copy or transcript to judge value delivery.")
      if not target.get("sceneJson"):
        if self._has_attempted_evidence(VIDEO_METADATA):
          return self._abstain_decision("Value timing metadata remains unavailable after metadata tool attempt.")
        return self._need_tool(VIDEO_METADATA, "Need metadata or scene evidence to ground value delivery timing.")

    # RAG：每次诊断前必须先检索本维度的评分点（RAG_MODE=always，默认）
    if self._rubric_required() and not self._has_attempted_evidence(RUBRIC):
      return self._need_tool(RUBRIC, "Retrieve this dimension's scoring rubric from the knowledge base before diagnosing.")

    if (
      not self._rubric_required()
      and self._needs_domain_knowledge()
      and not self._has_knowledge_evidence()
      and not self._has_attempted_knowledge()
    ):
      return self._need_tool(
        DOMAIN_KNOWLEDGE,
        "Need domain knowledge, analysis rules, or comparable cases to calibrate the diagnosis standard.",
      )

    job_context = dict(self.job_context)
    rubric = rubric_items(self._knowledge_observations())
    if rubric:
      job_context["rubric"] = rubric
    # 用户标准：只把分给本维度的条目交给本专家（优先级高于内置评分点）
    job_context["user_criteria"] = criteria_for_dimension(
      list(self.job_context.get("user_criteria") or []), str(self.skill.get("dimension") or "")
    )
    if self.evaluator_feedback:
      # Evaluator 判定 RETRY 时给出的具体原因：重试不再是“同样的输入再抽一次签”
      job_context["evaluator_feedback"] = list(self.evaluator_feedback)
      self._record_simple_step(
        "RETRY_WITH_FEEDBACK",
        len(self.step_traces) + 1,
        "SUCCESS",
        "; ".join(self.evaluator_feedback)[:240],
      )
    if self.handoff_answer:
      # 回调：提问方拿着被询问方的答复，完成自己原本没能下的结论
      job_context["execution_mode"] = "HANDOFF_INTEGRATION"
      job_context["handoff_answer"] = dict(self.handoff_answer)
      self._record_simple_step(
        "HANDOFF_INTEGRATION",
        len(self.step_traces) + 1,
        "SUCCESS",
        str(self.handoff_answer.get("question") or ""),
      )
    elif self.handoff:
      job_context["execution_mode"] = "TARGETED_REINVESTIGATION"
      job_context["handoff_context"] = dict(self.handoff)
      self._record_simple_step(
        "TARGETED_REINVESTIGATION",
        len(self.step_traces) + 1,
        "SUCCESS",
        str(self.handoff.get("question") or ""),
      )

    finding = run_diagnosis_skill(
      self.skill,
      job_context,
      self.evidence_pack,
      knowledge_observations=self._knowledge_observations(),
    )
    return {
      "status": "FINAL",
      "reasoning_summary": "Evidence is sufficient for a final finding.",
      "finding": finding,
    }

  def _need_tool(self, evidence_type: str, summary: str) -> ReasoningDecision:
    return {
      "status": "NEED_TOOL",
      "reasoning_summary": summary,
      "requested_evidence_type": evidence_type,
      "tool_input": {"job_id": self.job_id, "reason": summary},
    }

  def _abstain_decision(self, summary: str) -> ReasoningDecision:
    return {
      "status": "FINAL",
      "reasoning_summary": summary,
      "finding": make_abstain_result(self.skill, summary, self._collect_refs()),
    }

  def _execute_requested_tool(self, decision: ReasoningDecision, iteration: int) -> ToolObservation:
    requested_type = decision.get("requested_evidence_type") or JOB_EVIDENCE
    skill_key = self.skill["skill_key"]
    action_started = utc_now()
    try:
      resolution = resolve_tool_request(skill_key, requested_type, decision.get("tool_input"))
    except ToolResolutionError as exc:
      self._append_tool_step(iteration, requested_type, "", action_started, "FAILED", str(exc))
      return {
        "observation_type": requested_type,
        "tool_name": "",
        "payload": {},
        "evidence_refs": [],
        "success": False,
        "error": str(exc),
      }

    tool_name = resolution["tool_name"]
    if tool_name not in self._agent().allowed_tools:
      self._append_tool_step(iteration, requested_type, tool_name, action_started, "FAILED", "agent tool policy denied")
      return {
        "observation_type": requested_type,
        "tool_name": tool_name,
        "payload": {},
        "evidence_refs": [],
        "success": False,
        "error": f"Agent {self._agent().agent_id} is not allowed to call {tool_name}",
      }
    self._append_tool_step(iteration, requested_type, tool_name, action_started, "RUNNING", "resolved")
    observation_started = utc_now()
    try:
      payload = self._call_resolved_tool(tool_name, requested_type, decision)
      if isinstance(payload, dict) and requested_type not in KNOWLEDGE_EVIDENCE_TYPES:
        self.evidence_pack = payload
      evidence_refs = self._collect_observation_refs(requested_type, payload)
      knowledge_refs = [ref for ref in evidence_refs if ref.startswith("KNOWLEDGE:")]
      retrieval_trace = self._extract_retrieval_trace(payload)
      observation: ToolObservation = {
        "observation_type": requested_type,
        "tool_name": tool_name,
        "payload": payload if isinstance(payload, dict) else {"value": payload},
        "evidence_refs": evidence_refs,
        "knowledge_evidence_refs": knowledge_refs,
        "retrieval_trace": retrieval_trace,
        "success": True,
      }
      self._append_observation_step(
        iteration,
        requested_type,
        tool_name,
        observation_started,
        "SUCCESS",
        evidence_refs,
        retrieval_trace=retrieval_trace,
      )
      return observation
    except Exception as exc:  # noqa: BLE001 - tool boundary
      self._append_observation_step(iteration, requested_type, tool_name, observation_started, "FAILED", [], str(exc))
      if requested_type in KNOWLEDGE_EVIDENCE_TYPES:
        return {
          "observation_type": requested_type,
          "tool_name": tool_name,
          "payload": {"degraded": True, "strategy": "VIDEO_EVIDENCE_ONLY"},
          "evidence_refs": [],
          "knowledge_evidence_refs": [],
          "success": True,
          "error": f"RAG unavailable, degraded to video evidence only: {exc}",
        }
      return {
        "observation_type": requested_type,
        "tool_name": tool_name,
        "payload": {},
        "evidence_refs": [],
        "success": False,
        "error": str(exc),
      }

  def _append_tool_step(
    self,
    iteration: int,
    requested_type: str,
    tool_name: str,
    start: str,
    status: str,
    output: str,
  ) -> None:
    self.step_traces.append(
      {
        "node": "skill_react",
        "agent_id": self._agent().agent_id,
        "skill": self.skill["skill_key"],
        "step_type": "ACTION",
        "start": start,
        "end": utc_now(),
        "status": status,
        "iteration": iteration,
        "tool_calls": [{"tool_name": tool_name, "evidence_type": requested_type}] if tool_name else [],
        "requested_evidence": requested_type,
        "tool_name": tool_name,
        "output_summary": output,
      }
    )

  def _append_observation_step(
    self,
    iteration: int,
    requested_type: str,
    tool_name: str,
    start: str,
    status: str,
    evidence_refs: list[str],
    error: str = "",
    retrieval_trace: dict[str, Any] | None = None,
  ) -> None:
    trace = retrieval_trace or {}
    self.step_traces.append(
      {
        "node": "skill_react",
        "agent_id": self._agent().agent_id,
        "skill": self.skill["skill_key"],
        "step_type": "OBSERVATION",
        "start": start,
        "end": utc_now(),
        "status": status,
        "iteration": iteration,
        "tool_calls": [{"tool_name": tool_name, "evidence_type": requested_type}],
        "requested_evidence": requested_type,
        "tool_name": tool_name,
        "error": error,
        "output_summary": ",".join(evidence_refs[:5]),
        "skill_code": trace.get("skill_code", ""),
        "query": trace.get("query", ""),
        "knowledge_type": trace.get("knowledge_type", ""),
        "retrieval_method": trace.get("retrieval_method", ""),
        "bm25_count": int(trace.get("bm25_count") or 0),
        "vector_count": int(trace.get("vector_count") or 0),
        "rrf_count": int(trace.get("rrf_count") or 0),
        "rerank_count": int(trace.get("rerank_count") or 0),
        "top_k": int(trace.get("top_k") or 0),
        "latency": int(trace.get("latency_ms") or 0),
        "selected_evidence_refs": list(trace.get("selected_evidence_refs") or []),
      }
    )

  def _record_simple_step(self, step_type: str, iteration: int, status: str, summary: str) -> None:
    self.step_traces.append(
      {
        "node": "skill_react",
        "agent_id": self._agent().agent_id,
        "skill": self.skill["skill_key"],
        "step_type": step_type,
        "start": utc_now(),
        "end": utc_now(),
        "status": status,
        "iteration": iteration,
        "tool_calls": [],
        "output_summary": summary,
      }
    )

  def _failed(self, iteration: int, error: str) -> SkillExecutionResult:
    self._record_simple_step("FAILED", iteration, "FAILED", error)
    return {
      "agent_id": self._agent().agent_id,
      "skill_code": self.skill["skill_key"],
      "observations": self._new_observations(),
      "evidence_refs": self._collect_refs(),
      "knowledge_evidence_refs": [ref for item in self._knowledge_observations() for ref in item.get("knowledge_evidence_refs", [])],
      "react_iterations": iteration,
      "status": "FAILED",
      "error": error,
      "step_traces": list(self.step_traces),
    }

  def _agent(self) -> SpecialistAgentDefinition:
    return self.agent or specialist_for_skill(self.skill["skill_key"])

  def _new_observations(self) -> list[ToolObservation]:
    return list(self.observations[self.seeded_observation_count:])

  def _has_text_evidence(self) -> bool:
    target = self.evidence_pack.get("targetEvidence") or {}
    # 旧实现把 '{"ocr":[]}' 这种空 OCR 结果也当成"有文字"
    if has_text_evidence(target):
      return True
    return any(item.get("success") and item.get("observation_type") == FRAME_TEXT for item in self.observations)

  def _rubric_required(self) -> bool:
    return get_settings().rag_mode == "always"

  def _needs_domain_knowledge(self) -> bool:
    return bool(
      self.job_context.get("needKnowledge")
      or self.job_context.get("category")
      or self.job_context.get("useKnowledge")
    )

  def _has_knowledge_evidence(self) -> bool:
    return any(
      item.get("success") and item.get("knowledge_evidence_refs")
      for item in self._knowledge_observations()
    )

  def _has_attempted_knowledge(self) -> bool:
    return bool(self._knowledge_observations())

  def _has_attempted_evidence(self, evidence_type: str) -> bool:
    return any(item.get("observation_type") == evidence_type for item in self.observations)

  def _knowledge_observations(self) -> list[ToolObservation]:
    return [
      item
      for item in self.observations
      if item.get("observation_type") in KNOWLEDGE_EVIDENCE_TYPES
    ]

  def _call_resolved_tool(
    self,
    tool_name: str,
    requested_type: str,
    decision: ReasoningDecision,
  ) -> Any:
    if requested_type not in KNOWLEDGE_EVIDENCE_TYPES:
      return self.harness.call_tool(self.harness_ctx, tool_name, job_id=self.job_id)

    if requested_type == RUBRIC:
      settings = get_settings()
      return self.harness.call_tool(
        self.harness_ctx,
        tool_name,
        query_text=rubric_query(self.skill["skill_key"], self.evidence_pack),
        skill_code=self.skill["skill_key"],
        knowledge_type=RUBRIC,
        category=job_category(self.job_context),
        top_k=settings.rubric_top_k,
        filters={"job_id": self.job_id, "dimension": self.skill.get("dimension", "")},
      )
    category = str(self.job_context.get("category") or "")
    query_text = self._knowledge_query_text(requested_type)
    return self.harness.call_tool(
      self.harness_ctx,
      tool_name,
      query_text=query_text,
      skill_code=self.skill["skill_key"],
      knowledge_type=requested_type,
      category=category,
      top_k=int((decision.get("tool_input") or {}).get("top_k") or get_settings().retrieval_top_k),
      filters={"job_id": self.job_id, "dimension": self.skill.get("dimension", "")},
    )

  def _knowledge_query_text(self, requested_type: str) -> str:
    target = self.evidence_pack.get("targetEvidence") or {}
    text_bits = [
      self.skill.get("goal", ""),
      str(self.job_context.get("category") or ""),
      str(target.get("transcriptText") or ""),
      str(target.get("ocrJson") or ""),
      requested_type,
    ]
    return " ".join(item for item in text_bits if item).strip()

  def _collect_observation_refs(self, requested_type: str, payload: Any) -> list[str]:
    if requested_type in KNOWLEDGE_EVIDENCE_TYPES:
      if not isinstance(payload, dict):
        return []
      return [
        str(item.get("evidenceRef"))
        for item in payload.get("items") or []
        if item.get("evidenceRef")
      ]
    return self._collect_refs()

  def _extract_retrieval_trace(self, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
      return {}
    trace = payload.get("trace")
    return dict(trace) if isinstance(trace, dict) else {}

  def _collect_refs(self) -> list[str]:
    target = self.evidence_pack.get("targetEvidence") or {}
    refs: list[str] = []
    timeline = parse_timeline(target)
    if timeline:
      # v0.2：最多 60 帧，全部列出会让观察记录膨胀；只记前 12 个时间点引用
      for frame in (timeline.get("keyframes") or [])[:12]:
        if isinstance(frame, dict) and frame.get("time"):
          refs.append(f"FRAME:{TARGET_ALIAS}@{frame['time']}")
    else:
      for frame in target.get("keyframes") or []:
        refs.append(str(frame))
    if target.get("transcriptText"):
      refs.append(f"ASR:{target.get('videoAssetId', 'target')}")
    if target.get("ocrJson"):
      refs.append(f"OCR:{target.get('videoAssetId', 'target')}")
    if target.get("sceneJson"):
      refs.append(f"METADATA:{target.get('videoAssetId', 'target')}")
    return list(dict.fromkeys(refs))

  def _observation_summary(self) -> str:
    if not self.observations:
      return "base_evidence"
    last = self.observations[-1]
    refs = last.get("evidence_refs") or []
    return f"{last.get('observation_type')} success={last.get('success')} refs={len(refs)}"
