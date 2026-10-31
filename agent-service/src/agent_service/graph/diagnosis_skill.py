from __future__ import annotations

import inspect
from typing import Any

from agent_service.config import get_settings
from agent_service.graph.criteria import verdict_coverage
from agent_service.graph.evidence_timeline import (
  evidence_refs_for_video,
  ground_quotes,
  has_text_evidence,
  is_time_level_ref,
  opening_text,
  time_ref_is_grounded,
  video_aliases,
)
from agent_service.graph.finding_types import GAP, OPENING_SECONDS, PARITY, STRENGTH
from agent_service.graph.state import DiagnosisPlanItem, DraftHypothesis
from agent_service.llm.diagnosis_llm import diagnose_dimension


def run_diagnosis_skill(
  skill: DiagnosisPlanItem,
  job_context: dict[str, Any],
  evidence_pack: dict[str, Any],
  knowledge_observations: list[dict[str, Any]] | None = None,
) -> DraftHypothesis:
  """统一 Diagnosis Skill 抽象：输入证据与目标，输出 Finding 草稿和证据缺口。"""
  dimension = skill["dimension"]
  hypothesis = dict(_diagnose_with_skill_snapshot(dimension, job_context, evidence_pack, skill))
  hypothesis["skill_key"] = skill["skill_key"]
  hypothesis["dimension"] = dimension
  knowledge_refs = _collect_knowledge_refs(knowledge_observations or [])
  # 校验模型引用的证据是否真实存在：编造的帧/引用不能算作“有证据支撑”
  invalid_refs = _invalid_cited_refs(hypothesis, evidence_pack, knowledge_refs)
  if invalid_refs:
    invalid = set(invalid_refs)
    for key in ("target_frame_refs", "reference_frame_refs", "evidence_refs"):
      hypothesis[key] = [item for item in hypothesis.get(key) or [] if str(item).strip() not in invalid]
  hypothesis["invalid_evidence_refs"] = invalid_refs
  # 模型自己引用的条目（下面会再自动补充视频级引用，判断"只引用了帧"时要看这里）
  hypothesis["cited_refs"] = list(
    dict.fromkeys(
      str(item).strip()
      for key in ("target_frame_refs", "reference_frame_refs", "evidence_refs")
      for item in hypothesis.get(key) or []
      if str(item).strip()
    )
  )
  grounded_quotes, quote_issues = ground_quotes(list(hypothesis.get("quotes") or []), evidence_pack)
  hypothesis["grounded_quotes"] = grounded_quotes
  hypothesis["quote_issues"] = quote_issues
  hypothesis.setdefault("polarity", "GAP")
  if get_settings().quality_rules != "v1":
    apply_score_polarity(hypothesis)
    apply_fact_corrections(hypothesis, evidence_pack)
  if get_settings().rag_mode == "always":
    # RAG 评分点：只保留模型声明且确实检索到的评分点作为知识依据，而不是把检索结果整批挂到每条结论上
    cited_rubric = [str(item).strip() for item in hypothesis.get("rubric_refs") or [] if str(item).strip()]
    hypothesis["retrieved_rubric_refs"] = knowledge_refs
    hypothesis["invalid_rubric_refs"] = [ref for ref in cited_rubric if ref not in knowledge_refs]
    knowledge_refs = [ref for ref in dict.fromkeys(cited_rubric) if ref in knowledge_refs]
    hypothesis["rubric_refs"] = knowledge_refs
  # 用户评分标准：只保留对分给本维度的条目的回应，记录缺少回应的条目（Evaluator 据此打回）
  assigned = [str(item["id"]) for item in job_context.get("user_criteria") or [] if item.get("id")]
  verdicts = [row for row in hypothesis.get("criteria_verdicts") or [] if row.get("id") in assigned]
  hypothesis["assigned_criteria_ids"] = assigned
  hypothesis["criteria_verdicts"] = verdicts
  hypothesis["missing_criteria_ids"], _ = verdict_coverage(assigned, verdicts)
  video_refs = _collect_video_evidence_refs(hypothesis, evidence_pack)
  evidence_refs = list(dict.fromkeys([*video_refs, *knowledge_refs]))
  hypothesis["video_evidence_refs"] = video_refs
  hypothesis["knowledge_evidence_refs"] = knowledge_refs
  hypothesis["evidence_refs"] = evidence_refs
  hypothesis["evidence_gaps"] = _detect_evidence_gaps(
    skill,
    hypothesis,
    evidence_pack,
    video_refs,
    knowledge_refs,
    job_context,
    knowledge_observations or [],
  )
  return DraftHypothesis(**hypothesis)


