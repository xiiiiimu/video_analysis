from __future__ import annotations

from dataclasses import dataclass

from agent_service.graph.specialists import CapabilityRegistry


@dataclass(frozen=True)
class RoutingDecision:
  source_agent: str
  target_agent: str
  target_capability: str
  reason: str
  question: str
  evidence_refs: tuple[str, ...]
  status: str = "ROUTED"

  def to_dict(self) -> dict[str, object]:
    return {
      "sourceAgent": self.source_agent,
      "targetAgent": self.target_agent,
      "targetCapability": self.target_capability,
      "reason": self.reason,
      "question": self.question,
      "evidenceRefs": list(self.evidence_refs),
      "status": self.status,
    }


class CentralSupervisor:
  """Routing-only supervisor. It never diagnoses video or calls tools."""

  def __init__(self, registry: CapabilityRegistry | None = None) -> None:
    self._registry = registry or CapabilityRegistry()

  def route(self, handoff_request: dict[str, object]) -> RoutingDecision:
    target_capability = str(handoff_request.get("target_capability") or "")
    target = self._registry.resolve(target_capability)
    return RoutingDecision(
      source_agent=str(handoff_request.get("from_agent") or ""),
      target_agent=target.agent_id,
      target_capability=target_capability,
      reason=str(handoff_request.get("reason") or ""),
      question=str(handoff_request.get("question") or ""),
      evidence_refs=tuple(str(item) for item in handoff_request.get("evidence_refs") or []),
    )
