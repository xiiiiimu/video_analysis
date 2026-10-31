from __future__ import annotations

import json
import logging
import re
from typing import Any

from agent_service.config import get_settings
from agent_service.graph.criteria import criterion_payload, normalize_verdicts
from agent_service.graph.evidence_timeline import (
  TARGET_ALIAS,
  build_video_view,
  ocr_items,
  reference_alias,
  transcript_segments,
  window_for_dimension,
)
from agent_service.graph.finding_types import GAP, POLARITIES, taxonomy_prompt_lines
from agent_service.graph.state import DraftHypothesis
from agent_service.harness.context import call_model
from agent_service.llm.prompts.diagnosis import (
  CONCEPT_CONTRACT_LITE,
  CONCEPT_DEFINITIONS_V2,
  CRITERIA_RULES_V2,
  DIMENSION_DIAGNOSIS_SYSTEM_PROMPT,
  DIMENSION_DIAGNOSIS_SYSTEM_PROMPT_V2,
  RUBRIC_RULES_V2,
)

logger = logging.getLogger(__name__)


MAX_KEYFRAMES = 8
MAX_REFERENCES = 3


class LLMNotConfiguredError(RuntimeError):
  """没有可用的模型配置，且没有显式开启 LLM_MOCK。"""


def _extract_json(text: str) -> dict[str, Any]:
  text = text.strip()
  try:
    return json.loads(text)
  except json.JSONDecodeError:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
      return json.loads(match.group(0))
    raise


def diagnose_dimension(
  dimension: str,
  job_context: dict[str, Any],
  evidence_pack: dict[str, Any],
  skill_procedure: str = "",
) -> DraftHypothesis:
  """
  对单一维度执行 LLM 诊断。

  - 有 API Key：真实调用（经过 harness）；
  - LLM_MOCK=1：返回 mock 草稿（仅测试 / 演示）；
  - 两者都没有：直接失败。改造前会悄悄返回 mock 结果并当作真实 Finding 落库。
  """
  settings = get_settings()
  user_payload = _build_user_payload(dimension, job_context, evidence_pack, skill_procedure)

  if settings.llm_mock:
    logger.warning("LLM_MOCK enabled, using mock diagnosis for dimension=%s", dimension)
    parsed = _mock_diagnosis(dimension, evidence_pack)
    parsed.setdefault("rubric_refs", [str(item.get("ref")) for item in (job_context.get("rubric") or [])[:1]])
    parsed.setdefault(
      "criteria_verdicts",
      [{"id": item["id"], "verdict": "UNKNOWN", "reason": "LLM_MOCK"} for item in job_context.get("user_criteria") or []],
    )
  elif settings.chat_api_key:
    from agent_service.llm.provider import get_chat_model

    llm = get_chat_model()
    # 统一经过 harness：发模型事件、统计 token、传输层重试（ModelRetryPlugin）、
    # JSON 解析失败时带反馈重试（OutputFormatGuard）、token 限额检查（LimitsPlugin）。
    _, parsed = call_model(
      llm.invoke,
      [
        {"role": "system", "content": render_dimension_system_prompt(dimension)},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
      ],
      parse=lambda response: _extract_json(str(response.content)),
    )
  else:
    raise LLMNotConfiguredError(
      "CHAT_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY 均未配置；如只是本地演示，请设置 LLM_MOCK=1"
    )

  return DraftHypothesis(
    dimension=dimension,
    outcome=str(parsed.get("outcome") or "FINDING"),
    finding_type=str(parsed.get("finding_type", "")),
    reason=str(parsed.get("reason", "")),
    question=str(parsed.get("question", "")),
    target_capability=str(parsed.get("target_capability", "")),
    observation=str(parsed.get("observation", "")),
    difference_text=str(parsed.get("difference_text", "")),
    hypothesis_text=str(parsed.get("hypothesis_text", "")),
    suggested_action=str(parsed.get("suggested_action", "")),
    # 模型偶尔输出格式不对（字符串代替列表、列表里夹着 null / 对象）：在这里规整，避免后续步骤崩溃
    target_frame_refs=_str_list(parsed.get("target_frame_refs")),
    reference_frame_refs=_str_list(parsed.get("reference_frame_refs")),
    evidence_refs=_str_list(parsed.get("evidence_refs")),
    evidence_gaps=_dict_list(parsed.get("evidence_gaps")),
    evidence_gap=parsed.get("evidence_gap") if isinstance(parsed.get("evidence_gap"), dict) else {},
    handoff_requests=_dict_list(parsed.get("handoff_requests")),
    counter_evidence=str(parsed.get("counter_evidence", "")),
    polarity=_polarity(parsed.get("polarity")),
    quotes=_quotes(parsed.get("quotes")),
    rubric_refs=_str_list(parsed.get("rubric_refs")),
    criteria_verdicts=normalize_verdicts(parsed.get("criteria_verdicts")),
    target_score=_score(parsed.get("target_score")),
    reference_scores=_reference_scores(parsed.get("reference_scores")),
    first_benefit_seconds=_benefit_seconds(parsed.get("first_benefit_seconds")),
    # 模型没给置信度时按 0 处理（交给 Evaluator 判断），不再默认 0.7 让它自动通过阈值
    confidence=_confidence(parsed.get("confidence")),
  )


