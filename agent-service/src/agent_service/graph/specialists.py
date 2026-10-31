from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecialistAgentDefinition:
  agent_id: str
  role: str
  goal: str
  capabilities: tuple[str, ...]
  allowed_tools: tuple[str, ...]
  skill_binding: str
  knowledge_namespaces: tuple[str, ...]
  output_contract: str = "Finding with confidence, evidence_refs, evidence_gaps, and optional handoff_requests."


SPECIALIST_AGENTS: dict[str, SpecialistAgentDefinition] = {
  "hook_agent": SpecialistAgentDefinition(
    agent_id="hook_agent",
    role="HookDiagnosisAgent",
    goal="Diagnose whether the opening earns attention and makes an early value promise.",
    capabilities=("hook_analysis", "hook_timing", "opening_pattern", "curiosity_gap", "early_value_promise"),
    allowed_tools=("get_video_evidence", "retrieve_knowledge"),
    skill_binding="hook_analysis",
    knowledge_namespaces=("hook_analysis",),
  ),
  "structure_agent": SpecialistAgentDefinition(
    agent_id="structure_agent",
    role="StructureDiagnosisAgent",
    goal="Diagnose content structure, pacing, segment progression, and rhythm changes.",
    capabilities=("structure_rhythm_analysis", "pacing", "content_structure", "segment_progression", "rhythm_change"),
    allowed_tools=("get_video_evidence", "retrieve_knowledge"),
    skill_binding="structure_rhythm_analysis",
    knowledge_namespaces=("structure_rhythm_analysis",),
  ),
  "value_agent": SpecialistAgentDefinition(
    agent_id="value_agent",
    role="ValueDiagnosisAgent",
    goal="Diagnose user benefit, value proposition, use case, and actionability.",
    capabilities=("value_delivery_analysis", "user_benefit", "value_proposition", "use_case", "actionability", "value_delivery"),
    allowed_tools=("get_video_evidence", "retrieve_knowledge"),
    skill_binding="value_delivery_analysis",
    knowledge_namespaces=("value_delivery_analysis",),
  ),
}

SKILL_TO_AGENT = {definition.skill_binding: definition.agent_id for definition in SPECIALIST_AGENTS.values()}
SKILL_BINDINGS = {agent_id: definition.skill_binding for agent_id, definition in SPECIALIST_AGENTS.items()}


class CapabilityRegistry:
  def __init__(self, agents: dict[str, SpecialistAgentDefinition] | None = None) -> None:
    self._agents = agents or SPECIALIST_AGENTS
    self._capability_to_agent = {
      capability: definition.agent_id
      for definition in self._agents.values()
      for capability in definition.capabilities
    }

  def resolve(self, capability: str) -> SpecialistAgentDefinition:
    agent_id = self._capability_to_agent.get(capability)
    if not agent_id:
      raise ValueError(f"No specialist agent registered for capability={capability}")
    return self._agents[agent_id]


def specialist_for_skill(skill_key: str) -> SpecialistAgentDefinition:
  agent_id = SKILL_TO_AGENT[skill_key]
  return SPECIALIST_AGENTS[agent_id]
