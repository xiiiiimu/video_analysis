"""
模型调用的传输层重试（参考 strands/event_loop/_retry.py 的 ModelRetryStrategy）。

- 只重试“值得重试”的错误：限流、超时、连接失败、5xx；其它异常立即抛出；
- 指数退避，用 ``ctx.cancel_signal.wait(delay)`` 等待：run 被取消时立刻醒来，不再重试；
- 尝试次数来自 ``event.attempt``，插件本身不保存状态，可被并行的 Specialist 安全共享；
- 想扩大/缩小可重试范围：继承并覆写 ``is_retryable``；
- 账户级错误（key 无效、余额不足 / 额度用完）重试也不会好：立即停止整个 run（stop_reason=model_fatal），
  否则每个专家都会"失败 → 弃权"，run 仍然显示成功，结果却是空的。

注意它和“语义重试”（输出不是合法 JSON）是两回事，后者由 OutputFormatGuard 负责。
"""

from __future__ import annotations

import logging

from agent_service.harness.errors import StopRun
from agent_service.harness.events import AfterModelCallEvent
from agent_service.harness.plugins.base import Plugin, hook

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}
_RETRYABLE_NAME_MARKERS = ("RateLimit", "Timeout", "APIConnection", "InternalServer", "ServiceUnavailable")
# 401 key 无效 / 402 余额不足（DeepSeek）；429 里只有"额度用完"是账户级的，普通限流仍然重试
_FATAL_STATUS = {401, 402}
_QUOTA_MARKERS = (
  "insufficient_quota",
  "no credits remaining",
  "exceeded your current quota",
  "insufficient balance",
  "insufficient_balance",
)


class ModelRetryPlugin(Plugin):
  name = "model-retry"

  def __init__(self, *, max_attempts: int = 3, initial_delay: float = 2.0, max_delay: float = 30.0) -> None:
    super().__init__()
    self.max_attempts = max_attempts
    self.initial_delay = initial_delay
    self.max_delay = max_delay

  def is_retryable(self, exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
      return True
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int) and status in _RETRYABLE_STATUS:
      return True
    name = type(exc).__name__
    return any(marker in name for marker in _RETRYABLE_NAME_MARKERS)

  def is_fatal(self, exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int) and status in _FATAL_STATUS:
      return True
    text = str(exc).lower()
    return any(marker in text for marker in _QUOTA_MARKERS)

  def delay_for(self, attempt: int) -> float:
    return min(self.initial_delay * (2 ** (attempt - 1)), self.max_delay)

  @hook
  def maybe_retry(self, event: AfterModelCallEvent) -> None:
    exc = event.exception
    if exc is not None and self.is_fatal(exc):
      logger.error("model_call_fatal agent_id=%s error=%s", event.agent_id, exc)
      message = f"模型服务账户不可用（key 无效或余额不足），已停止：{exc}"
      event.ctx.request_stop("model_fatal", message)
      raise StopRun("model_fatal", message)
    if exc is None or event.attempt >= self.max_attempts or not self.is_retryable(exc):
      return
    delay = self.delay_for(event.attempt)
    logger.warning(
      "model_call_retry agent_id=%s attempt=%s delay=%.1fs error=%s",
      event.agent_id,
      event.attempt,
      delay,
      exc,
    )
    if event.ctx.cancel_signal.wait(delay):
      return  # run 已被取消：不再重试，交给下一个检查点停止
    event.retry = True
