"""
极简 main.py 入口：HTTP 服务或 Harness 演示模式。

运行方式：
  python -m agent_service.main

HTTP 模式（默认）：
  POST http://localhost:8090/api/v1/agent/jobs/submit

演示模式：
  RUN_HARNESS_DEMO=1 python -m agent_service.main
"""

from __future__ import annotations

import logging
import os
from typing import Any

from agent_service.config import get_settings
from agent_service.observability.logging_setup import configure_logging

logger = logging.getLogger(__name__)


def run_harness_demo() -> None:
  from agent_service.services.harness_setup import create_diagnosis_harness
  from agent_service.tools.registry import build_tool_registry

  harness = create_diagnosis_harness(build_tool_registry())

  demo_payload: dict[str, Any] = {
    "job_id": "demo-job-id",
    "user_intent": "diagnose_video_gap",
  }
  result = harness.run(task_id=demo_payload["job_id"], input_payload=demo_payload)
  logger.info(
    "Harness finished: status=%s stop_reason=%s turns=%s usage=%s",
    result.status,
    result.stop_reason,
    result.turns,
    result.usage,
  )


def create_app():
  from contextlib import asynccontextmanager

  from fastapi import FastAPI

  from agent_service.api.routes import router
  from agent_service.services.job_queue import get_dispatcher

  settings = get_settings()
  if not settings.chat_api_key and not settings.llm_mock:
    logger.error("No LLM API key configured and LLM_MOCK is off: every diagnosis job will fail fast.")
  # 启动时就校验评分点 md：格式写错直接启动失败并指出文件和行号，而不是等到任务里才发现
  from agent_service.knowledge import diagnosis_rubric_corpus

  logger.info("rubric_loaded items=%s", len(diagnosis_rubric_corpus()))
  if not settings.agent_service_api_key:
    logger.warning("AGENT_SERVICE_API_KEY is empty: /jobs/submit accepts unauthenticated requests (local dev only).")

  @asynccontextmanager
  async def lifespan(_app: FastAPI):
    yield
    get_dispatcher().shutdown(wait=False)

  app = FastAPI(title="Video Diagnosis Agent Service", version="0.2.0", lifespan=lifespan)
  app.include_router(router)
  return app


def main() -> None:
  configure_logging()

  if os.getenv("RUN_HARNESS_DEMO") == "1":
    run_harness_demo()
    return

  import uvicorn

  settings = get_settings()
  uvicorn.run(create_app(), host=settings.agent_service_host, port=settings.agent_service_port)


if __name__ == "__main__":
  main()
