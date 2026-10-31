from __future__ import annotations

from typing import Any

from agent_service.graph.state import ToolResolution

FRAME_TEXT = "FRAME_TEXT"
KEY_FRAME = "KEY_FRAME"
VIDEO_METADATA = "VIDEO_METADATA"
JOB_EVIDENCE = "JOB_EVIDENCE"
DOMAIN_KNOWLEDGE = "DOMAIN_KNOWLEDGE"
SIMILAR_CASE = "SIMILAR_CASE"
ANALYSIS_RULE = "ANALYSIS_RULE"
# 评分点：该维度下所有类型的知识（模式 / 规则 / 好例 / 反例 / 平台规则），每次诊断前必检索
RUBRIC = "RUBRIC"

VIDEO_EVIDENCE_TYPES = frozenset({FRAME_TEXT, KEY_FRAME, VIDEO_METADATA, JOB_EVIDENCE})
KNOWLEDGE_EVIDENCE_TYPES = frozenset({DOMAIN_KNOWLEDGE, SIMILAR_CASE, ANALYSIS_RULE, RUBRIC})

EVIDENCE_TOOL_MAP = {
  FRAME_TEXT: "get_video_evidence",
  VIDEO_METADATA: "get_video_evidence",
  KEY_FRAME: "get_video_evidence",
  JOB_EVIDENCE: "get_video_evidence",
  DOMAIN_KNOWLEDGE: "retrieve_knowledge",
  SIMILAR_CASE: "retrieve_knowledge",
  ANALYSIS_RULE: "retrieve_knowledge",
  RUBRIC: "retrieve_knowledge",
}

ALLOWED_REACT_TOOLS = frozenset(EVIDENCE_TOOL_MAP.values())

SKILL_ALLOWED_EVIDENCE = {
  "hook_analysis": frozenset(
    {FRAME_TEXT, KEY_FRAME, VIDEO_METADATA, JOB_EVIDENCE, DOMAIN_KNOWLEDGE, SIMILAR_CASE, ANALYSIS_RULE, RUBRIC}
  ),
  "structure_rhythm_analysis": frozenset(
    {KEY_FRAME, VIDEO_METADATA, JOB_EVIDENCE, DOMAIN_KNOWLEDGE, SIMILAR_CASE, ANALYSIS_RULE, RUBRIC}
  ),
  "value_delivery_analysis": frozenset(
    {FRAME_TEXT, VIDEO_METADATA, JOB_EVIDENCE, DOMAIN_KNOWLEDGE, SIMILAR_CASE, ANALYSIS_RULE, RUBRIC}
  ),
}


class ToolResolutionError(Exception):
  pass


def resolve_tool_request(
  skill_key: str,
  evidence_type: str,
  tool_input: dict[str, Any] | None = None,
) -> ToolResolution:
  normalized_type = evidence_type or JOB_EVIDENCE
  allowed = SKILL_ALLOWED_EVIDENCE.get(skill_key, frozenset({JOB_EVIDENCE}))
  if normalized_type not in allowed:
    raise ToolResolutionError(f"Skill {skill_key} is not allowed to request {normalized_type}")
  tool_name = EVIDENCE_TOOL_MAP.get(normalized_type)
  if tool_name is None:
    raise ToolResolutionError(f"Unsupported evidence type: {normalized_type}")
  if tool_name not in ALLOWED_REACT_TOOLS:
    raise ToolResolutionError(f"Tool not whitelisted: {tool_name}")
  return {
    "evidence_type": normalized_type,
    "tool_name": tool_name,
    "skill_key": skill_key,
    "reason": str((tool_input or {}).get("reason") or "Skill requested additional evidence."),
  }
