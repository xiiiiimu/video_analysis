"""
区分“预期内”和“预期外”的工具错误（参考 Strands hooks 文档的 Exception Handling）。

- 预期内（参数不对、证据不存在 404……）：照常把异常交给调用方（ReAct 会把它变成一次失败的观察，
  Specialist 可以换一种证据或 ABSTAIN）；
- 预期外（鉴权失败、熔断打开、配置错误……）：重试或换策略都没有意义，立刻结束整个 run，
  stop_reason="error"，避免几个 Specialist 白白重试、最后才失败。

harness 只提供机制；“哪些错误算致命”由组合根传入的 ``is_fatal`` 决定。
"""

from __future__ import annotations

from collections.abc import Callable

from agent_service.harness.errors import StopRun, UnknownToolError
from agent_service.harness.events import AfterToolCallEvent
from agent_service.harness.hooks import HookOrder
from agent_service.harness.plugins.base import Plugin, hook


def _default_is_fatal(exc: BaseException) -> bool:
  return isinstance(exc, UnknownToolError)


class FatalToolErrorPlugin(Plugin):
  name = "fatal-tool-errors"

  def __init__(self, is_fatal: Callable[[BaseException], bool] | None = None) -> None:
    super().__init__()
    self._is_fatal = is_fatal or _default_is_fatal

  # After 事件按 order 反向执行：order 比审计（FIRST）更小，才会在审计之后执行，保证错误先被记下
  @hook(order=HookOrder.FIRST - 1)
  def check(self, event: AfterToolCallEvent) -> None:
    exc = event.exception
    if exc is None or not self._is_fatal(exc):
      return
    event.ctx.request_stop("error")
    raise StopRun("error", f"Fatal tool error from {event.tool_name}: {exc}")
