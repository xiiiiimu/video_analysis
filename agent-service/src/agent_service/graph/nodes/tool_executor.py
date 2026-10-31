from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from agent_service.config import get_settings
from agent_service.graph.criteria import criteria_input, parse_user_criteria
from agent_service.graph.runtime import trace_step
from agent_service.graph.state import AgentGraphState
from agent_service.harness.context import harness_scope


def tool_executor_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
  """
  工具调度节点：通过 Harness.call_tool 调用 Java 内部接口适配器。

  节点内不做护栏判断，全部委托 Harness ToolInterceptor。
  """
  harness = config["configurable"]["harness"]
  harness_ctx = config["configurable"]["harness_ctx"]
  job_id = state["job_id"]
  action = state.get("next_action", "fetch_context")

  if action == "fetch_context":
    with trace_step(state, "tool_executor", input_summary="get_job_context") as step:
      context = dict(harness.call_tool(harness_ctx, "get_job_context", job_id=job_id) or {})
      # 用户上传的评分标准：拆分并归到三个专家 / 补充分析节点（只属于本任务，不进公共知识库）
      criteria_text, supplementary = criteria_input(context)
      criteria: list[dict[str, Any]] = []
      if criteria_text:
        settings = get_settings()
        with harness_scope(harness, harness_ctx, agent_id="criteria_parser"):
          criteria = parse_user_criteria(criteria_text, use_llm=bool(settings.chat_api_key) and not settings.llm_mock)
      context["user_criteria"] = criteria
      context["supplementary_analysis"] = supplementary
      step["tool_calls"] = [{"tool_name": "get_job_context"}]
      step["output_summary"] = f"job_context_loaded user_criteria={len(criteria)} supplementary={supplementary}"
      return {
        "job_context": context,
        "tool_results": [*list(state.get("tool_results") or []), {"tool": "get_job_context", "status": "SUCCESS"}],
        "next_action": "fetch_evidence",
        "done": False,
        "step_traces": state["step_traces"],
      }

  if action == "fetch_evidence":
    with trace_step(state, "tool_executor", input_summary="get_video_evidence") as step:
      evidence = harness.call_tool(harness_ctx, "get_video_evidence", job_id=job_id)
      step["tool_calls"] = [{"tool_name": "get_video_evidence"}]
      step["output_summary"] = "evidence_loaded"
      return {
        "evidence_pack": evidence,
        "tool_results": [*list(state.get("tool_results") or []), {"tool": "get_video_evidence", "status": "SUCCESS"}],
        "next_action": "diagnose",
        "done": False,
        "step_traces": state["step_traces"],
      }

  return {"next_action": "finish", "done": True}
