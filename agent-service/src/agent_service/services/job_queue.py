"""
任务调度：进程内有界并发 + 按 job_id 去重。

改造前用 FastAPI BackgroundTasks：没有并发上限（50 个请求就是 50 个线程同时调 LLM），
Java 重复提交同一个 job 会跑两遍。现在：
- 最多 ``MAX_CONCURRENT_JOBS`` 个任务同时执行，超出的排队；排队数超过上限时拒绝（HTTP 429）；
- 同一个 job_id 正在执行或排队时，重复提交直接返回已有的 agent_run_id（参考 Strands 的 idempotency_token）。

仍然是进程内队列：进程重启时排队/执行中的任务会丢失，由 Java 端的 RUNNING 超时兜底。
需要跨进程持久化时，可以把 ``submit`` 换成 Redis Stream / 消息队列，接口不变。
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QueueFullError(RuntimeError):
  pass


@dataclass(frozen=True)
class SubmitResult:
  job_id: str
  agent_run_id: str | None
  duplicate: bool


class JobDispatcher:
  def __init__(
    self,
    runner: Callable[[str, str | None], None],
    *,
    max_workers: int = 4,
    max_pending: int = 100,
  ) -> None:
    self._runner = runner
    self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers), thread_name_prefix="agent-job")
    self._max_pending = max_pending
    self._in_flight: dict[str, tuple[str | None, Future[None]]] = {}
    self._lock = threading.Lock()

  def submit(self, job_id: str, agent_run_id: str | None = None) -> SubmitResult:
    with self._lock:
      existing = self._in_flight.get(job_id)
      if existing is not None:
        logger.info("agent_job_duplicate job_id=%s agent_run_id=%s", job_id, existing[0])
        return SubmitResult(job_id=job_id, agent_run_id=existing[0], duplicate=True)
      if len(self._in_flight) >= self._max_pending:
        raise QueueFullError(f"Too many pending agent jobs: {len(self._in_flight)}")
      future = self._executor.submit(self._run, job_id, agent_run_id)
      self._in_flight[job_id] = (agent_run_id, future)
      return SubmitResult(job_id=job_id, agent_run_id=agent_run_id, duplicate=False)

  def _run(self, job_id: str, agent_run_id: str | None) -> None:
    try:
      self._runner(job_id, agent_run_id)
    except Exception:  # run_agent_job 自己会回调失败；这里只防止线程里的异常被静默吞掉
      logger.exception("agent_job_unhandled job_id=%s", job_id)
    finally:
      with self._lock:
        self._in_flight.pop(job_id, None)

  @property
  def in_flight(self) -> int:
    with self._lock:
      return len(self._in_flight)

  def shutdown(self, wait: bool = False) -> None:
    pending = self.in_flight
    if pending:
      logger.warning("agent_job_dispatcher_shutdown pending=%s (Java RUNNING timeout will recover them)", pending)
    self._executor.shutdown(wait=wait, cancel_futures=not wait)


_dispatcher: JobDispatcher | None = None
_dispatcher_lock = threading.Lock()


def get_dispatcher() -> JobDispatcher:
  global _dispatcher
  with _dispatcher_lock:
    if _dispatcher is None:
      from agent_service.config import get_settings
      from agent_service.services.job_runner import run_agent_job

      _dispatcher = JobDispatcher(run_agent_job, max_workers=get_settings().max_concurrent_jobs)
    return _dispatcher
