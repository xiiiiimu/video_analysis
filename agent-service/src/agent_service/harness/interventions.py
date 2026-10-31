"""
Interventions：返回“决策”而不是直接改事件（参考 strands/interventions/）。

handler 只负责表态，由 InterventionPlugin 统一仲裁并修改一次事件：
- 按注册顺序评估，只调用覆写了对应方法的 handler；
- ``Deny`` 短路，后面的 handler 不再评估；
- ``Guide`` 累积，所有反馈合并成一条（每条带 ``[handler名]`` 前缀）；
- ``Transform`` 原地修改事件，后面的 handler 看到修改后的内容；
- handler 自己抛异常时按 ``on_error`` 处理：throw（默认）/ deny（fail-closed）/ proceed（fail-open）。

决策在不同事件上的效果：

  | 决策      | before_tool_call      | after_tool_call | before_model_call | after_model_call   |
  |-----------|-----------------------|-----------------|-------------------|--------------------|
  | Deny      | 取消工具调用          | —               | 取消模型调用      | —                  |
  | Guide     | 取消并把反馈作为结果  | —               | 追加一条 user 消息 | 追加反馈并重试     |
  | Transform | 修改                  | 修改            | 修改              | 修改               |

  — 表示不支持：会记一条 warning，不生效。

⚠ after_model_call 上的 Guide 会触发重试，handler 必须自己保证收敛
  （例如看 ``event.attempt``，超过次数就返回 Proceed）。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from agent_service.harness.audit import AuditLogger
from agent_service.harness.errors import StopRun
from agent_service.harness.events import (
  AfterModelCallEvent,
  AfterToolCallEvent,
  BeforeModelCallEvent,
  BeforeToolCallEvent,
  HarnessEvent,
)
from agent_service.harness.hooks import HookOrder
from agent_service.harness.plugins.base import Plugin, hook

logger = logging.getLogger(__name__)

OnError = Literal["throw", "deny", "proceed"]


@dataclass(frozen=True)
class Proceed:
  reason: str | None = None
  type: str = field(default="proceed", init=False)


@dataclass(frozen=True)
class Deny:
  reason: str = ""
  type: str = field(default="deny", init=False)


@dataclass(frozen=True)
class Guide:
  feedback: str = ""
  reason: str | None = None
  type: str = field(default="guide", init=False)


@dataclass(frozen=True)
class Transform:
  apply: Callable[[Any], None] = field(default=lambda event: None)
  reason: str | None = None
  type: str = field(default="transform", init=False)


InterventionAction = Proceed | Deny | Guide | Transform


class InterventionHandler:
  """覆写需要的方法即可；未覆写的方法不会被调用。"""

  name: str = ""
  on_error: OnError = "throw"

  def before_tool_call(self, event: BeforeToolCallEvent) -> InterventionAction:
    return Proceed()

  def after_tool_call(self, event: AfterToolCallEvent) -> InterventionAction:
    return Proceed()

  def before_model_call(self, event: BeforeModelCallEvent) -> InterventionAction:
    return Proceed()

  def after_model_call(self, event: AfterModelCallEvent) -> InterventionAction:
    return Proceed()


def _is_overridden(handler: InterventionHandler, method: str) -> bool:
  return getattr(type(handler), method, None) is not getattr(InterventionHandler, method)


class InterventionPlugin(Plugin):
  name = "interventions"

  def __init__(self, handlers: list[InterventionHandler], audit: AuditLogger | None = None) -> None:
    super().__init__()
    seen: set[str] = set()
    for handler in handlers:
      if not handler.name:
        raise ValueError(f"{type(handler).__name__} must define a name")
      if handler.name in seen:
        raise ValueError(f"Duplicate intervention handler name: {handler.name}")
      seen.add(handler.name)
    self.handlers = list(handlers)
    self._audit = audit or AuditLogger()

  # Before 类事件放在其它 hook 之后（INTERVENTION_INPUT），After 类事件放在前面（INTERVENTION_OUTPUT），
  # 与 Strands 一致：决策基于其它 hook 处理后的内容。

  @hook(order=HookOrder.INTERVENTION_INPUT)
  def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
    self._dispatch(event, "before_tool_call")

  @hook(order=HookOrder.INTERVENTION_OUTPUT)
  def _on_after_tool_call(self, event: AfterToolCallEvent) -> None:
    self._dispatch(event, "after_tool_call")

  @hook(order=HookOrder.INTERVENTION_INPUT)
  def _on_before_model_call(self, event: BeforeModelCallEvent) -> None:
    self._dispatch(event, "before_model_call")

  @hook(order=HookOrder.INTERVENTION_OUTPUT)
  def _on_after_model_call(self, event: AfterModelCallEvent) -> None:
    self._dispatch(event, "after_model_call")

  # ------------------------------------------------------------------ 仲裁

  def _dispatch(self, event: HarnessEvent, method: str) -> None:
    guides: list[tuple[str, Guide]] = []
    for handler in self.handlers:
      if not _is_overridden(handler, method):
        continue
      try:
        action = getattr(handler, method)(event)
      except StopRun:
        raise
      except Exception as error:  # noqa: BLE001 - handler boundary
        action = self._handle_error(handler, method, error)
        if action is None:
          continue
      if action is None:
        raise TypeError(f"handler '{handler.name}.{method}' returned None; expected an InterventionAction")
      if isinstance(action, Guide):
        guides.append((handler.name, action))
        continue
      if not isinstance(action, Proceed):
        self._log(event, handler.name, method, action)
      if self._apply(event, method, action, handler.name):
        return
    if guides:
      feedback = "\n".join(f"[{name}] {guide.feedback}" for name, guide in guides)
      merged = Guide(feedback=feedback)
      self._log(event, ",".join(name for name, _ in guides), method, merged)
      self._apply(event, method, merged, "")

  def _apply(self, event: Any, method: str, action: InterventionAction, handler_name: str) -> bool:
    """返回 True 表示短路。"""
    if isinstance(action, Proceed):
      return False
    if isinstance(action, Transform):
      action.apply(event)
      return False
    if method == "before_tool_call":
      if isinstance(action, Deny):
        event.cancel_tool = f"DENIED: {action.reason}"
        return True
      if isinstance(action, Guide):
        event.cancel_tool = f"GUIDANCE: {action.feedback}"
        return False
    elif method == "before_model_call":
      if isinstance(action, Deny):
        event.cancel = f"DENIED: {action.reason}"
        return True
      if isinstance(action, Guide):
        event.messages.append({"role": "user", "content": action.feedback})
        return False
    elif method == "after_model_call":
      if isinstance(action, Guide):
        event.messages.append({"role": "user", "content": action.feedback})
        event.retry = True
        return False
    logger.warning("handler=<%s> event=<%s> | %s has no effect", handler_name, method, action.type)
    return False

  def _handle_error(self, handler: InterventionHandler, method: str, error: Exception) -> InterventionAction | None:
    if handler.on_error == "deny":
      logger.warning("handler=<%s> event=<%s> on_error=deny | %s", handler.name, method, error)
      return Deny(reason=f"Handler {handler.name} failed: {error}")
    if handler.on_error == "proceed":
      logger.warning("handler=<%s> event=<%s> on_error=proceed (fail-open) | %s", handler.name, method, error)
      return None
    raise error

  def _log(self, event: Any, handler_name: str, method: str, action: InterventionAction) -> None:
    ctx = event.ctx
    detail = getattr(action, "reason", None) or getattr(action, "feedback", None)
    fields = {
      "handler": handler_name,
      "lifecycle": method,
      "action": action.type,
      "detail": detail,
      "agent_id": getattr(event, "agent_id", None),
      "tool_name": getattr(event, "tool_name", None),
      "job_id": ctx.job_id or ctx.task_id,
    }
    self._audit.log("intervention_applied", trace_id=ctx.trace_id, task_id=ctx.task_id, **fields)
    ctx.record("intervention_applied", **fields)
