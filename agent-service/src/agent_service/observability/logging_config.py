"""Structured JSON logging for log systems (ELK / Loki / Datadog)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
  def format(self, record: logging.LogRecord) -> str:
    payload: dict[str, Any] = {
      "timestamp": datetime.now(UTC).isoformat(),
      "level": record.levelname,
      "logger": record.name,
      "message": record.getMessage(),
    }
    if hasattr(record, "audit_payload") and isinstance(record.audit_payload, dict):
      payload.update(record.audit_payload)
    return json.dumps(payload, ensure_ascii=False)


def configure_structured_logging(level: int = logging.INFO) -> None:
  root = logging.getLogger()
  if any(isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, JsonLogFormatter) for handler in root.handlers):
    return
  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(JsonLogFormatter())
  root.handlers.clear()
  root.addHandler(handler)
  root.setLevel(level)
