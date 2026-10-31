from __future__ import annotations

import re
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent_service.config import get_settings
from agent_service.graph.evidence_timeline import (
  ocr_items,
  opening_quotes,
  opening_text,
  parse_timeline,
  scene_stats,
  text_similarity,
  transcript_segments,
  video_by_alias,
)
from agent_service.graph.finding_types import (
  GAP,
  OPENING_SECONDS,
  STRENGTH,
  is_known_type,
  types_for_dimension,
)
from agent_service.graph.result_contract import make_abstain_result
from agent_service.graph.runtime import report_stage, trace_step
from agent_service.graph.state import AgentGraphState

CONFIDENCE_THRESHOLD = 0.6

# 跨维度建议的对立词：两个不同维度的 suggested_action 分别包含一对里的两个词，视为潜在冲突
_OPPOSING_DIRECTIVES: tuple[tuple[str, str], ...] = (
  ("提前", "延后"),
  ("提前", "推迟"),
  ("前置", "后置"),
  ("加快", "放慢"),
  ("加速", "减速"),
  ("缩短", "延长"),
  ("删减", "增加"),
  ("减少", "增加"),
  ("精简", "扩充"),
  ("合并", "拆分"),
)


def evaluator_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
  """
  最终质量 Gate：PASS / RETRY_AGENT / REPLAN / FAILED。

  - 每个需要重试的 Skill 都会拿到具体原因（retry_feedback），重试时注入 prompt；
  - 检查模型引用的证据是否真实存在于证据包（invalid_evidence_refs）；
  - 没能完成回调的 NEEDS_CAPABILITY 在合成前转成 ABSTAIN，绝不作为结论落库；
  - 单个 Specialist 系统故障且无法重试时，其它维度照常完成（COMPLETED_WITH_GAPS）。
  """
  report_stage(state, config, "EVALUATING", 88, "Evaluating findings and evidence grounding.")

  with trace_step(state, "evaluator", input_summary=f"findings={len(state.get('findings') or [])}") as step:
    findings = list(state.get("findings") or [])
    plan = list(state.get("plan") or [])
    gaps = list(state.get("evidence_gaps") or [])
    handoffs = list(state.get("handoff_requests") or [])
    reasons: list[str] = []
    feedback: dict[str, list[str]] = {}

    def flag(skill_key: str, reason: str, hint: str | None = None) -> None:
      reasons.append(reason)
      if skill_key:
        feedback.setdefault(skill_key, []).append(hint or reason)

    skill_status = dict(state.get("skill_execution_status") or {})
    missing_results = {item["skill_key"] for item in plan if not skill_status.get(item["skill_key"])}
    failed_skills = {skill_key for skill_key, status in skill_status.items() if status == "FAILED"}
    if missing_results:
      reasons.append("MISSING_SPECIALIST_RESULT: " + ",".join(sorted(missing_results)))
      for skill_key in sorted(missing_results):
        feedback.setdefault(skill_key, []).append("上一轮没有产出结果，请重新完成本维度诊断。")
    if failed_skills:
      reasons.append("SPECIALIST_SYSTEM_FAILURE: " + ",".join(sorted(failed_skills)))
      for skill_key in sorted(failed_skills):
        feedback.setdefault(skill_key, []).append("上一轮执行失败，请重新完成本维度诊断。")

    if len(findings) < len(plan) and not missing_results:
      missing = {item["skill_key"] for item in plan} - {str(item.get("skill_key")) for item in findings}
      if missing:
        reasons.append("MISSING_SPECIALIST_RESULT: " + ",".join(sorted(missing)))
        for skill_key in sorted(missing):
          feedback.setdefault(skill_key, []).append("上一轮没有产出结果，请重新完成本维度诊断。")

    for finding in findings:
      skill_key = str(finding.get("skill_key") or "")
      outcome = str(finding.get("outcome") or "FINDING")
      if outcome == "ABSTAIN":
        if not finding.get("evidence_refs"):
          reasons.append(f"{skill_key} abstained with no evidence refs.")
        continue
      if outcome == "NEEDS_CAPABILITY":
        continue  # 由交接流程处理；无法回调的会在合成前转成 ABSTAIN
      confidence = float(finding.get("confidence") or 0)
      if not finding.get("observation") or not finding.get("suggested_action"):
        flag(skill_key, f"{skill_key} output structure is incomplete.", "observation 或 suggested_action 为空，请补全。")
      # "两者相当"本身就是低确定性的判断，不因置信度低而反复重试
      is_parity = get_settings().quality_rules != "v1" and str(finding.get("polarity") or "") == "PARITY"
      if confidence < CONFIDENCE_THRESHOLD and not is_parity:
        if get_settings().quality_rules == "v1":
          hint = f"置信度 {confidence:.2f} 低于 {CONFIDENCE_THRESHOLD}：请补充具体证据支撑，证据确实不足时改为 ABSTAIN。"
        else:
          # v2：第一次真实评测里，这句"改为 ABSTAIN"让大量本可成立的结论被放弃，改为要求补证据 / 如实打分
          hint = (
            f"置信度 {confidence:.2f} 低于 {CONFIDENCE_THRESHOLD}：请补充更直接的原文或镜头数字支撑结论，"
            "并给出与证据相符的真实置信度；差异不明显就改为 PARITY。证据存在时不要 ABSTAIN。"
          )
        flag(skill_key, f"{skill_key} confidence below threshold.", hint)
      if not finding.get("evidence_refs"):
        flag(skill_key, f"{skill_key} lacks evidence refs.", "结论没有引用任何证据，请引用证据包中的帧/OCR/ASR。")
      invalid_refs = list(finding.get("invalid_evidence_refs") or [])
      if invalid_refs:
        flag(
          skill_key,
          f"{skill_key} cites evidence refs not present in the evidence pack: {','.join(invalid_refs[:5])}",
          f"以下引用在证据包中不存在，请只引用证据包里真实存在的条目：{', '.join(invalid_refs[:5])}",
        )
      if finding.get("knowledge_evidence_refs") and not _has_video_evidence(finding):
        flag(
          skill_key,
          f"{skill_key} only has knowledge evidence; video facts must be grounded by video evidence.",
          "只引用了知识库条目：关于视频本身的事实必须引用视频证据。",
        )
      if not _has_video_evidence(finding):
        flag(skill_key, f"{skill_key} lacks video evidence refs.", "缺少视频证据引用。")

    if get_settings().quality_rules != "v1":
      for skill_key, reason, hint in _quality_v2_issues(findings, state.get("evidence_pack") or {}):
        flag(skill_key, reason, hint)

    for skill_a, skill_b, detail in _detect_conflicts(findings):
      reasons.append(f"Skill conclusions appear conflicting: {skill_a} vs {skill_b} ({detail}).")
      feedback.setdefault(skill_a, []).append(f"你的建议与 {skill_b} 的建议可能冲突（{detail}），请确认或说明适用条件。")
      feedback.setdefault(skill_b, []).append(f"你的建议与 {skill_a} 的建议可能冲突（{detail}），请确认或说明适用条件。")

    system_failure = bool(missing_results or failed_skills)
    completed_skills = {skill_key for skill_key, status in skill_status.items() if status == "COMPLETED"}
    dropped = list(state.get("dropped_handoffs") or [])

    if handoffs and _can_replan(state):
      decision = "REPLAN"
      reasons.append("Structured capability handoff requested.")
    elif handoffs:
      # 交接预算用完：剩余请求记为 dropped，提问方结论在 _finalize_findings 里转成 ABSTAIN
      decision = "PASS"
      reasons.append("Global replan limit exceeded; completing with gaps.")
      dropped.extend({**item, "drop_reason": "global_replan_limit_exceeded"} for item in handoffs)
      handoffs = []
    else:
      if system_failure:
        if _can_retry(state):
          decision = "RETRY_AGENT"
        elif completed_skills:
          decision = "PASS"
          reasons.append("Partial completion: failed specialists are recorded as evidence gaps.")
        else:
          decision = "FAILED"
      elif gaps and _has_rejected_handoff(findings):
        decision = "PASS"
        reasons.append("Handoff rejected; completing with gaps.")
      elif gaps and _has_abstain(findings):
        decision = "PASS"
        reasons.append("Specialist abstained with unresolved evidence gaps; completing with gaps.")
      elif gaps:
        decision = "RETRY_AGENT" if _can_retry(state) else "PASS"
        reasons.append("Unresolved evidence gaps remain after local ReAct.")
        for gap in gaps:
          skill_key = str(gap.get("skillKey") or gap.get("skill_key") or "")
          if skill_key:
            feedback.setdefault(skill_key, []).append(f"仍有证据缺口：{gap.get('reason') or gap.get('evidenceType')}")
      elif reasons and _can_retry(state):
        decision = "RETRY_AGENT"
      else:
        decision = "PASS"

    affected_skills = [key for key in dict.fromkeys(feedback) if key]
    result = {
      "decision": decision,
      "reasons": reasons,
      "affected_skills": affected_skills,
      "evidence_gaps": gaps,
    }
    evaluation_results = list(state.get("evaluation_results") or [])
    evaluation_results.append(result)
    step["output_summary"] = f"decision={decision} affected={','.join(affected_skills)}"

    if decision == "PASS":
      if get_settings().quality_rules != "v1":
        findings, downgrade_notes = enforce_hard_rules(findings, state.get("evidence_pack") or {})
        reasons.extend(downgrade_notes)
      finalized, converted = _finalize_findings(findings, plan, completed_skills, system_failure)
      final_gaps = [gap for finding in finalized for gap in finding.get("evidence_gaps", [])]
      unanswered = [item for item in state.get("handoff_answers") or [] if item.get("status") != "ANSWERED"]
      if unanswered:
        reasons.append(f"{len(unanswered)} handoff question(s) were not answered by the target specialist.")
      with_gaps = (
        bool(reasons) or bool(dropped) or converted or _has_abstain(finalized) or _has_rejected_handoff(finalized)
      )
      completion_status = "COMPLETED_WITH_GAPS" if with_gaps else "COMPLETED"
      completion_trace = {
        "node": "evaluator",
        "step_type": completion_status,
        "start": "",
        "end": "",
        "status": "SUCCESS",
        "iteration": state.get("iteration_count", 0),
        "tool_calls": [],
        "output_summary": "; ".join(reasons),
      }
      return {
        "evaluation_results": evaluation_results,
        "findings": finalized,
        "draft_hypotheses": finalized,
        "evidence_gaps": final_gaps,
        "handoff_requests": [],
        "dropped_handoffs": dropped,
        "status": "SYNTHESIZING",
        "diagnosis_completion_status": completion_status,
        "next_action": "synthesize",
        "done": False,
        "step_traces": [*list(state["step_traces"]), completion_trace],
      }
    if decision == "RETRY_AGENT":
      return {
        "evaluation_results": evaluation_results,
        "skills_to_run": affected_skills or [item["skill_key"] for item in plan],
        "retry_feedback": feedback,
        "handoff_requests": handoffs,
        "dropped_handoffs": dropped,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "status": "REFINING",
        "next_action": "diagnose",
        "done": False,
        "step_traces": state["step_traces"],
      }
    if decision == "REPLAN":
      replan_trace = {
        "node": "evaluator",
        "step_type": "REPLAN",
        "start": "",
        "end": "",
        "status": "SUCCESS",
        "iteration": state.get("global_replan_count", 0),
        "tool_calls": [],
        "output_summary": "handoff_requests=" + str(len(handoffs)),
      }
      return {
        "evaluation_results": evaluation_results,
        "status": "REPLANNING",
        "next_action": "supervise",
        "done": False,
        "step_traces": [*list(state["step_traces"]), replan_trace],
      }

    return {
      "evaluation_results": evaluation_results,
      "status": "FAILED",
      "error": "; ".join(reasons or ["Evaluator failed"]),
      "next_action": "fail",
      "done": True,
      "step_traces": state["step_traces"],
    }


