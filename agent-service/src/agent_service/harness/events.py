"""
Harness 生命周期事件（参考 strands/hooks/events.py）。

设计要点：
- 每个事件携带本阶段的数据，大部分字段只读；
- 只有 ``_writable`` 里列出的字段允许 hook 修改，它们就是 hook 影响执行的“控制杆”；
- After 类事件 ``reverse_callbacks = True``：回调按注册顺序反向执行（洋葱模型）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from agent_service.harness.types import HarnessContext, HarnessRunResult


class HarnessEvent:
  _writable: ClassVar[frozenset[str]] = frozenset()
  reverse_callbacks: ClassVar[bool] = False

  def __post_init__(self) -> None:
    object.__setattr__(self, "_initialized", True)

  def __setattr__(self, name: str, value: Any) -> None:
    if getattr(self, "_initialized", False) and name not in self._writable:
      raise AttributeError(f"{type(self).__name__}.{name} is read-only")
    object.__setattr__(self, name, value)


# ---------------------------------------------------------------- run 级


@dataclass
class BeforeRunEvent(HarnessEvent):
  ctx: HarnessContext
  input_payload: dict[str, Any]


@dataclass
class AfterRunEvent(HarnessEvent):
  ctx: HarnessContext
  result: HarnessRunResult
  reverse_callbacks: ClassVar[bool] = True


# ---------------------------------------------------------------- node 级（LangGraph 节点）


@dataclass
class BeforeNodeEvent(HarnessEvent):
  ctx: HarnessContext
  node: str


@dataclass
class AfterNodeEvent(HarnessEvent):
  ctx: HarnessContext
  node: str
  update: dict[str, Any] | None = None
  exception: BaseException | None = None
  reverse_callbacks: ClassVar[bool] = True


# ---------------------------------------------------------------- tool 级


@dataclass
class BeforeToolCallEvent(HarnessEvent):
  """
  可写：
  - ``cancel_tool``：设为字符串则取消本次调用，调用方收到 ``ToolCallCancelled(消息)``；
  - ``tool_args``：dict，可原地修改参数（例如固定 job_id）。
  """

  ctx: HarnessContext
  tool_name: str
  tool_args: dict[str, Any]
  agent_id: str | None = None
  cancel_tool: str | None = None
  _writable: ClassVar[frozenset[str]] = frozenset({"cancel_tool", "tool_args"})


@dataclass
class AfterToolCallEvent(HarnessEvent):
  """
  可写：
  - ``result``：改写工具结果；
  - ``retry``：设为 True 则丢弃本次结果并重新执行工具。
  ``exception`` 只读：工具抛出的原始异常（没有则为 None）。
  """

  ctx: HarnessContext
  tool_name: str
  tool_args: dict[str, Any]
  agent_id: str | None = None
  attempt: int = 1
  result: Any = None
  exception: BaseException | None = None
  retry: bool = False
  _writable: ClassVar[frozenset[str]] = frozenset({"result", "retry"})
  reverse_callbacks: ClassVar[bool] = True


# ---------------------------------------------------------------- model 级


@dataclass
class BeforeModelCallEvent(HarnessEvent):
  """
  可写：
  - ``cancel``：设为字符串则取消本次模型调用；
  - ``messages``：本次要发给模型的消息（可原地追加引导信息）。
  """

  ctx: HarnessContext
  messages: list[dict[str, Any]]
  agent_id: str | None = None
  attempt: int = 1
  cancel: str | None = None
  _writable: ClassVar[frozenset[str]] = frozenset({"cancel", "messages"})


@dataclass
class AfterModelCallEvent(HarnessEvent):
  """
  可写：
  - ``retry``：设为 True 则丢弃本次回复重新调用模型（下一次使用 ``messages``）；
  - ``messages``：重试时要发送的消息（Guide 会在这里追加反馈）。
  只读：
  - ``exception``：调用模型本身抛出的异常（网络、限流等）；
  - ``parse_error``：模型返回了，但结果解析失败（例如不是合法 JSON）；
  - ``usage``：本次调用的 token 用量。
  """

  ctx: HarnessContext
  messages: list[dict[str, Any]]
  agent_id: str | None = None
  attempt: int = 1
  response: Any = None
  parsed: Any = None
  usage: dict[str, int] = field(default_factory=dict)
  exception: BaseException | None = None
  parse_error: BaseException | None = None
  retry: bool = False
  _writable: ClassVar[frozenset[str]] = frozenset({"retry", "messages"})
  reverse_callbacks: ClassVar[bool] = True


# ---------------------------------------------------------------- 基础设施调用（非工具）


@dataclass
class InfraCallEvent(HarnessEvent):
  """
  进度上报、结果回写这类“流程副作用”：模型不会主动选择它们，
  所以不走 call_tool、不计入轮次预算，只发一个事件供审计。
  """

  ctx: HarnessContext
  name: str
  args: dict[str, Any]
  exception: BaseException | None = None
