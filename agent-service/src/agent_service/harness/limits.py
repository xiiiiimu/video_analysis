from __future__ import annotations

import concurrent.futures
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def time_limit(seconds: int) -> Iterator[None]:
  """跨平台超时熔断（Docker/Linux 与 Windows 本地开发均可用）。"""
  if seconds <= 0:
    yield
    return

  with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(lambda: None)
    try:
      yield
    finally:
      try:
        future.result(timeout=seconds)
      except concurrent.futures.TimeoutError as exc:
        raise TimeoutError(f"Harness timeout after {seconds}s") from exc
