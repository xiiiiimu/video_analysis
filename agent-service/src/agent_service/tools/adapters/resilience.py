from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
  failure_count: int = 0
  opened_at: float | None = None


class CircuitBreakerOpenError(Exception):
  pass


class ResilientHttpExecutor:
  """简单重试 + 熔断，防止 Java 接口抖动导致 LangGraph 整体崩溃。"""

  def __init__(
    self,
    max_retries: int = 3,
    retry_backoff_seconds: float = 0.5,
    failure_threshold: int = 5,
    recovery_seconds: float = 30.0,
  ) -> None:
    self._max_retries = max_retries
    self._retry_backoff_seconds = retry_backoff_seconds
    self._failure_threshold = failure_threshold
    self._recovery_seconds = recovery_seconds
    self._state = CircuitBreakerState()

  def call(self, operation: str, fn: Any) -> Any:
    self._ensure_closed()
    last_error: Exception | None = None
    for attempt in range(1, self._max_retries + 1):
      try:
        result = fn()
        self._on_success()
        return result
      except Exception as exc:  # noqa: BLE001
        last_error = exc
        logger.warning("HTTP op=%s attempt=%s failed: %s", operation, attempt, exc)
        if attempt < self._max_retries:
          time.sleep(self._retry_backoff_seconds * attempt)
    self._on_failure()
    raise RuntimeError(f"{operation} failed after {self._max_retries} retries") from last_error

  def _ensure_closed(self) -> None:
    if self._state.opened_at is None:
      return
    elapsed = time.time() - self._state.opened_at
    if elapsed >= self._recovery_seconds:
      logger.info("Circuit breaker half-open, resetting failure count")
      self._state = CircuitBreakerState()
      return
    raise CircuitBreakerOpenError("Circuit breaker is open")

  def _on_success(self) -> None:
    self._state.failure_count = 0
    self._state.opened_at = None

  def _on_failure(self) -> None:
    self._state.failure_count += 1
    if self._state.failure_count >= self._failure_threshold:
      self._state.opened_at = time.time()
      logger.error("Circuit breaker opened after %s failures", self._state.failure_count)
