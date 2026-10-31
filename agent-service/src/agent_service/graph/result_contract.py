from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agent_service.config import get_settings
from agent_service.graph.finding_types import NON_GAP_TYPES, OTHER_TYPE, types_for_dimension
from agent_service.graph.specialists import CapabilityRegistry, SpecialistAgentDefinition

SpecialistOutcome = Literal["FINDING", "ABSTAIN", "NEEDS_CAPABILITY"]

ALLOWED_FINDING_TYPES: dict[str, set[str]] = {
  "hook_analysis": {
    "strong_opening_hook",
    "self_intro_delay",
    "empty_suspense",
    "visual_result_hook",
    "opening_value_boundary",
    "pain_point_opening_vs_benefit_opening",
    "hook_pain_vs_benefit_opening",
    "evidence_gap",
    "unknown",
    "mock_diagnosis",
  },
  "structure_rhythm_analysis": {
    "structure_opening_pattern_difference",
    "structure_rhythm_opening_order_gap",
    "fast_cut_without_answer",
    "static_talking_low_density",
    "topic_jump",
    "rhythm_marker_missing",
    "evidence_gap",
    "unknown",
    "mock_diagnosis",
  },
  "value_delivery_analysis": {
    "delayed_value_statement",
    "delayed_value_delivery",
    "value_framing_gap_pain_vs_benefit",
    "pain_first_value_benefit_unclear",
    "clear_steps_missing_audience_outcome",
    "proof_before_claim",
    "evidence_gap",
    "unknown",
    "mock_diagnosis",
  },
}


_SKILL_DIMENSION = {
  "hook_analysis": "HOOK",
  "structure_rhythm_analysis": "STRUCTURE_RHYTHM",
  "value_delivery_analysis": "VALUE_DELIVERY",
}


def _v2_allowed_types(skill_code: str) -> set[str]:
  """v1 白名单 + v2 分类表（graph/finding_types.py）+ strength / parity / other。"""
  return {
    *ALLOWED_FINDING_TYPES.get(skill_code, set()),
    *types_for_dimension(_SKILL_DIMENSION.get(skill_code, "")),
    *NON_GAP_TYPES,
    OTHER_TYPE,
  }


@dataclass(frozen=True)
class GateDecision:
  accepted: bool
  request: dict[str, Any] | None = None
  reason: str = ""


def normalize_specialist_result(raw: dict[str, Any], skill: dict[str, Any]) -> dict[str, Any]:
  result = dict(raw)
  skill_code = str(skill.get("skill_key") or result.get("skill_key") or "")
  outcome = str(result.get("outcome") or "").upper()
  if outcome not in {"FINDING", "ABSTAIN", "NEEDS_CAPABILITY"}:
    outcome = "ABSTAIN" if result.get("evidence_gaps") and not result.get("observation") else "FINDING"
  result["outcome"] = outcome
  result["skill_key"] = skill_code
  result["skill_code"] = skill_code

  finding_type = str(result.get("finding_type") or "")
  if outcome == "ABSTAIN":
    result["finding_type"] = "evidence_gap"
  elif finding_type in _v2_allowed_types(skill_code):
    pass
  elif get_settings().quality_rules != "v1":
    # v2：不在分类表里的类型原样保留，由 Evaluator 带着允许列表打回重试；
    # 改造前这里会静默改成 unknown，导致线上结论的 findingType 全是 unknown
    result["finding_type"] = finding_type or "unknown"
  elif finding_type not in ALLOWED_FINDING_TYPES.get(skill_code, set()):
    result["finding_type"] = "unknown"

  if outcome == "FINDING":
    result.pop("handoff_requests", None)
  if outcome == "ABSTAIN":
    result.pop("handoff_requests", None)
    result.setdefault("reason", _first_gap_reason(result) or "Insufficient evidence.")
    result.setdefault("evidence_gap", _first_gap(result))
    result.setdefault("observation", result.get("reason", "Insufficient evidence."))
    result.setdefault("suggested_action", "Collect more evidence before making a reliable diagnosis.")
  if outcome == "NEEDS_CAPABILITY":
    result.setdefault("reason", _first_gap_reason(result) or "Capability handoff required.")
    result.setdefault("question", "")
    result.setdefault("target_capability", "")
  return result


