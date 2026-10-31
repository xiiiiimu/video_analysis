from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any

import httpx

from agent_service.config import get_settings
from agent_service.tools.adapters.errors import JavaBackendError
from agent_service.tools.adapters.java_result import unwrap_java_result

logger = logging.getLogger(__name__)

__all__ = ["CircuitBreaker", "JavaBackendError", "JavaBackendHttpClient", "reset_circuit_breakers", "shared_circuit_breaker"]


class CircuitBreaker:
  """
  进程级熔断器（线程安全）。

  改造前每个 job 都会 new 一个 JavaBackendHttpClient，熔断状态也随之重置，
  一个 job 里很难连续失败 5 次，熔断器实际上永远不会打开。现在按 base_url 共享。
  只有“Java 端不健康”的失败（网络错误、5xx）才计数；4xx 是请求本身的问题，不计入。
  """

  def __init__(self, failure_threshold: int = 5, recovery_seconds: int = 30) -> None:
    self.failure_threshold = failure_threshold
    self.recovery_seconds = recovery_seconds
    self._failure_count = 0
    self._opened_at: float | None = None
    self._lock = threading.Lock()

  def before_call(self) -> None:
    with self._lock:
      if self._opened_at is None:
        return
      if time.time() - self._opened_at >= self.recovery_seconds:
        self._failure_count = 0
        self._opened_at = None
        return
    raise JavaBackendError("Java backend circuit breaker is open")

  def on_success(self) -> None:
    with self._lock:
      self._failure_count = 0
      self._opened_at = None

  def on_failure(self) -> None:
    with self._lock:
      self._failure_count += 1
      if self._failure_count >= self.failure_threshold and self._opened_at is None:
        self._opened_at = time.time()
        logger.warning("Java backend circuit breaker opened failures=%s", self._failure_count)

  @property
  def is_open(self) -> bool:
    with self._lock:
      return self._opened_at is not None


_BREAKERS: dict[str, CircuitBreaker] = {}
_BREAKERS_LOCK = threading.Lock()


def shared_circuit_breaker(base_url: str) -> CircuitBreaker:
  with _BREAKERS_LOCK:
    breaker = _BREAKERS.get(base_url)
    if breaker is None:
      breaker = CircuitBreaker()
      _BREAKERS[base_url] = breaker
    return breaker


def reset_circuit_breakers() -> None:
  """测试用：清空进程级熔断状态。"""
  with _BREAKERS_LOCK:
    _BREAKERS.clear()


class JavaBackendHttpClient:
  """
  Java 内部接口 HTTP 客户端：重试 + 熔断 + Result 解包。

  重试规则：
  - GET（幂等）：网络错误、超时、5xx 都重试，指数退避；
  - POST（非幂等，如 save_diagnosis_hypothesis）：只在“请求确定没发出去”（连接失败）时重试。
    超时或 5xx 时请求可能已经被 Java 处理，重试会写入重复数据，所以直接失败；
  - 4xx：请求本身有问题，不重试，也不计入熔断。
  """

  def __init__(
    self,
    base_url: str | None = None,
    api_key: str | None = None,
    max_retries: int | None = None,
    retry_backoff_seconds: float | None = None,
    transport: httpx.BaseTransport | None = None,
    circuit_breaker: CircuitBreaker | None = None,
  ) -> None:
    settings = get_settings()
    self._base_url = (base_url or settings.java_backend_base_url).rstrip("/")
    self._api_key = api_key or settings.java_internal_api_key
    self._max_retries = max_retries or settings.java_http_max_retries
    self._retry_backoff_seconds = (
      settings.java_http_retry_backoff_seconds if retry_backoff_seconds is None else retry_backoff_seconds
    )
    self._timeout_seconds = settings.tool_timeout
    self._transport = transport
    self._circuit_breaker = circuit_breaker or shared_circuit_breaker(self._base_url)
    self._trace_id = uuid.uuid4().hex

  def set_trace_id(self, trace_id: str) -> None:
    self._trace_id = trace_id

  def _headers(self) -> dict[str, str]:
    return {
      "X-Internal-Api-Key": self._api_key,
      "X-Trace-Id": self._trace_id,
      "Content-Type": "application/json",
    }

  def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
    return self._request("GET", path, params=params)

  def post(self, path: str, body: dict[str, Any]) -> Any:
    return self._request("POST", path, json=body)

  def _should_retry(self, method: str, exc: Exception) -> bool:
    if isinstance(exc, JavaBackendError) and exc.status_code and 400 <= exc.status_code < 500:
      return False
    if method == "GET":
      return True
    # 非幂等请求：只有确定没发出去时才重试
    return isinstance(exc, httpx.ConnectError)

  def _request(
    self,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
  ) -> Any:
    self._circuit_breaker.before_call()
    last_error: Exception | None = None

    for attempt in range(1, self._max_retries + 1):
      try:
        with httpx.Client(timeout=self._timeout_seconds, transport=self._transport) as client:
          response = client.request(
            method,
            f"{self._base_url}{path}",
            headers=self._headers(),
            params=params,
            json=json,
          )
        if response.status_code >= 500:
          raise JavaBackendError(
            f"Java backend server error: {response.status_code}",
            status_code=response.status_code,
          )
        if response.status_code >= 400:
          raise JavaBackendError(
            f"Java backend client error: {response.status_code} {response.text}",
            status_code=response.status_code,
          )
        self._circuit_breaker.on_success()
        if not response.text:
          return {}
        return unwrap_java_result(response.json())
      except (httpx.HTTPError, JavaBackendError) as exc:
        last_error = exc
        logger.warning(
          "java_http_failed trace_id=%s method=%s path=%s attempt=%s error=%s",
          self._trace_id,
          method,
          path,
          attempt,
          exc,
        )
        is_client_error = isinstance(exc, JavaBackendError) and exc.status_code and 400 <= exc.status_code < 500
        if not self._should_retry(method, exc) or attempt >= self._max_retries:
          if not is_client_error:
            self._circuit_breaker.on_failure()
          if isinstance(exc, JavaBackendError):
            raise
          raise JavaBackendError(f"Java backend request failed after {attempt} attempt(s): {exc}") from exc
        time.sleep(self._retry_backoff_seconds * (2 ** (attempt - 1)))

    # 只有 max_retries <= 0 时才会走到这里
    raise JavaBackendError(f"Java backend request failed: {last_error}")
