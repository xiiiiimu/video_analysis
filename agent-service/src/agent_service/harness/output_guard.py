"""
语义重试：模型返回了，但输出解析失败（例如不是合法 JSON）时，带着反馈让模型重来。

这是一个 intervention handler（返回 Guide），而不是直接写 ``event.retry``：
多个 handler 同时给反馈时会被合并成一条，不会互相覆盖。
收敛：超过 ``max_retries`` 次后返回 Proceed，让解析错误按原样抛给调用方。
"""

from __future__ import annotations

from agent_service.harness.events import AfterModelCallEvent
from agent_service.harness.interventions import (
  Guide,
  InterventionAction,
  InterventionHandler,
  Proceed,
)

DEFAULT_FEEDBACK = (
  "上一次输出无法解析：{error}。"
  "请只输出一个 JSON 对象，不要包含解释文字，也不要使用 Markdown 代码块。"
)


class OutputFormatGuard(InterventionHandler):
  name = "output-format-guard"

  def __init__(self, max_retries: int = 2, feedback_template: str = DEFAULT_FEEDBACK) -> None:
    self.max_retries = max_retries
    self.feedback_template = feedback_template

  def after_model_call(self, event: AfterModelCallEvent) -> InterventionAction:
    if event.parse_error is None or event.exception is not None:
      return Proceed()
    if event.attempt > self.max_retries:
      return Proceed(reason="output format retries exhausted")
    return Guide(feedback=self.feedback_template.format(error=str(event.parse_error)[:200]))
