from __future__ import annotations

import logging
from typing import Any

from agent_service.tools.adapters.http_client import JavaBackendError, JavaBackendHttpClient

logger = logging.getLogger(__name__)


class HypothesisToolAdapter:
  """保存 Agent 诊断假设到 Java（映射为 Finding 落库）。"""

  def __init__(self, client: JavaBackendHttpClient | None = None) -> None:
    self._client = client or JavaBackendHttpClient()

  def bind_trace(self, trace_id: str) -> None:
    self._client.set_trace_id(trace_id)

  def save_diagnosis_hypothesis(self, job_id: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    """逐条保存（旧接口）。批量接口不可用时的回退路径，每条带自己的幂等键。"""
    payload = {
      **self._finding_payload(job_id, hypothesis),
      "idempotencyKey": hypothesis.get("idempotency_key"),
    }
    try:
      finding_id = self._client.post(f"/internal/v1/analysis/jobs/{job_id}/hypotheses", payload)
      return {"findingId": finding_id, "jobId": job_id}
    except JavaBackendError as exc:
      logger.error("save_diagnosis_hypothesis failed job_id=%s error=%s", job_id, exc)
      raise

  def save_diagnosis_result(
    self,
    job_id: str,
    agent_run_id: str,
    result_version: int,
    idempotency_key: str,
    findings: list[dict[str, Any]],
    synthesis: dict[str, Any],
  ) -> dict[str, Any]:
    """
    一次性保存整次 run 的结论 + 合成结果（Java 端事务写入，按 idempotencyKey 去重）。

    同一个 idempotencyKey 重复提交时 Java 返回第一次的结果，不会产生重复 Finding。
    """
    payload = {
      "jobId": job_id,
      "agentRunId": agent_run_id,
      "resultVersion": result_version,
      "idempotencyKey": idempotency_key,
      "findings": [self._finding_payload(job_id, item) for item in findings],
      "synthesis": synthesis,
    }
    try:
      result = self._client.post(f"/internal/v1/analysis/jobs/{job_id}/diagnosis-results", payload)
    except JavaBackendError as exc:
      logger.error("save_diagnosis_result failed job_id=%s error=%s", job_id, exc)
      raise
    return result if isinstance(result, dict) else {"findingIds": list(result or [])}

  @staticmethod
  def _finding_payload(job_id: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    return {
      "jobId": job_id,
      "skillKey": hypothesis.get("skill_key"),
      "dimension": hypothesis.get("dimension"),
      "outcome": hypothesis.get("outcome") or "FINDING",
      "findingType": hypothesis.get("finding_type"),
      "observation": hypothesis.get("observation"),
      "differenceText": hypothesis.get("difference_text"),
      "hypothesisText": hypothesis.get("hypothesis_text"),
      "suggestedAction": hypothesis.get("suggested_action"),
      "evidenceRefs": hypothesis.get("evidence_refs") or [],
      "videoEvidenceRefs": hypothesis.get("video_evidence_refs") or [],
      "knowledgeEvidenceRefs": hypothesis.get("knowledge_evidence_refs") or [],
      "targetFrameRefs": hypothesis.get("target_frame_refs") or [],
      "referenceFrameRefs": hypothesis.get("reference_frame_refs") or [],
      "counterEvidence": hypothesis.get("counter_evidence"),
      "confidence": hypothesis.get("confidence"),
      # 与合成排序一致的优先级（P0/P1/P2）；旧版 Java 忽略未知字段
      "priority": hypothesis.get("priority"),
    }
