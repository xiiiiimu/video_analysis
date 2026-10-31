from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")

logger = logging.getLogger("agent_service.trace")


def new_trace_id() -> str:
  return uuid.uuid4().hex


def bind_trace(trace_id: str | None = None) -> str:
  value = trace_id or new_trace_id()
  trace_id_var.set(value)
  return value


def get_trace_id() -> str:
  return trace_id_var.get()


def log_event(event: str, **fields: Any) -> None:
  payload = {"trace_id": get_trace_id(), "event": event, **fields}
  logger.info("%s", payload)


class CircuitBreakerOpen(Exception):
  pass


class CircuitBreaker:
  def __init__(self, failure_threshold: int = 5, recovery_seconds: int = 30) -> None:
    self._failure_threshold = failure_threshold
    self._recovery_seconds = recovery_seconds
    self._failures = 0
    self._opened_at: float | None = None

  def before_call(self) -> None:
    if self._opened_at is None:
      return
    if time.time() - self._opened_at >= self._recovery_seconds:
      self._opened_at = None
      self._failures = 0
      return
    raise CircuitBreakerOpen("Java backend circuit breaker is open")

  def on_success(self) -> None:
    self._failures = 0
    self._opened_at = None

  def on_failure(self) -> None:
    self._failures += 1
    if self._failures >= self._failure_threshold:
      self._opened_at = time.time()
      log_event("circuit_breaker_open", failures=self._failures)
