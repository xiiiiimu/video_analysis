"""
Hook 注册表（参考 strands/hooks/registry.py）。

- 回调按 ``order`` 升序执行，数值越小越先执行；同 order 保持注册顺序；
- After 类事件（``reverse_callbacks``）整体反向执行，形成洋葱模型：
  最先看到 Before 的 hook（如审计），最后看到 After，能看到其它 hook 修改后的最终结果；
- 回调里抛出的异常直接向上传播（hook 自身出错属于程序错误，不吞掉）。
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from agent_service.harness.events import HarnessEvent

TEvent = TypeVar("TEvent", bound=HarnessEvent)
HookCallback = Callable[[Any], None]


class HookOrder:
  FIRST = -100  # 审计：最先看到 Before，最后看到 After
  LIMITS = -95  # 预算/取消检查
  INTERVENTION_OUTPUT = -90  # After 类事件上的 intervention
  DEFAULT = 0
  INTERVENTION_INPUT = 90  # Before 类事件上的 intervention
  LAST = 100


@dataclass
class _Entry:
  callback: HookCallback
  order: float
  seq: int


class HookRegistry:
  def __init__(self) -> None:
    self._entries: dict[type[HarnessEvent], list[_Entry]] = {}
    self._seq = 0
    self._lock = threading.Lock()

  def add_callback(
    self,
    event_types: type[HarnessEvent] | tuple[type[HarnessEvent], ...] | list[type[HarnessEvent]],
    callback: HookCallback,
    order: float = HookOrder.DEFAULT,
  ) -> None:
    types = event_types if isinstance(event_types, (tuple, list)) else (event_types,)
    with self._lock:
      for event_type in types:
        self._seq += 1
        entries = self._entries.setdefault(event_type, [])
        entries.append(_Entry(callback=callback, order=order, seq=self._seq))
        entries.sort(key=lambda item: (item.order, item.seq))

  def callbacks_for(self, event: HarnessEvent) -> list[HookCallback]:
    entries = list(self._entries.get(type(event), []))
    callbacks = [entry.callback for entry in entries]
    return list(reversed(callbacks)) if event.reverse_callbacks else callbacks

  def emit(self, event: TEvent) -> TEvent:
    for callback in self.callbacks_for(event):
      callback(event)
    return event

  def has_callbacks(self, event_type: type[HarnessEvent]) -> bool:
    return bool(self._entries.get(event_type))
