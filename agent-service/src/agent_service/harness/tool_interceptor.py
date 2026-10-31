from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

from agent_service.harness.audit import AuditLogger
from agent_service.harness.types import HarnessContext

ToolCallable = Callable[..., Any]


class ToolInterceptor:
  """
  统一工具调用拦截器：所有护栏逻辑集中于此，禁止散落在 LangGraph node 内。

  职责：
  - 工具白名单校验
  - 参数 guardrails
  - 审计日志（结构化 JSON，对接日志系统）
  """

  def __init__(
    self,
    allowed_tools: set[str] | None = None,
    audit: AuditLogger | None = None,
  ) -> None:
    self._allowed_tools = allowed_tools or set()
    self._audit = audit

  def register_allowed_tools(self, names: Iterable[str]) -> None:
    self._allowed_tools.update(names)

  def before_call(self, ctx: HarnessContext, tool_name: str, args: dict[str, Any]) -> None:
    if self._allowed_tools and tool_name not in self._allowed_tools:
      raise GuardrailViolation(f"Tool not allowed: {tool_name}")

    if not args:
      raise GuardrailViolation(f"Tool args must not be empty: {tool_name}")

    ctx.record("tool_call_started", tool_name=tool_name, args=args)
    if self._audit:
      self._audit.log(
        "tool_call_started",
        job_id=ctx.task_id,
        tool_name=tool_name,
        args=args,
      )

  def after_call(self, ctx: HarnessContext, tool_name: str, result: Any) -> Any:
    ctx.record("tool_call_finished", tool_name=tool_name, result_type=type(result).__name__)
    if self._audit:
      self._audit.log(
        "tool_call_finished",
        job_id=ctx.task_id,
        tool_name=tool_name,
        result_type=type(result).__name__,
      )
    return result


class GuardrailViolation(Exception):
  pass
