from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

RunStatus = Literal["success", "failed", "timeout", "guardrail_blocked"]
"""对外（Java 回调 / eval）兼容的粗粒度状态。"""

StopReason = Literal[
  "completed",
  "cancelled",
  "limit_turns",
  "limit_tokens",
  "limit_steps",
  "error",
]
"""细粒度停止原因，参考 Strands 的 stop_reason：说明 run 为什么结束。"""

_STATUS_BY_STOP_REASON: dict[str, RunStatus] = {
  "completed": "success",
  "cancelled": "timeout",
  "limit_turns": "guardrail_blocked",
  "limit_tokens": "guardrail_blocked",
  "limit_steps": "guardrail_blocked",
  "error": "failed",
  "model_fatal": "failed",
}


def status_for(stop_reason: str) -> RunStatus:
  return _STATUS_BY_STOP_REASON.get(stop_reason, "failed")


@dataclass
class HarnessRunResult:
  task_id: str
  status: RunStatus
  turns: int
  output: dict[str, Any]
  audit_events: list[dict[str, Any]] = field(default_factory=list)
  error: str | None = None
  stop_reason: str = "completed"
  usage: dict[str, int] = field(default_factory=dict)


@dataclass
class HarnessLimits:
  max_turns: int = 20
  max_tokens: int = 32000
  max_graph_steps: int = 25
  timeout_seconds: int = 300


@dataclass
class HarnessContext:
  """
  一次 run 的 invocation state（对应 Strands 的 invocation_state）。

  - 不进入 LangGraph state，不发给模型，可以放不可序列化对象。
  - 3 个 Specialist 并行共享同一个 ctx，所以所有计数/状态写入都必须走带锁的方法。
  - 插件的运行期状态放在 ``plugin_state`` 里（按 key 区分，如 ``json_retry:hook_agent``），
    不要放在插件实例的 ``self`` 上。
  """

  task_id: str
  trace_id: str = ""
  job_id: str | None = None
  started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
  turns: int = 0
  graph_steps: int = 0
  model_calls: int = 0
  input_tokens: int = 0
  output_tokens: int = 0
  token_usage: int = 0
  stop_reason: str | None = None
  stop_detail: str | None = None  # 第一个停止原因的具体说明（例如模型账户错误原文），作为 run 的 error 返回
  audit_events: list[dict[str, Any]] = field(default_factory=list)
  plugin_state: dict[str, Any] = field(default_factory=dict)
  cancel_signal: threading.Event = field(default_factory=threading.Event, repr=False)
  _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

  def incr(self, counter: str, amount: int = 1) -> int:
    """线程安全地累加一个计数字段，返回累加后的值。"""
    with self._lock:
      value = int(getattr(self, counter)) + amount
      setattr(self, counter, value)
      return value

  def add_usage(self, input_tokens: int, output_tokens: int) -> None:
    with self._lock:
      self.input_tokens += input_tokens
      self.output_tokens += output_tokens
      self.token_usage += input_tokens + output_tokens

  def state_incr(self, key: str, amount: int = 1) -> int:
    """插件状态计数（例如某个 agent 的 JSON 重试次数）。"""
    with self._lock:
      value = int(self.plugin_state.get(key, 0)) + amount
      self.plugin_state[key] = value
      return value

  def record(self, event: str, **payload: Any) -> None:
    with self._lock:
      self.audit_events.append(
        {
          "event": event,
          "at": datetime.now(UTC).isoformat(),
          **payload,
        }
      )

  def request_stop(self, reason: str, detail: str | None = None) -> None:
    """请求停止整个 run：记录第一个停止原因，并设置取消信号让其它并行分支在检查点退出。"""
    with self._lock:
      if self.stop_reason is None:
        self.stop_reason = reason
        self.stop_detail = detail
    self.cancel_signal.set()

  @property
  def cancelled(self) -> bool:
    return self.cancel_signal.is_set()

  def usage(self) -> dict[str, int]:
    with self._lock:
      return {
        "modelCalls": self.model_calls,
        "inputTokens": self.input_tokens,
        "outputTokens": self.output_tokens,
        "totalTokens": self.token_usage,
      }
