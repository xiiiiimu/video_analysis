from __future__ import annotations

import logging
import uuid

from agent_service.config import get_settings
from agent_service.graph.runtime import build_lightweight_trace
from agent_service.harness import HarnessRunResult
from agent_service.observability.logging_setup import configure_logging
from agent_service.observability.trace import bind_trace_context
from agent_service.services.harness_setup import create_diagnosis_harness
from agent_service.tools.adapters.analysis_job import AnalysisJobToolAdapter
from agent_service.tools.adapters.http_client import JavaBackendHttpClient
from agent_service.tools.registry import build_tool_registry

logger = logging.getLogger(__name__)


def classify_outcome(result: HarnessRunResult) -> str:
  """
  把 stop_reason 归并成 Java 回调能表达的结果（参考 Strands lifecycle-controls 的 classify）。

  目前 Java 回调契约只有 SUCCESS / FAILED 两种；预算用完、超时都按 FAILED 回调，
  但错误信息里带上 stop_reason，并且回调里附带已经产生的 agent_trace，便于排查。
  """
  if result.stop_reason == "completed" and result.output.get("status") != "FAILED":
    return "SUCCESS"
  return "FAILED"


def run_agent_job(job_id: str, agent_run_id: str | None = None) -> None:
  configure_logging()
  trace_id = agent_run_id or uuid.uuid4().hex
  # 任务在线程池里执行，请求线程绑定的上下文带不过来，这里重新绑定：之后本次运行的每行日志都带 trace_id / job_id
  bind_trace_context(trace_id, job_id)
  logger.info("agent_job_started job_id=%s trace_id=%s", job_id, trace_id)

  http_client = JavaBackendHttpClient()
  http_client.set_trace_id(trace_id)
  tools = build_tool_registry(http_client)
  callback_adapter = AnalysisJobToolAdapter(http_client)

  settings = get_settings()
  if not settings.chat_api_key and not settings.llm_mock:
    # 没有模型配置时立刻失败：不浪费重试，也不会把 mock 结果当成真实结论落库
    message = "LLM is not configured (set CHAT_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY, or LLM_MOCK=1 for demos)"
    logger.error("agent_job_rejected job_id=%s trace_id=%s reason=%s", job_id, trace_id, message)
    callback_adapter.report_agent_failure(job_id, message, agent_run_id=trace_id, result_version=1)
    return

  harness = create_diagnosis_harness(tools, trace_id=trace_id)

  try:
    result = harness.run(
      task_id=job_id,
      input_payload={"job_id": job_id, "agent_run_id": trace_id, "user_intent": "diagnose_video_gap"},
    )
    if classify_outcome(result) == "SUCCESS":
      observations = result.output.get("draft_observations", [])
      agent_trace = list(result.output.get("agent_trace") or build_lightweight_trace(result.output))
      callback_adapter.report_agent_success(
        job_id,
        observations,
        agent_run_id=str(result.output.get("run_id") or trace_id),
        result_version=int(result.output.get("result_version") or 1),
        agent_trace=agent_trace,
      )
      logger.info(
        "agent_job_success job_id=%s trace_id=%s turns=%s usage=%s hypotheses=%s",
        job_id,
        trace_id,
        result.turns,
        result.usage,
        len(result.output.get("draft_hypotheses") or []),
      )
      return

    error = result.error or result.output.get("error") or f"Agent finished with status={result.status}"
    if result.stop_reason not in ("completed", "error"):
      error = f"[{result.stop_reason}] {error}"
    agent_trace = list(result.output.get("agent_trace") or build_lightweight_trace(result.output)) if result.output else []
    callback_adapter.report_agent_failure(
      job_id,
      error,
      agent_run_id=str(result.output.get("run_id") or trace_id),
      result_version=int(result.output.get("result_version") or 1),
      agent_trace=agent_trace,
    )
    logger.warning(
      "agent_job_failed job_id=%s trace_id=%s status=%s stop_reason=%s error=%s",
      job_id,
      trace_id,
      result.status,
      result.stop_reason,
      error,
    )
  except Exception as exc:
    logger.exception("agent_job_exception job_id=%s trace_id=%s", job_id, trace_id)
    try:
      callback_adapter.report_agent_failure(job_id, str(exc), agent_run_id=trace_id, result_version=1)
    except Exception:
      logger.exception("agent_failure_callback_failed job_id=%s trace_id=%s", job_id, trace_id)
