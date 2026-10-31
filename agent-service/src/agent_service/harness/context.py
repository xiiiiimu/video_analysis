"""
运行作用域：让深层业务代码（例如 LLM 调用）不需要层层传参也能找到当前 harness。

ReAct 循环在自己的线程里用 ``harness_scope(...)`` 绑定 harness、ctx 和 agent_id；
之后在这个线程里发生的模型调用和工具调用，都能知道“是哪个 Specialist 发起的”。
ContextVar 不会自动传进线程池，所以必须在线程内部绑定（DiagnosisReActLoop.run 里做）。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HarnessScope:
  harness: Any
  ctx: Any
  agent_id: str | None = None


_CURRENT: ContextVar[HarnessScope | None] = ContextVar("agent_service_harness_scope", default=None)


@contextmanager
def harness_scope(harness: Any, ctx: Any, agent_id: str | None = None) -> Iterator[HarnessScope]:
  scope = HarnessScope(harness=harness, ctx=ctx, agent_id=agent_id)
  token = _CURRENT.set(scope)
  try:
    yield scope
  finally:
    _CURRENT.reset(token)


def current_scope() -> HarnessScope | None:
  return _CURRENT.get()


def current_agent_id() -> str | None:
  scope = _CURRENT.get()
  return scope.agent_id if scope else None


def call_model(
  invoke: Callable[[list[dict[str, Any]]], Any],
  messages: list[dict[str, Any]],
  *,
  parse: Callable[[Any], Any] | None = None,
) -> tuple[Any, Any]:
  """
  业务代码调用模型的唯一入口。

  有 harness 作用域时走 ``harness.call_model``（发事件、计 token、重试、限额）；
  没有时（单元测试、离线脚本）直接调用，行为与改造前一致。
  返回 ``(response, parsed)``。
  """
  scope = _CURRENT.get()
  if scope is not None and hasattr(scope.harness, "call_model"):
    return scope.harness.call_model(scope.ctx, invoke, messages, parse=parse, agent_id=scope.agent_id)
  response = invoke(messages)
  return response, (parse(response) if parse else None)