def _finalize_findings(
  findings: list[dict[str, Any]],
  plan: list[dict[str, Any]],
  completed_skills: set[str],
  system_failure: bool,
) -> tuple[list[dict[str, Any]], bool]:
  """
  合成前的收尾：
  - 仍是 NEEDS_CAPABILITY 的结果（交接没能完成回调）转成 ABSTAIN，记录缺口；
  - 部分完成时，没有结果的维度补一条 ABSTAIN，说明是系统故障导致缺失。
  返回 (结果, 是否发生了转换)。
  """
  plan_by_skill = {item["skill_key"]: item for item in plan}
  converted = False
  finalized: list[dict[str, Any]] = []
  for finding in findings:
    skill_key = str(finding.get("skill_key") or "")
    if finding.get("outcome") == "NEEDS_CAPABILITY" and skill_key in plan_by_skill:
      abstain = make_abstain_result(
        plan_by_skill[skill_key],
        f"Handoff was not resolved before completion: {finding.get('question') or finding.get('reason') or ''}".strip(),
        list(finding.get("evidence_refs") or []),
      )
      abstain["handoff_rejected"] = {
        "reason": "handoff_not_resolved",
        "target_capability": finding.get("target_capability", ""),
      }
      finalized.append(abstain)
      converted = True
      continue
    finalized.append(finding)

  if system_failure and completed_skills:
    present = {str(item.get("skill_key")) for item in finalized}
    for skill_key, item in plan_by_skill.items():
      if skill_key not in present or skill_key not in completed_skills:
        finalized = [row for row in finalized if str(row.get("skill_key")) != skill_key]
        placeholder = make_abstain_result(item, "SPECIALIST_SYSTEM_FAILURE: specialist did not complete after retries.")
        placeholder["system_failure"] = True
        finalized.append(placeholder)
        converted = True
  return finalized, converted