def _diagnose_with_skill_snapshot(
  dimension: str,
  job_context: dict[str, Any],
  evidence_pack: dict[str, Any],
  skill: DiagnosisPlanItem,
) -> DraftHypothesis:
  skill_content = str((skill.get("skill_snapshot") or {}).get("content") or "")
  signature = inspect.signature(diagnose_dimension)
  if "skill_procedure" in signature.parameters:
    return diagnose_dimension(dimension, job_context, evidence_pack, skill_procedure=skill_content)
  return diagnose_dimension(dimension, job_context, evidence_pack)


def _collect_video_evidence_refs(
  hypothesis: dict[str, Any],
  evidence_pack: dict[str, Any],
) -> list[str]:
  refs: list[str] = []
  for key in ("target_frame_refs", "reference_frame_refs"):
    for item in hypothesis.get(key) or []:
      text = str(item).strip()
      if text:
        refs.append(text)

  target = evidence_pack.get("targetEvidence") or {}
  if target.get("transcriptText"):
    refs.append(f"ASR:{target.get('videoAssetId', 'target')}")
  if target.get("ocrJson"):
    refs.append(f"OCR:{target.get('videoAssetId', 'target')}")
  if target.get("sceneJson"):
    refs.append(f"METADATA:{target.get('videoAssetId', 'target')}")
  return list(dict.fromkeys(refs))


def known_evidence_refs(evidence_pack: dict[str, Any]) -> set[str]:
  """证据包里真实存在、可以被引用的条目（含 v0.2 时间轴引用，如 FRAME:T@00:01:03）。"""
  known: set[str] = set()
  for alias, video in video_aliases(evidence_pack):
    known |= evidence_refs_for_video(video, alias)
  return known


def _invalid_cited_refs(
  hypothesis: dict[str, Any],
  evidence_pack: dict[str, Any],
  knowledge_refs: list[str],
) -> list[str]:
  known = known_evidence_refs(evidence_pack) | set(knowledge_refs)
  cited: list[str] = []
  for key in ("target_frame_refs", "reference_frame_refs", "evidence_refs"):
    cited.extend(str(item).strip() for item in hypothesis.get(key) or [] if str(item).strip())
  invalid: list[str] = []
  for ref in dict.fromkeys(cited):
    if is_time_level_ref(ref):
      # 时间级引用（FRAME:T@00:01:03 等）按时间位置严格校验，不走下面的宽松子串匹配
      if not time_ref_is_grounded(ref, evidence_pack):
        invalid.append(ref)
      continue
    if ref in known:
      continue
    if ref.startswith("KNOWLEDGE:"):
      invalid.append(ref)  # 引用了没有检索到的知识条目
      continue
    # 宽松匹配：时间戳包含在帧 URL / id 里，或反之
    if any(ref in item or item in ref for item in known if len(item) >= 4):
      continue
    invalid.append(ref)
  return invalid


def _collect_knowledge_refs(observations: list[dict[str, Any]]) -> list[str]:
  refs: list[str] = []
  for observation in observations:
    refs.extend(str(item) for item in observation.get("knowledge_evidence_refs") or [])
    refs.extend(str(item) for item in observation.get("evidence_refs") or [] if str(item).startswith("KNOWLEDGE:"))
  return list(dict.fromkeys(refs))


