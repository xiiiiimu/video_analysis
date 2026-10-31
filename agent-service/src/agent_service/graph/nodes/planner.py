from typing import Any

from langchain_core.runnables import RunnableConfig

from agent_service.graph.runtime import report_stage, trace_step
from agent_service.graph.specialists import specialist_for_skill
from agent_service.graph.state import CORE_DIAGNOSIS_SKILLS, AgentGraphState


def plan_node(state: AgentGraphState, config: RunnableConfig) -> dict[str, Any]:
  """输出固定、机器可执行的诊断计划，不做业务 Triage。"""
  report_stage(state, config, "PLANNING", 62, "Agent planning diagnosis skills.")

  with trace_step(state, "planner", input_summary=f"job_id={state['job_id']}") as step:
    plan = [
      {
        **item,
        "agent_id": specialist_for_skill(item["skill_key"]).agent_id,
        "skill_snapshot": state["skill_snapshots"][specialist_for_skill(item["skill_key"]).agent_id],
        "required_evidence": ["JOB_EVIDENCE", "KEY_FRAME", "FRAME_TEXT", "VIDEO_METADATA"],
      }
      for item in CORE_DIAGNOSIS_SKILLS
    ]
    observations = list(state.get("draft_observations", []))
    observations.append("plan:" + ",".join(item["skill_key"] for item in plan))
    step["output_summary"] = f"skills={len(plan)}"
    return {
      "plan": plan,
      "skills_to_run": [item["skill_key"] for item in plan],
      "draft_observations": observations,
      "status": "PLANNED",
      "next_action": "fetch_context",
      "done": False,
      "step_traces": state["step_traces"],
    }
