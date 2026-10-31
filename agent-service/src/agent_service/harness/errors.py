from __future__ import annotations


class StopRun(BaseException):
  """
  请求结束整个 run（超时取消、超出预算）。

  继承 ``BaseException`` 而不是 ``Exception``：业务代码里大量 ``except Exception``
  （工具边界、进度上报、trace_step），如果它是普通异常就会被吞掉，run 停不下来。
  Strands 文档对 InterruptException 也提醒过同样的问题。
  """

  def __init__(self, stop_reason: str, message: str = "") -> None:
    super().__init__(message or stop_reason)
    self.stop_reason = stop_reason


class ToolCallCancelled(Exception):
  """工具调用被 hook / intervention 取消。消息会作为错误结果交给调用方（ReAct 循环）。"""


class ModelCallCancelled(Exception):
  """模型调用被 hook / intervention 取消。"""


class UnknownToolError(Exception):
  """调用了注册表中不存在的工具：属于配置/代码错误，不交给模型处理。"""
