from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("agent_service.audit")


class AuditLogger:
  """
  结构化审计日志，输出单行 JSON，便于对接 ELK / Loki / Datadog。

  字段约定：
  - audit: true（便于日志系统过滤）
  - event: 事件名
  - trace_id / task_id / job_id
  - timestamp: ISO8601 UTC

  无状态：trace_id / task_id 每次从调用方传入，同一个实例可以被多个 run 安全共享。
  """

  def log(self, event: str, *, trace_id: str = "-", task_id: str = "-", **fields: Any) -> None:
    payload = {
      "audit": True,
      "event": event,
      "trace_id": trace_id or "-",
      "task_id": task_id or "-",
      "timestamp": datetime.now(UTC).isoformat(),
      **fields,
    }
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))
