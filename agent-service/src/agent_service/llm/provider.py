from __future__ import annotations

from langchain_openai import ChatOpenAI

from agent_service.config import get_settings


def get_chat_model() -> ChatOpenAI:
  settings = get_settings()
  return ChatOpenAI(
    api_key=settings.chat_api_key or "missing-key",
    model=settings.chat_model,
    base_url=settings.chat_base_url or None,
    temperature=0.2,
    # harness 的超时是“在检查点停下”，打断不了卡住的 HTTP 请求，所以单次请求必须有自己的超时
    timeout=settings.llm_timeout_seconds,
    # 重试统一交给 harness 的 ModelRetryPlugin（有审计、会响应取消），避免两层重试叠加
    max_retries=0,
  )
