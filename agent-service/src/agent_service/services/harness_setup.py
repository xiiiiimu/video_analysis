"""
组合根（composition root）：把诊断图、工具和诊断业务的 intervention 交给 harness 组装。

harness 本身不认识业务（不导入 graph）；“诊断服务用哪张图、哪些规则”在这里决定。
job_runner、main 的演示模式、eval 都从这里拿 harness，保证三处行为一致。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any

from agent_service.graph.builder import build_diagnosis_graph
from agent_service.graph.policies import diagnosis_interventions
from agent_service.harness import (
  FatalToolErrorPlugin,
  HarnessLimits,
  HarnessRunner,
  Plugin,
  build_harness,
)
from agent_service.harness.errors import UnknownToolError
from agent_service.tools.adapters.errors import JavaBackendError

_FATAL_STATUS = {401, 403}


def is_fatal_tool_error(exc: BaseException) -> bool:
  """鉴权失败、熔断打开、未知工具：重试无意义，直接结束 run。404/422 等交给 Specialist 处理。"""
  if isinstance(exc, UnknownToolError):
    return True
  if isinstance(exc, JavaBackendError):
    return exc.status_code in _FATAL_STATUS or "circuit breaker is open" in str(exc)
  return False


@lru_cache
def cached_diagnosis_graph() -> Any:
  return build_diagnosis_graph()


def create_diagnosis_harness(
  tools: dict[str, Callable[..., Any]],
  *,
  graph: Any | None = None,
  limits: HarnessLimits | None = None,
  plugins: Sequence[Plugin] | None = None,
  builtin_plugins: Sequence[str] | None = None,
  trace_id: str | None = None,
) -> HarnessRunner:
  return build_harness(
    graph if graph is not None else cached_diagnosis_graph(),
    tools,
    limits=limits,
    plugins=[FatalToolErrorPlugin(is_fatal_tool_error), *(plugins or [])],
    interventions=diagnosis_interventions(),
    builtin_plugins=builtin_plugins,
    trace_id=trace_id,
  )
