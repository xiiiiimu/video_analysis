"""
预算与取消插件（参考 Strands 的 invocation limits / cancellation）。

- 计数由 runner 负责（机制），本插件只负责“是否超出”（策略）；
- 检查发生在每个检查点开始之前：节点开始前、工具调用前、模型调用前，
  不会在调用进行中打断，所以单次调用可能略微超出预算，但下一次不会再开始；
- 超出时调用 ``ctx.request_stop(reason)``：记录停止原因并设置取消信号，
  其它并行分支会在各自的下一个检查点以同一个原因退出。
"""

from __future__ import annotations

from agent_service.harness.errors import StopRun
from agent_service.harness.events import BeforeModelCallEvent, BeforeNodeEvent, BeforeToolCallEvent
from agent_service.harness.hooks import HookOrder
from agent_service.harness.plugins.base import Plugin, hook
from agent_service.harness.types import HarnessContext, HarnessLimits


def _stop(ctx: HarnessContext, reason: str, message: str) -> None:
  ctx.request_stop(reason)
  raise StopRun(ctx.stop_reason or reason, message)


def _check_cancelled(ctx: HarnessContext) -> None:
  if ctx.cancelled:
    reason = ctx.stop_reason or "cancelled"
    raise StopRun(reason, f"Run stopped: {reason}")


class LimitsPlugin(Plugin):
  name = "limits"

  def __init__(self, limits: HarnessLimits) -> None:
    super().__init__()
    self.limits = limits

  @hook(order=HookOrder.LIMITS)
  def before_node(self, event: BeforeNodeEvent) -> None:
    _check_cancelled(event.ctx)
    steps = event.ctx.incr("graph_steps")
    if steps > self.limits.max_graph_steps:
      _stop(event.ctx, "limit_steps", f"Max graph steps exceeded: {steps}/{self.limits.max_graph_steps}")

  @hook(order=HookOrder.LIMITS)
  def before_tool(self, event: BeforeToolCallEvent) -> None:
    _check_cancelled(event.ctx)
    if event.ctx.turns >= self.limits.max_turns:
      _stop(event.ctx, "limit_turns", f"Max turns exceeded: {event.ctx.turns}/{self.limits.max_turns}")

  @hook(order=HookOrder.LIMITS)
  def before_model(self, event: BeforeModelCallEvent) -> None:
    _check_cancelled(event.ctx)
    if event.ctx.token_usage >= self.limits.max_tokens:
      _stop(event.ctx, "limit_tokens", f"Max tokens exceeded: {event.ctx.token_usage}/{self.limits.max_tokens}")
