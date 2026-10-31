"""
诊断业务的 intervention handler（业务规则，所以放在 graph 层，不放进 harness 默认值）。

harness 只提供“返回决策”的机制；这里决定具体规则。
"""

from __future__ import annotations

from agent_service.graph.specialists import SPECIALIST_AGENTS, SpecialistAgentDefinition
from agent_service.harness.events import BeforeToolCallEvent
from agent_service.harness.interventions import (
  Deny,
  InterventionAction,
  InterventionHandler,
  Proceed,
  Transform,
)


class SpecialistToolPolicy(InterventionHandler):
  """
  Specialist 只能调用自己 ``allowed_tools`` 里的工具。

  这是 harness 层的第二道防线：ReAct 循环里已经按 allowed_tools 做过一次检查，
  但任何绕过 ReAct、直接在 Specialist 作用域里调用工具的代码也会被拦下。
  不在 Specialist 作用域里的调用（外层流程取上下文、保存结果）不受影响。
  ``on_error="deny"``：策略检查自己出错时宁可拒绝（fail-closed）。
  """

  name = "specialist-tool-policy"
  on_error = "deny"

  def __init__(self, agents: dict[str, SpecialistAgentDefinition] | None = None) -> None:
    self._agents = agents or SPECIALIST_AGENTS

  def before_tool_call(self, event: BeforeToolCallEvent) -> InterventionAction:
    if not event.agent_id:
      return Proceed()
    agent = self._agents.get(event.agent_id)
    if agent is None:
      return Deny(f"Unknown specialist agent: {event.agent_id}")
    if event.tool_name not in agent.allowed_tools:
      return Deny(f"{agent.agent_id} 只能调用 {', '.join(agent.allowed_tools)}，不能调用 {event.tool_name}")
    return Proceed()


class JobIdPinning(InterventionHandler):
  """
  工具参数里的 ``job_id`` 一律固定为本次 run 的 job_id（Transform 决策）。

  防止任何一层（将来的 LLM 选工具、拼错的参数）把请求发到别的任务上。
  """

  name = "job-id-pinning"

  def before_tool_call(self, event: BeforeToolCallEvent) -> InterventionAction:
    job_id = event.ctx.job_id
    if not job_id or "job_id" not in event.tool_args or event.tool_args.get("job_id") == job_id:
      return Proceed()

    def pin(target: BeforeToolCallEvent) -> None:
      target.tool_args["job_id"] = job_id

    return Transform(apply=pin, reason=f"job_id pinned to {job_id}")


def diagnosis_interventions() -> list[InterventionHandler]:
  return [SpecialistToolPolicy(), JobIdPinning()]
