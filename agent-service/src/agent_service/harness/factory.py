"""
组装层（参考 strands_harness.create_harness）：解析 → 组装 → 构造。

1. 解析：limits 为空时从配置读取默认值；
2. 组装：内置插件（按名字选择）+ 调用方插件；内置 intervention handler + 调用方 handler；
3. 构造：返回一个普通的 HarnessRunner，没有任何额外包装。

调用方显式传入的值总是优先；内置插件可以通过 ``builtin_plugins`` 按名字关掉（便于消融实验）。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from agent_service.harness.defaults import BUILTIN_PLUGIN_NAMES, default_limits, default_plugins
from agent_service.harness.interventions import InterventionHandler
from agent_service.harness.plugins.base import Plugin
from agent_service.harness.runner import HarnessRunner
from agent_service.harness.types import HarnessLimits


def build_harness(
  graph: Any,
  tools: dict[str, Callable[..., Any]],
  *,
  limits: HarnessLimits | None = None,
  plugins: Sequence[Plugin] | None = None,
  interventions: Sequence[InterventionHandler] | None = None,
  builtin_plugins: Sequence[str] | None = None,
  trace_id: str | None = None,
) -> HarnessRunner:
  resolved_limits = limits or default_limits()
  enabled = set(BUILTIN_PLUGIN_NAMES if builtin_plugins is None else builtin_plugins)
  unknown = enabled - set(BUILTIN_PLUGIN_NAMES)
  if unknown:
    raise ValueError(f"Unknown builtin plugins: {sorted(unknown)}; available: {list(BUILTIN_PLUGIN_NAMES)}")

  builtins = [
    plugin
    for plugin in default_plugins(resolved_limits, extra_handlers=list(interventions or []))
    if plugin.name in enabled
  ]
  harness = HarnessRunner(
    compiled_graph=graph,
    tools=tools,
    limits=resolved_limits,
    plugins=[*builtins, *(plugins or [])],
  )
  if trace_id:
    harness.set_trace_id(trace_id)
  return harness
