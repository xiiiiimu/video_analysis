from __future__ import annotations

from typing import Any

from agent_service.graph.state import AgentGraphState


def reason_node(state: AgentGraphState, config: dict[str, Any]) -> dict[str, Any]:
  """推理节点：基于草稿观察生成中间结论（仍不落库）。"""

  observations = state.get("draft_observations", [])
  summary = " | ".join(observations[-3:]) if observations else "no_observation"
  return {
    "draft_messages": [{"role": "assistant", "content": f"draft_reasoning:{summary}"}],
    "next_action": "persist",
    "done": False,
  }
