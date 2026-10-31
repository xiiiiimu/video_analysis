from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any, TypeVar

# 链路上下文：一次 Agent 运行的 trace_id 就是 Java 派发时生成的 agentRunId，
# Java 派发请求头、本服务每行日志、回调 Java 的请求头（X-Trace-Id）都是同一个值，两边日志能串起来。
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")
job_id_var: ContextVar[str] = ContextVar("job_id", default="-")

logger = logging.getLogger("agent_service.trace")

T = TypeVar("T")


def new_trace_id() -> str:
  return uuid.uuid4().hex


def bind_trace_id(trace_id: str | None = None) -> str:
  value = trace_id or new_trace_id()
  trace_id_var.set(value)
  return value


def bind_trace_context(trace_id: str | None, job_id: str | None = None) -> str:
  """在当前线程 / 协程绑定 trace_id 和 job_id，返回实际使用的 trace_id。"""
  value = bind_trace_id(trace_id)
  if job_id:
    job_id_var.set(job_id)
  return value


def get_trace_id() -> str:
  return trace_id_var.get()


def run_with_trace(fn: Callable[[], T]) -> Callable[[], T]:
  """
  把当前的 trace_id / job_id 带进线程池。

  ContextVar 不会自动传进 ThreadPoolExecutor 的线程；这里只传这两个值，
  不整体 copy_context（避免把 harness scope 等其它上下文也带过去，改变原有行为）。
  """
  trace_id, job_id = trace_id_var.get(), job_id_var.get()

  def wrapped() -> T:
    trace_token = trace_id_var.set(trace_id)
    job_token = job_id_var.set(job_id)
    try:
      return fn()
    finally:
      # 线程池线程会复用：跑完恢复原值，避免下一个任务的日志带着上一个任务的 trace_id
      trace_id_var.reset(trace_token)
      job_id_var.reset(job_token)

  return wrapped


class TraceContextFilter(logging.Filter):
  """给每条日志补上 trace_id / job_id，格式里用 %(trace_id)s 输出；JSON 日志也会带上这两个字段。"""

  def filter(self, record: logging.LogRecord) -> bool:
    if not hasattr(record, "trace_id"):
      record.trace_id = trace_id_var.get()
    if not hasattr(record, "job_id"):
      record.job_id = job_id_var.get()
    return True


def log_event(event: str, **fields: Any) -> None:
  logger.info("trace_id=%s event=%s %s", get_trace_id(), event, fields)