def _can_retry(state: AgentGraphState) -> bool:
  return state.get("iteration_count", 0) < get_settings().evaluator_retry_limit


def _can_replan(state: AgentGraphState) -> bool:
  return state.get("global_replan_count", 0) < state.get("max_global_replans", get_settings().max_global_replans)


def _detect_conflicts(findings: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
  """跨维度建议冲突（启发式）：对立动词出现在不同维度的建议里。"""
  conflicts: list[tuple[str, str, str]] = []
  rows = [
    (str(item.get("skill_key") or ""), str(item.get("suggested_action") or ""), str(item.get("observation") or ""))
    for item in findings
    if item.get("outcome", "FINDING") == "FINDING"
  ]
  for index, (skill_a, action_a, observation_a) in enumerate(rows):
    for skill_b, action_b, observation_b in rows[index + 1 :]:
      for left, right in _OPPOSING_DIRECTIVES:
        if (left in action_a and right in action_b) or (right in action_a and left in action_b):
          conflicts.append((skill_a, skill_b, f"{left}/{right}"))
          break
      else:
        texts = (observation_a.lower(), observation_b.lower())
        if ("no issue" in texts[0] and "critical" in texts[1]) or ("critical" in texts[0] and "no issue" in texts[1]):
          conflicts.append((skill_a, skill_b, "no issue/critical"))
  return conflicts


def _has_video_evidence(finding: dict[str, Any]) -> bool:
  refs = list(finding.get("video_evidence_refs") or [])
  if not refs:
    refs = [str(item) for item in finding.get("evidence_refs") or [] if not str(item).startswith("KNOWLEDGE:")]
  return bool(refs)


def _has_abstain(findings: list[dict[str, Any]]) -> bool:
  return any(str(item.get("outcome") or "") == "ABSTAIN" for item in findings)


def _has_rejected_handoff(findings: list[dict[str, Any]]) -> bool:
  return any(bool(item.get("handoff_rejected")) for item in findings)


def _criteria_issues(finding: dict[str, Any]) -> list[tuple[str, str, str]]:
  """用户评分标准：分给本维度的每一条都必须在 criteria_verdicts 里有回应（满足 / 不满足 / 无法判断）。"""
  missing = list(finding.get("missing_criteria_ids") or [])
  if not missing:
    return []
  skill_key = str(finding.get("skill_key") or "")
  return [(
    skill_key,
    f"{skill_key} did not answer user criteria {missing}.",
    (
      f"用户评分标准 {'、'.join(missing)} 没有回应：请在 criteria_verdicts 里逐条给出 verdict（MET / NOT_MET / UNKNOWN）"
      "和 reason（写清时间点和原文）；证据不足就填 UNKNOWN 并说明缺什么，不要省略。"
    ),
  )]


def _rubric_issues(finding: dict[str, Any]) -> list[tuple[str, str, str]]:
  """
  RAG 评分点（RAG_MODE=always）：检索到了评分点时，每条结论必须注明依据了哪几条（rubric_refs），
  且只能引用本次真正检索到的评分点。检索失败（知识库不可用）时不强制。
  """
  if get_settings().rag_mode != "always":
    return []
  retrieved = list(finding.get("retrieved_rubric_refs") or [])
  if not retrieved:
    return []
  skill_key = str(finding.get("skill_key") or "")
  issues: list[tuple[str, str, str]] = []
  invalid = list(finding.get("invalid_rubric_refs") or [])
  if invalid:
    issues.append((
      skill_key,
      f"{skill_key} cites rubric items that were not retrieved: {invalid[:3]}.",
      f"rubric_refs 里的 {'、'.join(invalid[:3])} 不是本次检索到的评分点，只能从输入 rubric 里原样复制 ref。",
    ))
  if not finding.get("rubric_refs"):
    issues.append((
      skill_key,
      f"{skill_key} does not state which rubric items the finding is based on.",
      (
        "结论没有注明依据的评分点：请对照输入里的 rubric，在 rubric_refs 里列出 1~3 条与本结论直接相关的评分点 ref，"
        "并在 observation / difference_text 里说明目标和参考分别是否满足它们。"
      ),
    ))
  return issues


def _quality_v2_issues(findings: list[dict[str, Any]], evidence_pack: dict[str, Any]) -> list[tuple[str, str, str]]:
  """
  quality rules v2 的检查，返回 (skill_key, 原因, 给专家的反馈)：

  1. 原文引用：FINDING 必须至少 1 条在证据里真实存在的逐字引用；结构节奏维度可以改用镜头数据（SCENE 引用）。
     只引用帧时间点不算证据（模型看不到画面）。
  2. 分类：finding_type 必须来自分类表。
  3. 分析窗口：视频被截断时，不能对窗口之外的结尾下"没有行动号召"的结论。
  4. 跨维度矛盾：开场钩子说"开场没有价值承诺"，而价值传递引用了开场几秒内的收益原文（或反之）。
  """
  issues: list[tuple[str, str, str]] = []
  conclusive = [
    item for item in findings if str(item.get("outcome") or "FINDING") == "FINDING" and not item.get("system_failure")
  ]
  target_timeline = parse_timeline(evidence_pack.get("targetEvidence") or {}) or {}

  for finding in conclusive:
    skill_key = str(finding.get("skill_key") or "")
    dimension = str(finding.get("dimension") or "")
    polarity = str(finding.get("polarity") or GAP)
    finding_type = str(finding.get("finding_type") or "")
    grounded = list(finding.get("grounded_quotes") or [])
    cited = [str(item) for item in finding.get("cited_refs") or []]
    has_scene = any(ref.startswith(("SCENE:", "METADATA:")) for ref in cited)

    if not grounded and not (dimension == "STRUCTURE_RHYTHM" and has_scene):
      problems = "；".join(list(finding.get("quote_issues") or [])[:3])
      issues.append((
        skill_key,
        f"{skill_key} has no verbatim quote grounded in the evidence.",
        "结论没有可以在证据中找到的逐字引用"
        + (f"（{problems}）" if problems else "")
        + "：quotes 里请逐字摘抄 speech / screenText 某一段的原文，ref 直接复制该段的 ref 字段；只引用 FRAME 不算证据。"
        + ("结构节奏也可以在 evidence_refs 里引用 METADATA:T（sceneStats）或 SCENE:T#n 并写出镜头数字。" if dimension == "STRUCTURE_RHYTHM" else "")
        + "补上引用即可，不要因此改为 ABSTAIN。",
      ))

    if not is_known_type(dimension, finding_type, polarity):
      allowed = "、".join(types_for_dimension(dimension)) if polarity == GAP else "strength、parity"
      issues.append((
        skill_key,
        f"{skill_key} finding_type '{finding_type}' is not in the taxonomy.",
        f"finding_type「{finding_type}」不在分类表中，polarity={polarity} 时请从以下类型选择：{allowed}（确实不适用才用 other）。",
      ))

    if polarity == GAP and finding_type == "no_cta" and target_timeline.get("truncated"):
      issues.append((
        skill_key,
        f"{skill_key} claims a missing ending CTA outside the analysis window.",
        (
          f"目标视频时长 {target_timeline.get('durationSeconds')} 秒，只分析了前 {target_timeline.get('analyzedSeconds')} 秒，"
          "结尾不在分析窗口内，不能断言没有行动号召；请改为其它有证据的问题或 PARITY / ABSTAIN。"
        ),
      ))

    issues.extend(_comparison_issues(finding, evidence_pack))
    issues.extend(_rubric_issues(finding))
    issues.extend(_criteria_issues(finding))

  by_dimension = {str(item.get("dimension")): item for item in conclusive}
  hook = by_dimension.get("HOOK")
  value = by_dimension.get("VALUE_DELIVERY")
  if hook and value:
    hook_gap = str(hook.get("polarity") or GAP) == GAP and hook.get("finding_type") == "hook_no_value_promise"
    value_opening = opening_quotes(list(value.get("grounded_quotes") or []), opening_seconds=OPENING_SECONDS)
    value_says_ok = str(value.get("polarity") or GAP) != GAP or value.get("finding_type") not in {"value_late", "value_unclear"}
    if hook_gap and value_opening and value_says_ok:
      quote = value_opening[0]
      issues.append((
        str(hook.get("skill_key") or ""),
        "Skill conclusions appear conflicting: hook says no value promise but value_delivery quotes an opening benefit.",
        (
          f"价值传递专家引用了开场 {quote['ref']} 的收益原文「{quote['text']}」，与你的'开场没有价值承诺'矛盾。"
          "请重新核对开场 0~5 秒的口播与屏幕文字；如果收益确实已经说出，请改判（例如改为 hook_weak_visual_text 或 PARITY）。"
        ),
      ))
    hook_opening = opening_quotes(list(hook.get("grounded_quotes") or []), opening_seconds=OPENING_SECONDS)
    value_gap_late = str(value.get("polarity") or GAP) == GAP and value.get("finding_type") in {"value_late", "value_unclear"}
    if value_gap_late and hook_opening and str(hook.get("polarity") or GAP) == STRENGTH:
      quote = hook_opening[0]
      issues.append((
        str(value.get("skill_key") or ""),
        "Skill conclusions appear conflicting: value_delivery says benefit is late/unclear but hook quotes an opening benefit.",
        f"开场钩子专家引用了开场 {quote['ref']} 的原文「{quote['text']}」并判断开场优于参考，与你的'收益太晚/模糊'矛盾，请核对。",
      ))
  return issues


_REFERENCE_QUOTE = re.compile(r"^(ASR|OCR):R\d+")
_REFERENCE_DATA = re.compile(r"^(METADATA|SCENE):R\d+")
SAME_OPENING_SIMILARITY = 0.9
SAME_PACING_TOLERANCE = 0.15
# 平均值接近不代表节奏接近（hard 组 c23：平均只差 12%，但前 14 秒 12 个碎镜头 + 40 秒一镜到底）。
# 中位镜头时长和最长镜头也接近，才认定"节奏相同"。
SAME_MEDIAN_TOLERANCE = 0.30
SAME_LONGEST_RATIO = 1.5
SAME_SHORT_SHOTS_DIFF = 4


def _comparison_issues(finding: dict[str, Any], evidence_pack: dict[str, Any]) -> list[tuple[str, str, str]]:
  """
  v2 的"比较"检查（第二轮真实评测：模型在孤立地给目标挑毛病，没有和参考比较）：

  1. 必须给出 target_score / reference_scores（方向由系统按分差计算）；
  2. GAP 必须引用参考视频同一环节的证据，证明参考在这一点上做得更好；
  3. 证据实质相同却判 GAP：开场文字几乎相同的 HOOK 差距、镜头统计几乎一致的节奏差距；
  4. 结构节奏的 GAP 建议必须带数字。
  """
  issues: list[tuple[str, str, str]] = []
  skill_key = str(finding.get("skill_key") or "")
  dimension = str(finding.get("dimension") or "")
  polarity = str(finding.get("polarity") or GAP)
  references = dict(finding.get("reference_scores") or {})

  if finding.get("target_score") is None or not references:
    issues.append((
      skill_key,
      f"{skill_key} did not score target and references.",
      (
        "请给出 target_score（目标 1~5 分）和 reference_scores（每个参考一个分数，如 {\"R1\": 3}）；"
        "差距方向由系统按分差计算：目标比最好的参考低至少 1 分才算 GAP。"
      ),
    ))
  if polarity != GAP:
    return issues

  quotes = [str(item.get("ref") or "") for item in finding.get("grounded_quotes") or []]
  cited = [str(item) for item in finding.get("cited_refs") or []]
  has_reference_evidence = any(_REFERENCE_QUOTE.match(ref) for ref in quotes) or (
    dimension == "STRUCTURE_RHYTHM" and any(_REFERENCE_DATA.match(ref) for ref in cited)
  )
  if not has_reference_evidence:
    issues.append((
      skill_key,
      f"{skill_key} reports a GAP without reference-side evidence.",
      "判定为差距时，必须在 quotes 里引用参考视频（R1/R2）同一环节的原文，证明参考在这一点上做得更好"
      + ("（结构节奏可以引用 METADATA:R1 / SCENE:R1#n）" if dimension == "STRUCTURE_RHYTHM" else "")
      + "；如果参考并不更好，请如实打分。",
    ))

  violation = hard_rule_violation(finding, evidence_pack)
  if violation:
    issues.append((skill_key, f"{skill_key} violates a hard rule: {violation['rule']}", violation["message"]))
  if dimension == "VALUE_DELIVERY" and str(finding.get("finding_type")) == "value_late" and not _benefit_times(finding)[0]:
    issues.append((
      skill_key,
      f"{skill_key} value_late without first_benefit_seconds.",
      "判为 value_late 时必须填写 first_benefit_seconds，如 {\"T\": 70, \"R1\": 0.5}（开场承诺也算收益首次出现）。",
    ))
  if dimension == "STRUCTURE_RHYTHM" and not re.search(r"\d", str(finding.get("suggested_action") or "")):
    issues.append((
      skill_key,
      f"{skill_key} structure suggestion has no concrete numbers.",
      "结构节奏的建议必须带具体数字，例如'目标平均镜头 1.8 秒、参考 6 秒，建议把 30~60 秒段的镜头延长到 4 秒以上'。",
    ))
  return issues


_STEP_MARKER = re.compile(r"第[一二三四五六七八九十\d]+[步个点招]|首先|其次|最后|step\s*\d", re.IGNORECASE)
VALUE_LATE_MIN_GAP_SECONDS = 3.0


def _best_reference(finding: dict[str, Any], evidence_pack: dict[str, Any]) -> tuple[str, dict[str, Any]]:
  references = dict(finding.get("reference_scores") or {})
  alias = max(references, key=references.get) if references else "R1"
  return alias, video_by_alias(evidence_pack, alias) or {}


def _benefit_times(finding: dict[str, Any]) -> tuple[float | None, float | None]:
  rows = dict(finding.get("first_benefit_seconds") or {})
  target = rows.pop("T", None)
  references = [value for key, value in rows.items() if key.startswith("R") and value is not None]
  return target, (min(references) if references else None)


def _all_text(video: dict[str, Any]) -> str:
  parts = [str(item.get("text") or "") for item in transcript_segments(video)]
  parts += [str(item.get("text") or "") for item in ocr_items(video)]
  return " ".join(parts)


def _shot_numbers(stats: dict[str, Any]) -> tuple[float, float, float]:
  longest = stats.get("longestShot") or {}
  return (
    float(stats.get("avgShotSeconds") or 0),
    float(stats.get("medianShotSeconds") or 0),
    float(longest.get("seconds") or 0) if isinstance(longest, dict) else 0.0,
  )


def same_pacing(target_stats: dict[str, Any], reference_stats: dict[str, Any]) -> str | None:
  """平均、中位、最长镜头三项都接近才算节奏相同；返回说明文字，不相同返回 None。"""
  t_avg, t_median, t_longest = _shot_numbers(target_stats)
  r_avg, r_median, r_longest = _shot_numbers(reference_stats)
  if not (t_avg and r_avg and t_median and r_median and t_longest and r_longest):
    return None
  if abs(t_avg - r_avg) / r_avg > SAME_PACING_TOLERANCE:
    return None
  if abs(t_median - r_median) / r_median > SAME_MEDIAN_TOLERANCE:
    return None
  if max(t_longest, r_longest) / min(t_longest, r_longest) > SAME_LONGEST_RATIO:
    return None
  # 2 秒内的碎镜头数差得多（真实任务里 7 个 vs 2 个），也不算相同
  t_short = int(target_stats.get("shotsUnder2s") or 0)
  r_short = int(reference_stats.get("shotsUnder2s") or 0)
  if abs(t_short - r_short) >= SAME_SHORT_SHOTS_DIFF:
    return None
  return (
    f"平均镜头 {t_avg} vs {r_avg} 秒、中位 {t_median} vs {r_median} 秒、最长 {t_longest} vs {r_longest} 秒"
  )


def hard_rule_violation(finding: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, str] | None:
  """
  可以由系统直接核对的事实。违反时：先打回让专家改；打回次数用尽仍违反，就把这条 GAP 降级为 PARITY
  （第三次评测：c14 / c17 连续被打回 2~3 次，模型始终不改，最后照样以 GAP 过关）。
  """
  if str(finding.get("polarity") or GAP) != GAP or str(finding.get("outcome") or "FINDING") != "FINDING":
    return None
  dimension = str(finding.get("dimension") or "")
  finding_type = str(finding.get("finding_type") or "")
  alias, best = _best_reference(finding, evidence_pack)
  target = evidence_pack.get("targetEvidence") or {}

  if dimension == "HOOK":
    if text_similarity(opening_text(target), opening_text(best)) >= SAME_OPENING_SIMILARITY:
      return {"rule": "same_opening", "message": f"目标与 {alias} 开场 5 秒内的口播和屏幕文字几乎相同，不能判为开场差距（相同应为 PARITY）。"}
    if finding_type == "hook_no_value_promise":
      same_speech = text_similarity(opening_text(target, channels=("speech",)), opening_text(best, channels=("speech",)))
      if same_speech >= SAME_OPENING_SIMILARITY:
        return {
          "rule": "same_opening_speech",
          "message": f"目标与 {alias} 开场口播几乎相同，价值承诺是一样的，不能判为 hook_no_value_promise；"
          "如果差别只在屏幕文字，请改为 hook_weak_visual_text。",
        }

  if dimension == "STRUCTURE_RHYTHM":
    if finding_type in {"pacing_too_dense", "pacing_too_slow"}:
      same = same_pacing(scene_stats(target, "T") or {}, scene_stats(best, alias) or {})
      if same:
        return {
          "rule": "same_pacing",
          "message": f"目标与 {alias} 的镜头节奏几乎相同（{same}），不能判为节奏过快/过慢。",
        }
    if finding_type == "structure_unclear":
      markers = set(_STEP_MARKER.findall(_all_text(target)))
      if len(markers) >= 2:
        return {
          "rule": "has_step_markers",
          "message": f"目标的口播 / 字幕里已经有分段标记（{'、'.join(sorted(markers)[:4])}），不能判为 structure_unclear。",
        }

  if dimension == "VALUE_DELIVERY" and finding_type == "value_late":
    target_first, reference_first = _benefit_times(finding)
    if target_first is not None and reference_first is not None and target_first - reference_first < VALUE_LATE_MIN_GAP_SECONDS:
      return {
        "rule": "benefit_not_late",
        "message": f"按你填写的 first_benefit_seconds，目标第 {target_first} 秒、参考第 {reference_first} 秒就说出收益，"
        "目标并不比参考晚，不能判为 value_late。",
      }
  return None


def enforce_hard_rules(findings: list[dict[str, Any]], evidence_pack: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
  """合成前：仍违反硬规则的 GAP 降级为 PARITY，并记录原因（会出现在 synthesis.parity 里）。"""
  rows: list[dict[str, Any]] = []
  notes: list[str] = []
  for finding in findings:
    violation = hard_rule_violation(finding, evidence_pack)
    if violation:
      notes.append(f"{finding.get('skill_key')} downgraded to PARITY: {violation['rule']}")
      finding = {
        **finding,
        "polarity": "PARITY",
        "finding_type": "parity",
        "confidence": min(float(finding.get("confidence") or 0), 0.5),
        "downgraded": {"rule": violation["rule"], "reason": violation["message"], "originalType": finding.get("finding_type")},
      }
    rows.append(finding)
  return rows, notes
