from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from agent_service.observability.trace import TraceContextFilter


class JsonLogFormatter(logging.Formatter):
  """将日志格式化为单行 JSON，便于 ELK / Loki / Datadog 采集。"""

  def format(self, record: logging.LogRecord) -> str:
    payload: dict[str, Any] = {
      "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
      "level": record.levelname,
      "logger": record.name,
      "message": record.getMessage(),
    }
    if hasattr(record, "audit") and record.audit:
      payload["audit"] = True
    for key in ("event", "trace_id", "task_id", "job_id", "tool_name"):
      if hasattr(record, key):
        payload[key] = getattr(record, key)
    if record.exc_info:
      payload["exception"] = self.formatException(record.exc_info)
    return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
  """初始化日志：默认文本；设置 AGENT_JSON_LOGS=1 时输出 JSON。"""
  level = os.getenv("AGENT_LOG_LEVEL", "INFO").upper()
  root = logging.getLogger()
  if root.handlers:
    return

  handler = logging.StreamHandler()
  # 每行日志带 trace_id / job_id（= Java 侧的 agentRunId / jobId），和 Java 日志的 [trace=... job=...] 对得上
  handler.addFilter(TraceContextFilter())
  if os.getenv("AGENT_JSON_LOGS", "0") == "1":
    handler.setFormatter(JsonLogFormatter())
  else:
    handler.setFormatter(
      logging.Formatter("%(asctime)s %(levelname)s [trace=%(trace_id)s job=%(job_id)s] [%(name)s] %(message)s")
    )

  root.addHandler(handler)
  root.setLevel(level)
  logging.getLogger("agent_service.audit").setLevel(level)
