from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from agent_service.graph.runtime import trace_step
from agent_service.graph.specialists import SPECIALIST_AGENTS
from agent_service.graph.state import AgentGraphState
from agent_service.graph.supervisor import CentralSupervisor


def supervisor_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
  """
  Routing-only Central Supervisor for structured handoff.

  一次只路由一个交接请求，其余请求保留在 ``handoff_requests`` 里，由 Evaluator 决定是否继续 REPLAN；
  交接预算用完时不再让整个 run 失败，而是把剩余请求记入 ``dropped_handoffs``，
  对应的提问方结论会在合成前转成 ABSTAIN（带缺口说明）。
  """
  requests = list(state.get("handoff_requests") or [])
  if not requests:
    return {"next_action": "evaluate", "done": False}

  routing_history = list(state.get("routing_history") or [])
  if len(routing_history) >= state.get("max_agent_handoffs", 2):
    dropped = [
      *list(state.get("dropped_handoffs") or []),
      *({**item, "drop_reason": "agent_handoff_budget_exceeded"} for item in requests),
    ]
    with trace_step(state, "central_supervisor", step_type="SUPERVISOR_DROP", input_summary=f"dropped={len(requests)}") as step:
      step["output_summary"] = "Agent handoff budget exceeded; remaining requests dropped."
    return {
      "handoff_requests": [],
      "dropped_handoffs": dropped,
      "next_action": "evaluate",
      "done": False,
      "step_traces": state["step_traces"],
    }

  request = {**requests[0], "request_id": f"handoff-{len(routing_history) + 1}"}
  with trace_step(state, "central_supervisor", step_type="SUPERVISOR_ROUTE", input_summary=str(request)) as step:
    decision = CentralSupervisor().route(request).to_dict()
    decision["requestId"] = request["request_id"]
    target_agent = str(decision["targetAgent"])
    target = SPECIALIST_AGENTS[target_agent]
    history = [*routing_history, decision]
    step["agent_id"] = target_agent
    step["sourceAgent"] = decision["sourceAgent"]
    step["targetCapability"] = decision["targetCapability"]
    step["targetAgent"] = target_agent
    step["question"] = decision["question"]
    step["evidenceRefs"] = decision["evidenceRefs"]
    step["gateResult"] = "ACCEPTED"
    step["output_summary"] = f"{decision['sourceAgent']}->{target_agent}:{decision['targetCapability']}"
    return {
      "active_handoff": request,
      "handoff_requests": requests[1:],
      "routing_history": history,
      "global_replan_count": state.get("global_replan_count", 0) + 1,
      "agents_to_run": [target_agent],
      "skills_to_run": [target.skill_binding],
      "status": "RUNNING",
      "next_action": "diagnose",
      "done": False,
      "step_traces": state["step_traces"],
    }