def _confidence(value: Any) -> float:
  try:
    number = float(value)
  except (TypeError, ValueError):
    return 0.0
  return max(0.0, min(1.0, number))


def _str_list(value: Any) -> list[str]:
  if isinstance(value, str):
    value = [value]
  if not isinstance(value, list):
    return []
  return [str(item).strip() for item in value if isinstance(item, (str, int, float)) and str(item).strip()]


def _dict_list(value: Any) -> list[dict[str, Any]]:
  if not isinstance(value, list):
    return []
  return [item for item in value if isinstance(item, dict)]


def _benefit_seconds(value: Any) -> dict[str, float | None]:
  """{"T": 0.5, "R1": 2, "R2": null}：每个视频第一次说出观众收益的秒数（模型填写，系统用来核对"收益太晚"）。"""
  if not isinstance(value, dict):
    return {}
  rows: dict[str, float | None] = {}
  for key, raw in value.items():
    name = str(key).strip().upper()
    if not name:
      continue
    try:
      rows[name] = None if raw is None else float(raw)
    except (TypeError, ValueError):
      rows[name] = None
  return rows


def _score(value: Any) -> float | None:
  try:
    number = float(value)
  except (TypeError, ValueError):
    return None
  return number if 1.0 <= number <= 5.0 else None


def _reference_scores(value: Any) -> dict[str, float]:
  if not isinstance(value, dict):
    return {}
  rows: dict[str, float] = {}
  for key, raw in value.items():
    score = _score(raw)
    if score is not None and str(key).strip():
      rows[str(key).strip().upper()] = score
  return rows


def _polarity(value: Any) -> str:
  text = str(value or "").strip().upper()
  # v1 prompt 没有 polarity：一律按 GAP 处理（与改造前"所有结论都是待改进问题"的行为一致）
  return text if text in POLARITIES else GAP


def _quotes(value: Any) -> list[dict[str, str]]:
  rows: list[dict[str, str]] = []
  if not isinstance(value, list):
    return rows
  for item in value:
    if isinstance(item, dict) and str(item.get("text") or "").strip():
      rows.append({"ref": str(item.get("ref") or "").strip(), "text": str(item.get("text") or "").strip()})
  return rows


