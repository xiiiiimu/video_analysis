"""
诊断图的初始 state（原来写死在 harness/runner.py 里）。

这些都是业务字段（Skill 快照、handoff 预算、草稿列表），属于 graph 层；
harness 只通过 ``graph.initial_state(payload, run_id)`` 调用它，不知道里面有什么。
"""

from __future__ import annotations

from typing import Any

from agent_service.config import get_settings
from agent_service.graph.specialists import SKILL_BINDINGS
from agent_service.skills import SkillLoader


def build_initial_state(
  input_payload: dict[str, Any],
  run_id: str,
  skill_loader: SkillLoader | None = None,
) -> dict[str, Any]:
  loader = skill_loader or SkillLoader()
  # AgentRun 开始时对 Skill 做不可变快照：运行中磁盘文件变化不影响本次 run
  skill_snapshots = loader.load_many(SKILL_BINDINGS)
  skill_loaded_traces = [
    {
      "node": "harness",
      "agent_id": agent_id,
      "step_type": "SKILL_LOADED",
      "start": "",
      "end": "",
      "status": "SUCCESS",
      "iteration": 0,
      "tool_calls": [],
      "skill_id": snapshot["skill_id"],
      "skill_version": snapshot["version"],
      "skill_hash": snapshot["content_hash"],
      "output_summary": f"{snapshot['skill_id']}@{snapshot['version']}",
    }
    for agent_id, snapshot in skill_snapshots.items()
  ]
  settings = get_settings()
  return {
    "run_id": run_id,
    "job_id": input_payload.get("job_id"),
    "result_version": 1,
    "skill_snapshots": skill_snapshots,
    "agent_states": {},
    "handoff_requests": [],
    "routing_history": [],
    "handoff_answers": [],
    "pending_integration": None,
    "dropped_handoffs": [],
    "retry_feedback": {},
    "global_replan_count": 0,
    "max_global_replans": settings.max_global_replans,
    "max_agent_handoffs": settings.max_agent_handoffs,
    "plan": [],
    "evidence_refs": [],
    "knowledge_evidence_refs": [],
    "findings": [],
    "evidence_gaps": [],
    "tool_results": [],
    "evaluation_results": [],
    "iteration_count": 0,
    "react_iterations_by_skill": {},
    "tool_observations": [],
    "knowledge_observations": [],
    "retrieval_traces": [],
    "skill_execution_status": {},
    "status": "RUNNING",
    "step_traces": skill_loaded_traces,
    "agent_trace": [],
    "draft_messages": [],
    "draft_observations": [],
    "draft_hypotheses": [],
    "next_action": "plan",
    "done": False,
  }
