"""
LangGraph 适配：把普通节点函数包成“会发 Node 事件”的节点。

改造前每个 node 都要手动调用 ``harness.on_graph_step(ctx)``，漏一次计数就不准；
现在在 builder 里统一包装，业务 node 不需要知道 harness 的存在。

注意：不能用 ``functools.wraps``。LangGraph 会通过 ``inspect.signature`` 看节点的
``config`` 参数类型来决定要不要传 config，``wraps`` 会让它看到原函数的签名。
包装函数自己声明 ``config: RunnableConfig``，保证 config 一定被传进来。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig

NodeFn = Callable[[Any, Any], dict[str, Any]]


def harness_node(name: str, fn: NodeFn) -> Callable[[Any, RunnableConfig], dict[str, Any]]:
  def wrapped(state: Any, config: RunnableConfig) -> dict[str, Any]:
    configurable = (config or {}).get("configurable") or {}
    harness = configurable.get("harness")
    run_node = getattr(harness, "run_node", None)
    if run_node is None:  # 单元测试里用假的 harness 直接调用节点时，保持原样
      return fn(state, config)
    return run_node(configurable.get("harness_ctx"), name, fn, state, config)

  wrapped.__name__ = getattr(fn, "__name__", name)
  wrapped.__qualname__ = getattr(fn, "__qualname__", name)
  wrapped.__doc__ = fn.__doc__
  return wrapped
