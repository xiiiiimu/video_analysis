from __future__ import annotations

from collections.abc import Callable
from typing import Any

ToolFn = Callable[..., Any]


class BaseTool:
  name: str
  description: str

  def __call__(self, **kwargs: Any) -> Any:
    raise NotImplementedError
