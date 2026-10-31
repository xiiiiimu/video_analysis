from __future__ import annotations

import logging
from typing import Any

from agent_service.tools.adapters.http_client import JavaBackendError, JavaBackendHttpClient

logger = logging.getLogger(__name__)


class VideoEvidenceToolAdapter:
  """获取视频帧证据包（关键帧 URL/时间戳、转写、场景/OCR JSON）。"""

  def __init__(self, client: JavaBackendHttpClient | None = None) -> None:
    self._client = client or JavaBackendHttpClient()

  def bind_trace(self, trace_id: str) -> None:
    self._client.set_trace_id(trace_id)

  def get_video_evidence(self, job_id: str) -> dict[str, Any]:
    try:
      return self._client.get(f"/internal/v1/analysis/jobs/{job_id}/evidence")
    except JavaBackendError as exc:
      logger.error("get_video_evidence failed job_id=%s error=%s", job_id, exc)
      raise
