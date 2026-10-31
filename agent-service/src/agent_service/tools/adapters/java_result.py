from __future__ import annotations

from typing import Any

from agent_service.tools.adapters.errors import JavaBackendError


def unwrap_java_result(payload: dict[str, Any]) -> Any:
  """解析 Java 统一 Result<T> 包装：{success, data, error, traceId}。"""
  if "success" in payload:
    if not payload.get("success"):
      raise JavaBackendError(str(payload.get("error") or "Java API returned success=false"))
    return payload.get("data")
  return payload