def render_dimension_system_prompt(dimension: str) -> str:
  """Render only the explicit dimension placeholder; JSON examples stay literal."""
  if get_settings().quality_rules == "v1":
    return DIMENSION_DIAGNOSIS_SYSTEM_PROMPT.replace("{dimension}", dimension)
  rubric_rules = RUBRIC_RULES_V2 if get_settings().rag_mode == "always" else ""
  return (
    DIMENSION_DIAGNOSIS_SYSTEM_PROMPT_V2.replace("{dimension}", dimension)
    .replace("{taxonomy}", taxonomy_prompt_lines())
    .replace("{rubric_rules}", rubric_rules)
    .replace("{criteria_rules}", CRITERIA_RULES_V2)
    .replace(
      "{concept_definitions}",
      CONCEPT_DEFINITIONS_V2 if get_settings().prompt_profile == "full" else CONCEPT_CONTRACT_LITE,
    )
  )


def _build_user_payload(
  dimension: str,
  job_context: dict[str, Any],
  evidence_pack: dict[str, Any],
  skill_procedure: str = "",
) -> dict[str, Any]:
  """
  组装发给模型的输入。

  - v0.2 数据（有 timelineJson）：按时间轴组织（关键帧时间点 / 镜头 / 屏幕文字分段 / 口播分段），
    HOOK 只看开场窗口，其它维度看完整分析窗口（默认 120 秒）；
  - 旧数据：沿用改造前的 legacy 视图。

  截断不是静默的：``truncation`` 告诉模型哪些内容被截掉，模型可以据此降低置信度或 ABSTAIN。
  """
  settings = get_settings()
  text_limit = settings.evidence_text_limit
  target = evidence_pack.get("targetEvidence") or {}
  references = evidence_pack.get("referenceEvidence") or []
  truncation: dict[str, Any] = {}
  window = window_for_dimension(dimension, settings.hook_window_seconds)

  def clip(field: str, value: Any, limit: int = text_limit) -> str:
    text = "" if value is None else (value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
    if len(text) > limit:
      truncation[field] = {"originalChars": len(text), "keptChars": limit}
    return _clip(text, limit)

  def frames(field: str, items: list[Any] | None) -> list[Any]:
    rows = list(items or [])
    if len(rows) > MAX_KEYFRAMES:
      truncation[field] = {"originalCount": len(rows), "keptCount": MAX_KEYFRAMES}
    return rows[:MAX_KEYFRAMES]

  def video_view(video: dict[str, Any], alias: str, prefix: str, *, include_scene: bool) -> dict[str, Any]:
    view = build_video_view(
      video,
      alias,
      window=window,
      max_keyframes=settings.evidence_max_keyframes,
      max_segments=settings.evidence_max_segments,
      segment_chars=settings.evidence_segment_chars,
      truncation=truncation,
      field_prefix=prefix,
    )
    if view is not None:
      return view
    legacy = {
      "alias": alias,
      "videoAssetId": video.get("videoAssetId"),
      "transcript": clip(f"{prefix}.transcript", video.get("transcriptText")),
      "keyframes": frames(f"{prefix}.keyframes", video.get("keyframes")),
      "ocrJson": clip(f"{prefix}.ocrJson", video.get("ocrJson")),
    }
    if include_scene:
      legacy["sceneJson"] = clip(f"{prefix}.sceneJson", video.get("sceneJson"))
    return legacy

  payload = {
    "dimension": dimension,
    "skillProcedure": clip("skillProcedure", skill_procedure, settings.skill_procedure_limit),
    "evidenceFormat": EVIDENCE_FORMAT_NOTE,
    "job": {
      "jobId": job_context.get("jobId"),
      "targetVideoId": job_context.get("targetVideoId"),
      "referenceVideoIds": job_context.get("referenceVideoIds"),
      "inputSnapshot": job_context.get("inputSnapshotJson"),
      "executionMode": job_context.get("execution_mode", "FULL_DIAGNOSIS"),
      "handoffContext": job_context.get("handoff_context") or {},
      "handoffAnswer": job_context.get("handoff_answer") or {},
      "evaluatorFeedback": list(job_context.get("evaluator_feedback") or []),
    },
    "target": video_view(target, TARGET_ALIAS, "target", include_scene=True),
    "references": [
      video_view(ref, reference_alias(index), f"references[{index}]", include_scene=True)
      for index, ref in enumerate(references[:MAX_REFERENCES])
    ],
  }
  rubric = list(job_context.get("rubric") or [])
  if rubric:
    payload["rubric"] = rubric
  user_criteria = list(job_context.get("user_criteria") or [])
  if user_criteria:
    payload["userCriteria"] = [criterion_payload(item) for item in user_criteria]
  if len(references) > MAX_REFERENCES:
    truncation["references"] = {"originalCount": len(references), "keptCount": MAX_REFERENCES}
  payload["truncation"] = truncation
  return payload


EVIDENCE_FORMAT_NOTE = (
  "target 的 alias 为 T，references 依次为 R1、R2。所有 s 字段都是秒数（如 s=\"65-72\" 表示第 65~72 秒），"
  "判断时间先后一律以 s 为准；ref 字段是可以直接复制的引用（其中 HH:MM:SS 是时:分:秒，00:01:05 是第 65 秒）。"
  "字段：sceneStats=系统算好的镜头统计（镜头数、平均/中位/最长镜头时长、2 秒内短镜头数、每 30 秒切换次数），"
  "引用 METADATA:T；scenes=逐个镜头（ref, s, len 时长）；keyframeTimes=关键帧时间点（你看不到画面）；"
  "screenText=屏幕文字分段；speech=口播分段，speechStatus 不是 ok 时没有口播；"
  "coverage.window 非空时只给了该时间窗口内的证据。"
)


def _clip(text: str | None, limit: int = 800) -> str:
  if not text:
    return ""
  return text if len(text) <= limit else text[:limit] + "..."


def _mock_diagnosis(dimension: str, evidence_pack: dict[str, Any]) -> dict[str, Any]:
  target = evidence_pack.get("targetEvidence") or {}
  keyframes = target.get("keyframes") or ["00:00:00-00:00:05"]
  mock_type = {"HOOK": "hook_no_value_promise", "STRUCTURE_RHYTHM": "pacing_too_dense", "VALUE_DELIVERY": "value_late"}
  return {
    "polarity": "GAP",
    "finding_type": mock_type.get(dimension, "other"),
    "quotes": _mock_quotes(target) + _mock_quotes((evidence_pack.get("referenceEvidence") or [{}])[0], alias="R1"),
    "target_score": 2,
    "reference_scores": {"R1": 4},
    "outcome": "FINDING",
    "observation": f"Mock observation for {dimension}",
    "difference_text": "Target pacing differs from references in early segment.",
    "hypothesis_text": f"Opening segment in {dimension} may not match reference baseline.",
    "suggested_action": "Strengthen the opening value statement within first 3 seconds.",
    "target_frame_refs": keyframes[:2],
    "reference_frame_refs": ["ref_segment_00_05"],
    "counter_evidence": "Style-led videos may intentionally delay the hook.",
    "confidence": 0.72,
  }


def _mock_quotes(target: dict[str, Any], alias: str = TARGET_ALIAS) -> list[dict[str, str]]:
  """LLM_MOCK 演示模式下也给出真实存在的原文引用（目标 + 参考），保证 v2 质量检查能通过。"""
  segments = transcript_segments(target)
  if segments:
    return [{"ref": f"ASR:{alias}@{segments[0].get('start', '')}", "text": str(segments[0].get("text") or "")}]
  items = ocr_items(target)
  if items:
    return [{"ref": f"OCR:{alias}@{items[0].get('time', '')}", "text": str(items[0].get("text") or "")}]
  text = str(target.get("transcriptText") or "").strip()
  if text:
    return [{"ref": f"ASR:{alias}", "text": text[:20]}]
  return []
