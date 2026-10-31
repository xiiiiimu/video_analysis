"""
插件机制（参考 strands/plugins/plugin.py、registry.py、_discovery.py）。

一个插件 = 一个唯一的 ``name`` + 一组用 ``@hook`` 标记的方法。
- 构造时沿 MRO 扫描 ``@hook`` 方法（父类先、子类覆写只算一次）；
- 事件类型从参数的类型注解推断，支持 ``A | B`` 联合类型；
- 运行期状态放在 ``event.ctx.plugin_state``，不要放在 ``self`` 上
  （3 个 Specialist 并行共享同一个插件实例）。
"""

from __future__ import annotations

import inspect
import types
import typing
from collections.abc import Callable
from typing import Any

from agent_service.harness.events import HarnessEvent
from agent_service.harness.hooks import HookOrder, HookRegistry

_HOOK_ORDER_ATTR = "_harness_hook_order"


def hook(fn: Callable[..., Any] | None = None, *, order: float = HookOrder.DEFAULT) -> Any:
  """把插件方法标记为 hook 回调。可写 ``@hook`` 或 ``@hook(order=...)``。"""

  def mark(func: Callable[..., Any]) -> Callable[..., Any]:
    setattr(func, _HOOK_ORDER_ATTR, order)
    return func

  return mark(fn) if fn is not None else mark


def _infer_event_types(method: Callable[..., Any]) -> tuple[type[HarnessEvent], ...]:
  hints = typing.get_type_hints(method)
  params = [name for name in inspect.signature(method).parameters if name != "self"]
  if not params or params[0] not in hints:
    raise TypeError(f"@hook method {method.__qualname__} needs a type-annotated event parameter")
  annotation = hints[params[0]]
  if isinstance(annotation, types.UnionType) or typing.get_origin(annotation) is typing.Union:
    candidates = typing.get_args(annotation)
  else:
    candidates = (annotation,)
  event_types = tuple(item for item in candidates if isinstance(item, type) and issubclass(item, HarnessEvent))
  if len(event_types) != len(candidates):
    raise TypeError(f"@hook method {method.__qualname__} must annotate HarnessEvent subclasses only")
  return event_types


class Plugin:
  name: str = ""

  def __init__(self) -> None:
    if not self.name:
      raise TypeError(f"{type(self).__name__} must define a non-empty `name`")
    self._hooks = self._discover_hooks()

  def _discover_hooks(self) -> list[tuple[tuple[type[HarnessEvent], ...], Callable[..., Any], float]]:
    found: list[tuple[tuple[type[HarnessEvent], ...], Callable[..., Any], float]] = []
    seen: set[str] = set()
    for cls in reversed(type(self).__mro__):
      for attr_name, raw in cls.__dict__.items():
        if attr_name in seen:
          continue
        if not callable(raw) or not hasattr(raw, _HOOK_ORDER_ATTR):
          continue
        seen.add(attr_name)
        bound = getattr(self, attr_name)
        found.append((_infer_event_types(raw), bound, getattr(raw, _HOOK_ORDER_ATTR)))
    return found

  def register_hooks(self, registry: HookRegistry) -> None:
    """默认注册所有 ``@hook`` 方法；需要按条件注册时可以覆写。"""
    for event_types, callback, order in self._hooks:
      registry.add_callback(event_types, callback, order=order)


class PluginRegistry:
  def __init__(self, hook_registry: HookRegistry) -> None:
    self._hooks = hook_registry
    self._plugins: dict[str, Plugin] = {}

  def add(self, plugin: Plugin) -> None:
    if plugin.name in self._plugins:
      raise ValueError(f"plugin already registered: {plugin.name}")
    self._plugins[plugin.name] = plugin
    plugin.register_hooks(self._hooks)

  @property
  def plugins(self) -> list[Plugin]:
    return list(self._plugins.values())

  def get(self, name: str) -> Plugin | None:
    return self._plugins.get(name)
