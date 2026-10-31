"""
Harness 运行时：只提供机制，不做业务决策。

职责：
- run 生命周期：发 BeforeRun / AfterRun，启动超时定时器，返回带 stop_reason 的结果；
- 三个统一入口：``run_node``（LangGraph 节点）、``call_tool``（工具）、``call_model``（模型），
  每个入口都会发 Before / After 事件，并负责计数（轮次、步数、token）；
- ``call_infra``：进度上报等流程副作用，不计入预算，只发审计事件。

护栏、审计、重试、拦截全部是挂在事件上的插件（见 harness/plugins、harness/interventions），
runner 不认识任何业务字段，也不导入 graph / skills 等业务模块。
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from typing import Any

from agent_service.harness.context import current_scope
from agent_service.harness.errors import (
  ModelCallCancelled,
  StopRun,
  ToolCallCancelled,
  UnknownToolError,
)
from agent_service.harness.events import (
  AfterModelCallEvent,
  AfterNodeEvent,
  AfterRunEvent,
  AfterToolCallEvent,
  BeforeModelCallEvent,
  BeforeNodeEvent,
  BeforeRunEvent,
  BeforeToolCallEvent,
  HarnessEvent,
  InfraCallEvent,
)
from agent_service.harness.hooks import HookRegistry
from agent_service.harness.plugins.base import Plugin, PluginRegistry
from agent_service.harness.types import HarnessContext, HarnessLimits, HarnessRunResult, status_for

logger = logging.getLogger(__name__)

try:  # LangGraph 自带的递归上限，作为步数限额之外的兜底
  from langgraph.errors import GraphRecursionError
except ImportError:  # pragma: no cover - langgraph 是必需依赖，这里只是防御
  GraphRecursionError = RuntimeError  # type: ignore[misc,assignment]

_MAX_TOOL_ATTEMPTS = 10
_MAX_MODEL_ATTEMPTS = 10


class HarnessRunner:
  """
  兼容旧的构造方式：``HarnessRunner(compiled_graph=..., tools=..., limits=...)``。
  ``plugins`` 为 None 时使用 harness 默认插件（审计、限额、模型重试、输出格式守卫）；
  推荐通过 ``harness.factory.build_harness`` 组装。
  """

  def __init__(
    self,
    compiled_graph: Any,
    tools: dict[str, Callable[..., Any]],
    limits: HarnessLimits | None = None,
    plugins: list[Plugin] | None = None,
  ) -> None:
    from agent_service.harness.defaults import default_limits, default_plugins

    self._graph = compiled_graph
    self._tools = dict(tools)
    self.limits = limits or default_limits()
    self.hooks = HookRegistry()
    self.plugins = PluginRegistry(self.hooks)
    for plugin in default_plugins(self.limits) if plugins is None else plugins:
      self.plugins.add(plugin)
    self._trace_id = uuid.uuid4().hex

  # ------------------------------------------------------------------ 配置

  def set_trace_id(self, trace_id: str) -> None:
    self._trace_id = trace_id

  @property
  def tool_names(self) -> list[str]:
    return list(self._tools)

  def emit(self, event: HarnessEvent) -> HarnessEvent:
    return self.hooks.emit(event)

  # ------------------------------------------------------------------ run 生命周期

  def run(self, task_id: str, input_payload: dict[str, Any]) -> HarnessRunResult:
    ctx = HarnessContext(task_id=task_id, trace_id=self._trace_id, job_id=input_payload.get("job_id"))
    run_id = str(input_payload.get("agent_run_id") or self._trace_id)
    timer = self._start_deadline(ctx)
    state: dict[str, Any] = {}
    error: str | None = None
    try:
      self.emit(BeforeRunEvent(ctx=ctx, input_payload=dict(input_payload)))
      state = self._initial_state(input_payload, run_id)
      config = {
        "configurable": {"harness": self, "harness_ctx": ctx},
        # 步数限额由 LimitsPlugin 负责；LangGraph 的递归上限放宽一点只做兜底
        "recursion_limit": self.limits.max_graph_steps + 5,
      }
      for snapshot in self._graph.stream(state, config=config, stream_mode="values"):
        state = snapshot
      stop_reason = ctx.stop_reason or "completed"
    except StopRun as stop:
      stop_reason = ctx.stop_reason or stop.stop_reason
      error = ctx.stop_detail or str(stop)
    except GraphRecursionError as exc:
      stop_reason = "limit_steps"
      error = str(exc)
    except Exception as exc:  # run 边界：意外错误记录完整堆栈后以 failed 返回
      logger.exception("harness_run_failed task_id=%s trace_id=%s", task_id, self._trace_id)
      stop_reason = "error"
      error = str(exc)
    finally:
      if timer is not None:
        timer.cancel()

    result = HarnessRunResult(
      task_id=task_id,
      status=status_for(stop_reason),
      turns=ctx.turns,
      output=dict(state),  # 预算用完 / 超时时保留最后一个完整节点之后的 state，不再返回空 dict
      audit_events=ctx.audit_events,
      error=error,
      stop_reason=stop_reason,
      usage=ctx.usage(),
    )
    self.emit(AfterRunEvent(ctx=ctx, result=result))
    return result

  def _start_deadline(self, ctx: HarnessContext) -> threading.Timer | None:
    """超时 = 到点设置取消信号；各检查点看到信号后以 stop_reason='cancelled' 退出。"""
    seconds = self.limits.timeout_seconds
    if not seconds or seconds <= 0:
      return None
    timer = threading.Timer(seconds, ctx.request_stop, args=("cancelled",))
    timer.daemon = True
    timer.start()
    return timer

  def _initial_state(self, input_payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    """初始 state 由图自己提供（业务字段属于 graph 层），harness 只负责调用。"""
    factory = getattr(self._graph, "initial_state", None)
    if callable(factory):
      return dict(factory(input_payload, run_id))
    return {**input_payload, "run_id": run_id}

  # ------------------------------------------------------------------ 节点

  def run_node(
    self,
    ctx: HarnessContext,
    node: str,
    fn: Callable[[dict[str, Any], Any], dict[str, Any]],
    state: dict[str, Any],
    config: Any,
  ) -> dict[str, Any]:
    self.emit(BeforeNodeEvent(ctx=ctx, node=node))
    try:
      update = fn(state, config)
    except BaseException as exc:
      self.emit(AfterNodeEvent(ctx=ctx, node=node, exception=exc))
      raise
    self.emit(AfterNodeEvent(ctx=ctx, node=node, update=update))
    return update

  # ------------------------------------------------------------------ 工具

  def call_tool(self, ctx: HarnessContext, tool_name: str, **args: Any) -> Any:
    tool = self._tools.get(tool_name)
    if tool is None:
      raise UnknownToolError(f"Unknown tool: {tool_name}")
    agent_id = self._agent_id(ctx)

    before = BeforeToolCallEvent(ctx=ctx, tool_name=tool_name, tool_args=dict(args), agent_id=agent_id)
    self.emit(before)
    if before.cancel_tool:
      cancelled = ToolCallCancelled(before.cancel_tool)
      self.emit(
        AfterToolCallEvent(
          ctx=ctx, tool_name=tool_name, tool_args=before.tool_args, agent_id=agent_id, exception=cancelled
        )
      )
      raise cancelled

    attempt = 0
    while True:
      attempt += 1
      result: Any = None
      exc: Exception | None = None
      try:
        result = tool(**before.tool_args)
      except Exception as error:  # noqa: BLE001 - 交给 AfterToolCall hook 决定重试或抛出
        exc = error
      ctx.incr("turns")
      after = AfterToolCallEvent(
        ctx=ctx,
        tool_name=tool_name,
        tool_args=before.tool_args,
        agent_id=agent_id,
        attempt=attempt,
        result=result,
        exception=exc,
      )
      self.emit(after)
      if after.retry and attempt < _MAX_TOOL_ATTEMPTS:
        continue
      if exc is not None:
        raise exc
      return after.result

  # ------------------------------------------------------------------ 模型

  def call_model(
    self,
    ctx: HarnessContext,
    invoke: Callable[[list[dict[str, Any]]], Any],
    messages: list[dict[str, Any]],
    *,
    parse: Callable[[Any], Any] | None = None,
    agent_id: str | None = None,
  ) -> tuple[Any, Any]:
    agent_id = agent_id or self._agent_id(ctx)
    current = list(messages)
    attempt = 0
    while True:
      attempt += 1
      before = BeforeModelCallEvent(ctx=ctx, messages=current, agent_id=agent_id, attempt=attempt)
      self.emit(before)
      if before.cancel:
        raise ModelCallCancelled(before.cancel)

      response: Any = None
      parsed: Any = None
      usage: dict[str, int] = {}
      exc: Exception | None = None
      parse_error: Exception | None = None
      try:
        response = invoke(before.messages)
      except Exception as error:  # noqa: BLE001 - 交给 AfterModelCall hook 决定是否重试
        exc = error
      else:
        ctx.incr("model_calls")
        usage = extract_usage(response)
        ctx.add_usage(usage.get("input_tokens", 0), usage.get("output_tokens", 0))
        if parse is not None:
          try:
            parsed = parse(response)
          except Exception as error:  # noqa: BLE001
            parse_error = error

      after = AfterModelCallEvent(
        ctx=ctx,
        messages=list(before.messages),
        agent_id=agent_id,
        attempt=attempt,
        response=response,
        parsed=parsed,
        usage=usage,
        exception=exc,
        parse_error=parse_error,
      )
      self.emit(after)
      if after.retry and attempt < _MAX_MODEL_ATTEMPTS:
        current = list(after.messages)
        continue
      if exc is not None:
        raise exc
      if parse_error is not None:
        raise parse_error
      return response, parsed

  # ------------------------------------------------------------------ 基础设施调用

  def call_infra(self, ctx: HarnessContext, name: str, **args: Any) -> Any:
    """流程副作用（如进度上报）：不经过工具 hook、不计轮次，只发审计事件。"""
    fn = self._tools.get(name)
    if fn is None:
      return None
    try:
      result = fn(**args)
    except Exception as exc:
      self.emit(InfraCallEvent(ctx=ctx, name=name, args=args, exception=exc))
      raise
    self.emit(InfraCallEvent(ctx=ctx, name=name, args=args))
    return result

  # ------------------------------------------------------------------ 内部

  @staticmethod
  def _agent_id(ctx: HarnessContext) -> str | None:
    scope = current_scope()
    if scope is not None and scope.ctx is ctx:
      return scope.agent_id
    return None


def extract_usage(response: Any) -> dict[str, int]:
  """兼容 LangChain AIMessage（usage_metadata / response_metadata.token_usage）。"""
  meta = getattr(response, "usage_metadata", None)
  if isinstance(meta, dict) and meta:
    return {
      "input_tokens": int(meta.get("input_tokens") or 0),
      "output_tokens": int(meta.get("output_tokens") or 0),
    }
  token_usage = (getattr(response, "response_metadata", None) or {}).get("token_usage") or {}
  if isinstance(token_usage, dict) and token_usage:
    return {
      "input_tokens": int(token_usage.get("prompt_tokens") or 0),
      "output_tokens": int(token_usage.get("completion_tokens") or 0),
    }
  return {}
