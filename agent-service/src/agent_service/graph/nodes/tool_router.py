from __future__ import annotations

from typing import Any

from agent_service.graph.state import AgentGraphState


def tool_router_node(state: AgentGraphState, config: dict[str, Any]) -> dict[str, Any]:
  """
  智能工具路由预留节点。

  当前主流程已降级为确定性 Tool Resolver，不再把 tool_router 挂入核心图。
  只有未来确实需要模型动态选择工具时，才应重新启用此节点。
  """
  harness = config["configurable"]["harness"]
  harness_ctx = config["configurable"]["harness_ctx"]
  job_id = state["job_id"]
  action = state.get("next_action", "fetch_context")

  if action == "fetch_context":
    harness.call_tool(harness_ctx, "get_job_context", job_id=job_id)
    return {"next_action": "reason", "done": False}

  if action == "persist":
    harness.call_tool(
      harness_ctx,
      "save_agent_draft_result",
      job_id=job_id,
      draft_observations=state.get("draft_observations", []),
    )
    return {"next_action": "finish", "done": True}

  return {"next_action": "finish", "done": True}
