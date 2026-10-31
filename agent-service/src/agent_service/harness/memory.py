from __future__ import annotations

from typing import Any


class MemoryManager:
  """
  Harness 记忆管理（会话级 / 任务级草稿，非权威业务数据）。

  权威业务数据一律通过 tools adapter 读写 Java MySQL。
  """

  def __init__(self) -> None:
    self._scratchpad: dict[str, list[dict[str, Any]]] = {}

  def append(self, task_id: str, message: dict[str, Any]) -> None:
    self._scratchpad.setdefault(task_id, []).append(message)

  def get(self, task_id: str) -> list[dict[str, Any]]:
    return list(self._scratchpad.get(task_id, []))

  def clear(self, task_id: str) -> None:
    self._scratchpad.pop(task_id, None)
