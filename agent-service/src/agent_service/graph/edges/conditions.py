from __future__ import annotations

from agent_service.graph.state import AgentGraphState

TOOL_ACTIONS = {
  "fetch_context",
  "fetch_evidence",
}


def route_by_action(state: AgentGraphState) -> str:
  if state.get("done"):
    return "end"
  action = state.get("next_action", "plan")
  if action == "plan":
    return "plan"
  if action in TOOL_ACTIONS:
    return "tools"
  if action == "diagnose":
    return "diagnose"
  if action == "evaluate":
    return "evaluate"
  if action == "supervise":
    return "supervise"
  if action == "synthesize":
    return "synthesize"
  return "end"
