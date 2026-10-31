"""审计插件：订阅所有生命周期事件，是审计日志的唯一出口。"""

from __future__ import annotations

from typing import Any

from agent_service.harness.audit import AuditLogger
from agent_service.harness.events import (
  AfterModelCallEvent,
  AfterNodeEvent,
  AfterRunEvent,
  AfterToolCallEvent,
  BeforeModelCallEvent,
  BeforeNodeEvent,
  BeforeRunEvent,
  BeforeToolCallEvent,
  InfraCallEvent,
)
from agent_service.harness.hooks import HookOrder
from agent_service.harness.plugins.base import Plugin, hook
from agent_service.harness.types import HarnessContext

_RUN_FINISHED_EVENT = {
  "success": "harness_finished",
  "timeout": "harness_timeout",
  "guardrail_blocked": "harness_guardrail_blocked",
  "failed": "harness_failed",
}


class AuditPlugin(Plugin):
  """
  事件名沿用改造前的约定（docs/12），日志系统按 ``audit=true`` 过滤的规则不需要改：
  harness_started / harness_finished / harness_failed / harness_timeout / harness_guardrail_blocked、
  graph_step、tool_call_started / tool_call_finished / tool_call_error。
  新增：model_call_started / model_call_finished / model_call_error、infra_call。

  ``order=HookOrder.FIRST``：Before 事件最先记录，After 事件最后记录（看到最终结果）。
  """

  name = "audit"

  def __init__(self, logger: AuditLogger | None = None, *, record_in_context: bool = True) -> None:
    super().__init__()
    self._logger = logger or AuditLogger()
    self._record = record_in_context

  def _emit(self, ctx: HarnessContext, event: str, **fields: Any) -> None:
    fields.setdefault("job_id", ctx.job_id or ctx.task_id)
    self._logger.log(event, trace_id=ctx.trace_id, task_id=ctx.task_id, **fields)
    if self._record:
      ctx.record(event, **fields)

  @hook(order=HookOrder.FIRST)
  def on_run_start(self, event: BeforeRunEvent) -> None:
    self._emit(event.ctx, "harness_started", input=event.input_payload)

  @hook(order=HookOrder.FIRST)
  def on_run_end(self, event: AfterRunEvent) -> None:
    result = event.result
    self._emit(
      event.ctx,
      _RUN_FINISHED_EVENT.get(result.status, "harness_finished"),
      status=result.status,
      stop_reason=result.stop_reason,
      turns=result.turns,
      graph_steps=event.ctx.graph_steps,
      usage=result.usage,
      error=result.error,
      hypothesis_count=len((result.output or {}).get("draft_hypotheses") or []),
    )

  @hook(order=HookOrder.FIRST)
  def on_node_start(self, event: BeforeNodeEvent) -> None:
    self._emit(event.ctx, "graph_step", node=event.node, graph_step=event.ctx.graph_steps + 1)

  @hook(order=HookOrder.FIRST)
  def on_node_end(self, event: AfterNodeEvent) -> None:
    if event.exception is not None and isinstance(event.exception, Exception):
      self._emit(event.ctx, "graph_step_error", node=event.node, error=str(event.exception))

  @hook(order=HookOrder.FIRST)
  def on_tool_start(self, event: BeforeToolCallEvent) -> None:
    self._emit(event.ctx, "tool_call_started", tool_name=event.tool_name, agent_id=event.agent_id, args=event.tool_args)

  @hook(order=HookOrder.FIRST)
  def on_tool_end(self, event: AfterToolCallEvent) -> None:
    if event.exception is not None:
      self._emit(
        event.ctx,
        "tool_call_error",
        tool_name=event.tool_name,
        agent_id=event.agent_id,
        attempt=event.attempt,
        error=str(event.exception),
        retry=event.retry,
      )
      return
    self._emit(
      event.ctx,
      "tool_call_finished",
      tool_name=event.tool_name,
      agent_id=event.agent_id,
      attempt=event.attempt,
      result_type=type(event.result).__name__,
    )

  @hook(order=HookOrder.FIRST)
  def on_model_start(self, event: BeforeModelCallEvent) -> None:
    self._emit(event.ctx, "model_call_started", agent_id=event.agent_id, attempt=event.attempt)

  @hook(order=HookOrder.FIRST)
  def on_model_end(self, event: AfterModelCallEvent) -> None:
    error = event.exception or event.parse_error
    self._emit(
      event.ctx,
      "model_call_error" if error is not None else "model_call_finished",
      agent_id=event.agent_id,
      attempt=event.attempt,
      usage=event.usage,
      error=str(error) if error is not None else None,
      retry=event.retry,
    )

  @hook(order=HookOrder.FIRST)
  def on_infra_call(self, event: InfraCallEvent) -> None:
    self._emit(
      event.ctx,
      "infra_call",
      name=event.name,
      error=str(event.exception) if event.exception is not None else None,
    )