def _detect_evidence_gaps(
  skill: DiagnosisPlanItem,
  hypothesis: dict[str, Any],
  evidence_pack: dict[str, Any],
  video_refs: list[str],
  knowledge_refs: list[str],
  job_context: dict[str, Any],
  knowledge_observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  gaps = list(hypothesis.get("evidence_gaps") or [])
  target = evidence_pack.get("targetEvidence") or {}
  keyframes = target.get("keyframes") or []
  has_text = has_text_evidence(target)

  if not video_refs:
    gaps.append(_gap(skill, "JOB_EVIDENCE", "Finding lacks concrete evidence references."))

  if skill["skill_key"] == "hook_analysis" and not has_text:
    gaps.append(_gap(skill, "FRAME_TEXT", "Hook analysis needs visible text or transcript in the opening segment."))

  if not keyframes:
    gaps.append(_gap(skill, "KEY_FRAME", "Diagnosis needs key frame evidence."))

  if _requires_knowledge(job_context) and not knowledge_refs and not _knowledge_degraded(knowledge_observations):
    gaps.append(_gap(skill, "DOMAIN_KNOWLEDGE", "Diagnosis requested domain knowledge but no knowledge evidence was retrieved."))

  return gaps


def _gap(skill: DiagnosisPlanItem, evidence_type: str, reason: str) -> dict[str, Any]:
  return {
    "skillKey": skill["skill_key"],
    "dimension": skill["dimension"],
    "evidenceType": evidence_type,
    "reason": reason,
  }


def _requires_knowledge(job_context: dict[str, Any]) -> bool:
  return bool(job_context.get("needKnowledge") or job_context.get("category") or job_context.get("useKnowledge"))


def _knowledge_degraded(observations: list[dict[str, Any]]) -> bool:
  return any(bool((item.get("payload") or {}).get("degraded")) for item in observations)


# 目标比"做得最好的参考"低至少这么多分才算差距（GAP），高至少这么多分才算优势（STRENGTH）
SCORE_MARGIN = 1.0


def apply_score_polarity(hypothesis: dict[str, Any]) -> None:
  """
  差距方向由系统根据评分计算，而不是采信模型自己写的 polarity。

  第二轮真实评测发现：目标与参考开场完全相同（甚至目标更好），模型仍判为 GAP——它在孤立地给目标挑毛病，
  没有执行"参考更好才算差距"。现在模型必须分别给目标和每个参考打分（1~5），方向按分差确定：
  目标比最好的参考低 ≥1 分 → GAP；高 ≥1 分 → STRENGTH；否则 PARITY。与模型自报方向不一致时以评分为准并记录。
  """
  if str(hypothesis.get("outcome") or "FINDING") != "FINDING":
    return
  target = hypothesis.get("target_score")
  references = dict(hypothesis.get("reference_scores") or {})
  if target is None or not references:
    return  # 缺评分由 Evaluator 打回
  best = max(references.values())
  diff = float(target) - best
  derived = GAP if diff <= -SCORE_MARGIN else (STRENGTH if diff >= SCORE_MARGIN else PARITY)
  model = str(hypothesis.get("polarity") or GAP)
  if derived == model:
    return
  hypothesis["polarity_overridden"] = {
    "model": model,
    "derived": derived,
    "targetScore": target,
    "bestReferenceScore": best,
  }
  hypothesis["polarity"] = derived
  if derived == PARITY:
    hypothesis["finding_type"] = "parity"
  elif derived == STRENGTH:
    hypothesis["finding_type"] = "strength"
  # 改成 GAP 时保留模型的类型；若是 strength / parity，Evaluator 会要求从分类表选一个具体问题


def apply_fact_corrections(hypothesis: dict[str, Any], evidence_pack: dict[str, Any]) -> None:
  """
  系统可以直接算出来的事实，不交给模型判断（第三次评测 c02：开场前 6 秒没有任何口播 / 字幕，
  模型判对了"开场有问题"，却选成了 hook_no_value_promise）。
  """
  if str(hypothesis.get("outcome") or "FINDING") != "FINDING" or str(hypothesis.get("polarity") or GAP) != GAP:
    return
  if str(hypothesis.get("dimension")) == "HOOK" and str(hypothesis.get("finding_type")) != "hook_slow_start":
    target = evidence_pack.get("targetEvidence") or {}
    if not opening_text(target, seconds=OPENING_SECONDS):
      hypothesis["type_corrected"] = {
        "from": hypothesis.get("finding_type"),
        "to": "hook_slow_start",
        "reason": f"目标前 {OPENING_SECONDS:g} 秒没有任何口播和屏幕文字",
      }
      hypothesis["finding_type"] = "hook_slow_start"
