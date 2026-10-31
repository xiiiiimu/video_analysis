from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent_service.graph.criteria import (
  apply_criteria_to_synthesis,
  build_criteria_report,
  render_report_markdown,
)
from agent_service.graph.runtime import build_lightweight_trace, report_stage, trace_step
from agent_service.graph.state import AgentGraphState
from agent_service.graph.supplementary import run_supplementary
from agent_service.graph.synthesis import (
  assign_priorities,
  build_rule_synthesis,
  persistable_findings,
  refine_with_llm,
)
from agent_service.harness.context import harness_scope

logger = logging.getLogger(__name__)

PERSISTABLE_OUTCOMES = {"FINDING", "ABSTAIN"}


def synthesizer_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
  """
  Evaluator 通过后：跨维度合成 → 一次性幂等保存到 Java。

  - 只保存 FINDING / ABSTAIN，NEEDS_CAPABILITY 永远不会作为结论落库；
  - 优先调用批量接口 ``save_diagnosis_result``（整批一个幂等键，Java 端事务写入）；
    旧版 Java 没有该接口时回退到逐条保存，每条带自己的幂等键。
  """
  harness = config["configurable"]["harness"]
  harness_ctx = config["configurable"]["harness_ctx"]
  job_id = state["job_id"]
  run_id = str(state.get("run_id") or "")
  result_version = int(state.get("result_version") or 1)
  report_stage(state, config, "SYNTHESIZING", 95, "Synthesizing and saving findings.")

  with trace_step(state, "synthesizer", input_summary=f"findings={len(state.get('findings') or [])}") as step:
    findings = [item for item in state.get("findings") or [] if item.get("outcome", "FINDING") in PERSISTABLE_OUTCOMES]
    completion_status = str(state.get("diagnosis_completion_status") or "COMPLETED")
    synthesis = build_rule_synthesis(
      findings,
      completion_status=completion_status,
      evaluation_results=list(state.get("evaluation_results") or []),
      handoff_answers=list(state.get("handoff_answers") or []),
      dropped_handoffs=list(state.get("dropped_handoffs") or []),
    )
    with harness_scope(harness, harness_ctx, agent_id=None):
      synthesis = refine_with_llm(synthesis, findings)

    # 用户评分标准：补充分析（默认只处理三个专家之外的标准；勾选"整体补充分析"时再给补充观察）+ 逐条对照报告
    job_context = state.get("job_context") or {}
    criteria = list(job_context.get("user_criteria") or [])
    supplementary = None
    try:
      with harness_scope(harness, harness_ctx, agent_id="supplementary_analysis"):
        supplementary = run_supplementary(job_context, state.get("evidence_pack") or {}, findings)
    except Exception as exc:  # noqa: BLE001 - 补充分析失败不影响三个专家的结论落库
      logger.warning("supplementary_analysis_failed error=%s", exc)
      supplementary = {"mode": "failed", "error": str(exc), "verdicts": [], "notes": []}
    synthesis["criteria"] = criteria
    synthesis["criteriaReport"] = build_criteria_report(criteria, findings, supplementary)
    synthesis["supplementary"] = supplementary or {}
    synthesis = apply_criteria_to_synthesis(synthesis, synthesis["criteriaReport"])
    synthesis["reportMarkdown"] = render_report_markdown(synthesis, findings)

    # 优先级与合成排序一致；v2 下优势 / 相当不作为 Finding 落库（只在 synthesis.strengths / parity 里）
    findings = persistable_findings(assign_priorities(findings, synthesis))
    saved_ids = _save(harness, harness_ctx, job_id, run_id, result_version, findings, synthesis)

    observations = list(state.get("draft_observations", []))
    observations.append(f"synthesis:{synthesis['summary']}")
    observations.append(f"synthesized_findings:{len(saved_ids)}")
    observations.append(f"agent_run_status:{completion_status}")
    agent_trace = build_lightweight_trace(state)
    step["tool_calls"] = [{"tool_name": "save_diagnosis_result", "count": len(saved_ids)}]
    step["output_summary"] = f"saved={len(saved_ids)} synthesis={synthesis['source']}"
    report_stage(state, config, "COMPLETED", 100, "Agent run completed.")
    return {
      "draft_observations": observations,
      "synthesis": synthesis,
      "status": completion_status,
      "diagnosis_completion_status": completion_status,
      "agent_trace": agent_trace,
      "next_action": "finish",
      "done": True,
      "step_traces": state["step_traces"],
    }


def _save(
  harness: Any,
  ctx: Any,
  job_id: str,
  run_id: str,
  result_version: int,
  findings: list[dict[str, Any]],
  synthesis: dict[str, Any],
) -> list[str]:
  batch_key = f"{run_id}:v{result_version}"
  if "save_diagnosis_result" in getattr(harness, "tool_names", []):
    try:
      result = harness.call_tool(
        ctx,
        "save_diagnosis_result",
        job_id=job_id,
        agent_run_id=run_id,
        result_version=result_version,
        idempotency_key=batch_key,
        findings=findings,
        synthesis=synthesis,
      )
      return [str(item) for item in (result or {}).get("findingIds") or []]
    except Exception as exc:
      # 旧版 Java 没有该接口：Spring 返回 404/405；本项目的 GlobalExceptionHandler 会把
      # NoResourceFoundException 映射成 500，所以 500/501 也走降级。批量接口是 @Transactional，
      # 失败即整体回滚，逐条保存又带幂等键，因此降级不会产生重复数据。
      if getattr(exc, "status_code", None) not in (404, 405, 500, 501):
        raise
      logger.warning("save_diagnosis_result endpoint unavailable, falling back to per-finding save: %s", exc)

  saved_ids: list[str] = []
  for finding in findings:
    result = harness.call_tool(
      ctx,
      "save_diagnosis_hypothesis",
      job_id=job_id,
      hypothesis={**finding, "idempotency_key": f"{batch_key}:{finding.get('skill_key')}"},
    )
    if isinstance(result, dict) and result.get("findingId"):
      saved_ids.append(str(result["findingId"]))
    elif isinstance(result, str):
      saved_ids.append(result)
  return saved_ids