def make_abstain_result(skill: dict[str, Any], reason: str, evidence_refs: list[str] | None = None) -> dict[str, Any]:
  gap = {"skillKey": skill["skill_key"], "dimension": skill["dimension"], "evidenceType": "UNKNOWN", "reason": reason}
  return normalize_specialist_result(
    {
      "outcome": "ABSTAIN",
      "skill_key": skill["skill_key"],
      "dimension": skill["dimension"],
      "finding_type": "evidence_gap",
      "reason": reason,
      "evidence_gap": gap,
      "evidence_gaps": [gap],
      "evidence_refs": evidence_refs or [],
      "confidence": 0.0,
    },
    skill,
  )


def evaluate_handoff_gate(
  *,
  result: dict[str, Any],
  agent: SpecialistAgentDefinition,
  routing_history: list[dict[str, Any]],
  max_agent_handoffs: int,
  active_handoff: dict[str, Any] | None = None,
  registry: CapabilityRegistry | None = None,
) -> GateDecision:
  if result.get("outcome") != "NEEDS_CAPABILITY":
    return GateDecision(False, reason="outcome_not_needs_capability")
  if active_handoff:
    return GateDecision(False, reason="targeted_reinvestigation_cannot_handoff")
  if len(routing_history) >= max_agent_handoffs:
    return GateDecision(False, reason="handoff_budget_exceeded")

  target_capability = str(result.get("target_capability") or "")
  if not target_capability:
    return GateDecision(False, reason="missing_target_capability")
  registry = registry or CapabilityRegistry()
  try:
    target = registry.resolve(target_capability)
  except ValueError:
    return GateDecision(False, reason="unregistered_target_capability")
  if target.agent_id == agent.agent_id:
    return GateDecision(False, reason="self_handoff_rejected")

  question = str(result.get("question") or "").strip()
  if not _specific_question(question):
    return GateDecision(False, reason="invalid_or_generic_question")
  reason = str(result.get("reason") or _first_gap_reason(result) or "").strip()
  if not reason:
    return GateDecision(False, reason="missing_reason")
  evidence_refs = list(result.get("evidence_refs") or [])
  if not evidence_refs:
    return GateDecision(False, reason="missing_evidence_refs")

  duplicate_key = (agent.agent_id, target_capability, question)
  for item in routing_history:
    existing = (
      str(item.get("sourceAgent") or item.get("source_agent") or ""),
      str(item.get("targetCapability") or item.get("target_capability") or ""),
      str(item.get("question") or ""),
    )
    if existing == duplicate_key:
      return GateDecision(False, reason="duplicate_handoff_rejected")

  request = {
    "from_agent": agent.agent_id,
    "target_capability": target_capability,
    "reason": reason,
    "question": question,
    "evidence_refs": evidence_refs,
    "confidence": float(result.get("confidence") or 0),
    "source_finding": _source_finding(result),
  }
  return GateDecision(True, request=request, reason="accepted")


def rejected_handoff_to_abstain(skill: dict[str, Any], result: dict[str, Any], reason: str) -> dict[str, Any]:
  abstain = make_abstain_result(
    skill,
    f"Handoff rejected: {reason}. {result.get('reason') or ''}".strip(),
    list(result.get("evidence_refs") or []),
  )
  abstain["handoff_rejected"] = {"reason": reason, "target_capability": result.get("target_capability", "")}
  return abstain


def _specific_question(question: str) -> bool:
  generic = {"请继续分析", "请确认一下", "继续分析", "确认一下", "please continue", "please check"}
  return len(question.strip()) >= 8 and question.strip().lower() not in generic


def _first_gap(result: dict[str, Any]) -> dict[str, Any]:
  gaps = list(result.get("evidence_gaps") or [])
  first = gaps[0] if gaps else {}
  return dict(first) if isinstance(first, dict) else {}


def _first_gap_reason(result: dict[str, Any]) -> str:
  return str(_first_gap(result).get("reason") or "")


def _source_finding(result: dict[str, Any]) -> dict[str, Any]:
  return {
    "skill_key": result.get("skill_key", ""),
    "finding_type": result.get("finding_type", ""),
    "observation": result.get("observation", ""),
    "evidence_refs": list(result.get("evidence_refs") or []),
    "confidence": result.get("confidence", 0),
  }
