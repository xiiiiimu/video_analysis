from __future__ import annotations

import logging
from typing import Any

from agent_service.tools.adapters.http_client import JavaBackendError, JavaBackendHttpClient

logger = logging.getLogger(__name__)


class AnalysisJobToolAdapter:
  def __init__(self, client: JavaBackendHttpClient | None = None) -> None:
    self._client = client or JavaBackendHttpClient()

  def bind_trace(self, trace_id: str) -> None:
    self._client.set_trace_id(trace_id)

  def get_job_context(self, job_id: str) -> dict[str, Any]:
    """读取任务上下文（权威数据来自 Java MySQL）。"""
    try:
      return self._client.get(f"/internal/v1/analysis/jobs/{job_id}/context")
    except JavaBackendError as exc:
      logger.error("get_job_context failed job_id=%s error=%s", job_id, exc)
      raise

  def report_agent_success(
    self,
    job_id: str,
    draft_observations: list[str],
    agent_run_id: str | None = None,
    result_version: int = 1,
    agent_trace: list[dict[str, Any]] | None = None,
  ) -> dict[str, Any]:
    return self._report_result(
      job_id=job_id,
      status="SUCCESS",
      draft_observations=draft_observations,
      error_message=None,
      agent_run_id=agent_run_id,
      result_version=result_version,
      agent_trace=agent_trace or [],
    )

  def report_agent_failure(
    self,
    job_id: str,
    error_message: str,
    agent_run_id: str | None = None,
    result_version: int = 1,
    agent_trace: list[dict[str, Any]] | None = None,
  ) -> dict[str, Any]:
    return self._report_result(
      job_id=job_id,
      status="FAILED",
      draft_observations=[],
      error_message=error_message,
      agent_run_id=agent_run_id,
      result_version=result_version,
      agent_trace=agent_trace or [],
    )

  def save_agent_draft_result(self, job_id: str, draft_observations: list[str]) -> dict[str, Any]:
    return self.report_agent_success(job_id, draft_observations)

  def _report_result(
    self,
    job_id: str,
    status: str,
    draft_observations: list[str],
    error_message: str | None,
    agent_run_id: str | None = None,
    result_version: int = 1,
    agent_trace: list[dict[str, Any]] | None = None,
  ) -> dict[str, Any]:
    try:
      return self._client.post(
        f"/internal/v1/analysis/jobs/{job_id}/agent-results",
        {
          "jobId": job_id,
          "status": status,
          "agentRunId": agent_run_id,
          "resultVersion": result_version,
          "draftObservations": draft_observations,
          "agentTrace": agent_trace or [],
          "errorMessage": error_message,
        },
      )
    except JavaBackendError as exc:
      logger.error("report_agent_result failed job_id=%s status=%s error=%s", job_id, status, exc)
      raise

  def report_agent_progress(
    self,
    job_id: str,
    agent_run_id: str,
    stage: str,
    percent: int,
    status: str = "RUNNING",
    short_summary: str = "",
  ) -> dict[str, Any]:
    try:
      return self._client.post(
        f"/internal/v1/analysis/jobs/{job_id}/agent-progress",
        {
          "jobId": job_id,
          "agentRunId": agent_run_id,
          "stage": stage,
          "percent": percent,
          "status": status,
          "shortSummary": short_summary,
        },
      )
    except JavaBackendError as exc:
      logger.warning("report_agent_progress failed job_id=%s stage=%s error=%s", job_id, stage, exc)
      raise
