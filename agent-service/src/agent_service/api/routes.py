from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from agent_service.config import get_settings
from agent_service.observability.trace import bind_trace_context
from agent_service.services.job_queue import QueueFullError, get_dispatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


def require_internal_api_key(x_internal_api_key: str | None = Header(default=None)) -> None:
  """
  Java -> agent-service 的入站鉴权（与 Python -> Java 使用同一个请求头 X-Internal-Api-Key）。
  AGENT_SERVICE_API_KEY 为空时不校验，只用于本地开发。
  """
  expected = get_settings().agent_service_api_key
  if not expected:
    return
  if not x_internal_api_key or not hmac.compare_digest(x_internal_api_key, expected):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid internal api key")


class SubmitJobRequest(BaseModel):
  job_id: str = Field(..., description="Java 侧 AnalysisJob ID")
  agent_run_id: str | None = Field(default=None, description="Java 生成的本次 AgentRun ID")


class SubmitJobResponse(BaseModel):
  accepted: bool
  job_id: str
  agent_run_id: str | None = None
  duplicate: bool = False


@router.get("/health")
def health() -> dict[str, str]:
  return {"status": "ok"}


@router.post(
  "/jobs/submit",
  response_model=SubmitJobResponse,
  status_code=202,
  dependencies=[Depends(require_internal_api_key)],
)
def submit_job(
  request: SubmitJobRequest,
  x_trace_id: str | None = Header(default=None),
) -> SubmitJobResponse:
  """
  接收 Java 提交的 job_id，放进有界任务池异步执行，立即返回 202。
  同一个 job 正在执行时重复提交不会再跑一遍（duplicate=true，返回已有的 agent_run_id）。
  Java 派发时请求头 X-Trace-Id = agentRunId；任务线程里会用同一个值重新绑定（见 run_agent_job）。
  """
  bind_trace_context(x_trace_id or request.agent_run_id, request.job_id)
  logger.info("agent_job_submit job_id=%s agent_run_id=%s", request.job_id, request.agent_run_id)
  try:
    result = get_dispatcher().submit(request.job_id, request.agent_run_id)
  except QueueFullError as exc:
    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
  return SubmitJobResponse(
    accepted=True,
    job_id=request.job_id,
    agent_run_id=result.agent_run_id,
    duplicate=result.duplicate,
  )
