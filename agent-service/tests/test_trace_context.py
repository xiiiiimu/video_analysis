"""链路追踪：日志带 trace_id / job_id（= Java 的 agentRunId / jobId），并且能带进专家并行的线程池。"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from agent_service.observability.trace import (
  TraceContextFilter,
  bind_trace_context,
  job_id_var,
  run_with_trace,
  trace_id_var,
)


def _record() -> logging.LogRecord:
  return logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)


def test_filter_adds_trace_and_job_ids() -> None:
  def inside_thread() -> logging.LogRecord:
    bind_trace_context("run-123", "job-9")
    record = _record()
    TraceContextFilter().filter(record)
    return record

  # 在独立线程里绑定，避免污染其它用例的上下文
  with ThreadPoolExecutor(max_workers=1) as executor:
    record = executor.submit(inside_thread).result()
  assert (record.trace_id, record.job_id) == ("run-123", "job-9")
  line = logging.Formatter("[trace=%(trace_id)s job=%(job_id)s] %(message)s").format(record)
  assert line == "[trace=run-123 job=job-9] msg"


def test_filter_keeps_explicit_values_and_defaults_outside_a_run() -> None:
  record = _record()
  record.trace_id = "explicit"
  TraceContextFilter().filter(record)
  assert record.trace_id == "explicit"

  fresh = _record()
  with ThreadPoolExecutor(max_workers=1) as executor:
    executor.submit(TraceContextFilter().filter, fresh).result()
  assert (fresh.trace_id, fresh.job_id) == ("-", "-")


def test_run_with_trace_propagates_into_worker_threads() -> None:
  seen: list[tuple[str, str, str]] = []

  def specialist() -> None:
    seen.append((trace_id_var.get(), job_id_var.get(), threading.current_thread().name))

  def agent_job() -> None:
    bind_trace_context("run-abc", "job-1")
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="specialist") as pool:
      for future in [pool.submit(run_with_trace(specialist)) for _ in range(3)]:
        future.result()
      # 不包装时 ContextVar 不会传进线程池（这正是要修的问题）
      assert pool.submit(lambda: trace_id_var.get()).result() == "-"

  with ThreadPoolExecutor(max_workers=1, thread_name_prefix="agent-job") as outer:
    outer.submit(agent_job).result()

  assert len(seen) == 3
  assert {(trace, job) for trace, job, _ in seen} == {("run-abc", "job-1")}
  assert all(name.startswith("specialist") for _, _, name in seen)
