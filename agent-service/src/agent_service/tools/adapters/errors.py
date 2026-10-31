from __future__ import annotations


class JavaBackendError(Exception):
  """Java 内部接口调用失败。单独成模块，避免 http_client ↔ java_result 循环导入。"""

  def __init__(self, message: str, status_code: int | None = None) -> None:
    super().__init__(message)
    self.status_code = status_code
