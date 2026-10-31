"""
补充分析节点。

- 默认只补漏：用户标准里不属于三个专家（开场钩子 / 结构节奏 / 价值传递）的条目，由这里逐条回应；
- 用户勾选"整体补充分析"时，再额外给出最多 3 条三个专家没有覆盖到的观察，作为补充材料。

在三个专家通过 Evaluator 之后运行，能看到专家的结论，避免重复；输出不进入改进优先级 / Finding 落库，
只出现在 synthesis.supplementary 和报告里。约束和专家一样：观察必须带能在证据里找到的逐字引用，
找不到的观察直接丢弃；逐条回应缺了的条目再要求一次，仍然缺就在报告里标"未覆盖"。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_service.config import get_settings
from agent_service.graph.criteria import (
  OTHER,
  criteria_for_dimension,
  criterion_payload,
  normalize_verdicts,
  verdict_coverage,
)
from agent_service.graph.evidence_timeline import ground_quotes

logger = logging.getLogger(__name__)

MAX_NOTES = 3

SUPPLEMENTARY_SYSTEM_PROMPT = """
你是短视频对比诊断的补充分析专家。三个专家（开场钩子、结构节奏、价值传递）已经给出结论（expertConclusions）。

你的任务：
1. otherCriteria 是用户上传、但不属于三个专家的评分标准。对每一条给出 criteria_verdicts：
   verdict 为 MET（目标满足）/ NOT_MET（目标不满足）/ UNKNOWN（证据不足无法判断），reason 写清目标第几秒说了什么、
   出现了什么文字或缺了什么，evidence 复制相关证据的 ref；verdict=NOT_MET 时 suggestion 给出具体改法。不要省略任何一条。
   带 limitation 的标准只能部分检查：只依据口播和屏幕文字判断，reason 里写明"画面 / 音频部分未检查"；
   不能因为口播和字幕里没出现就断定画面里也没有。
2. 仅当 overall=true 时：再给出最多 3 条 notes，内容必须是三个专家没有提到的方面（不要复述他们的结论），
   每条有 title、observation（具体事实 + 与参考的对比）、quotes（逐字摘抄 speech / screenText 的原文，ref 复制该分段的 ref）。
   overall=false 时 notes 输出 []。

你看不到画面，只能依据口播、屏幕文字、镜头数据推理，禁止臆造画面内容。证据格式见 evidenceFormat。
只输出 JSON（不要 markdown 代码块）：
{"criteria_verdicts": [{"id": "U3", "verdict": "NOT_MET", "reason": "...", "suggestion": "具体改法", "evidence": ["OCR:T@00:00:12"]}],
 "notes": [{"title": "...", "observation": "...", "quotes": [{"ref": "ASR:T@00:00:05", "text": "逐字原文"}]}]}
""".strip()


def needs_supplementary(job_context: dict[str, Any]) -> bool:
  return bool(criteria_for_dimension(list(job_context.get("user_criteria") or []), OTHER)) or bool(
    job_context.get("supplementary_analysis")
  )


def run_supplementary(
  job_context: dict[str, Any],
  evidence_pack: dict[str, Any],
  findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
  if not needs_supplementary(job_context):
    return None
  other = criteria_for_dimension(list(job_context.get("user_criteria") or []), OTHER)
  overall = bool(job_context.get("supplementary_analysis"))
  assigned = [str(item["id"]) for item in other]
  settings = get_settings()

  if settings.llm_mock or not settings.chat_api_key:
    parsed: dict[str, Any] = {
      "criteria_verdicts": [{"id": item_id, "verdict": "UNKNOWN", "reason": "LLM_MOCK"} for item_id in assigned],
      "notes": [],
    }
    attempts = 1
  else:
    feedback: list[str] = []
    parsed = {}
    attempts = 0
    for attempts in range(1, 3):  # 缺回应时再要求一次
      parsed = _call(other, overall, evidence_pack, findings, job_context, feedback)
      missing, _ = verdict_coverage(assigned, normalize_verdicts(parsed.get("criteria_verdicts")))
      if not missing:
        break
      feedback = [f"上一次没有回应 {'、'.join(missing)}，请对 otherCriteria 的每一条都给出 verdict。"]

  verdicts = [row for row in normalize_verdicts(parsed.get("criteria_verdicts")) if row["id"] in assigned]
  missing, _ = verdict_coverage(assigned, verdicts)
  notes, dropped = _grounded_notes(parsed.get("notes") if overall else [], evidence_pack)
  return {
    "mode": "overall" if overall else "criteria_only",
    "criteriaIds": assigned,
    "verdicts": verdicts,
    "missingCriteriaIds": missing,
    "notes": notes,
    "droppedNotes": dropped,
    "attempts": attempts,
  }


def _call(
  other: list[dict[str, Any]],
  overall: bool,
  evidence_pack: dict[str, Any],
  findings: list[dict[str, Any]],
  job_context: dict[str, Any],
  feedback: list[str],
) -> dict[str, Any]:
  from agent_service.harness.context import call_model
  from agent_service.llm.diagnosis_llm import _build_user_payload, _extract_json
  from agent_service.llm.provider import get_chat_model

  payload = _build_user_payload("SUPPLEMENTARY", job_context, evidence_pack)
  payload.pop("rubric", None)
  payload.pop("userCriteria", None)
  payload["otherCriteria"] = [criterion_payload(item) for item in other]
  payload["overall"] = overall
  payload["expertConclusions"] = [
    {
      "dimension": item.get("dimension"),
      "polarity": item.get("polarity"),
      "findingType": item.get("finding_type"),
      "observation": str(item.get("observation") or "")[:300],
    }
    for item in findings
    if str(item.get("outcome") or "FINDING") == "FINDING"
  ]
  if feedback:
    payload["feedback"] = feedback
  _, parsed = call_model(
    get_chat_model().invoke,
    [
      {"role": "system", "content": SUPPLEMENTARY_SYSTEM_PROMPT},
      {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ],
    parse=lambda response: _extract_json(str(response.content)),
  )
  return parsed if isinstance(parsed, dict) else {}


def _grounded_notes(raw: Any, evidence_pack: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
  notes: list[dict[str, Any]] = []
  dropped = 0
  for item in raw if isinstance(raw, list) else []:
    if not isinstance(item, dict):
      continue
    quotes = [quote for quote in item.get("quotes") or [] if isinstance(quote, dict)]
    grounded, _ = ground_quotes(quotes, evidence_pack)
    if not grounded or not str(item.get("observation") or "").strip():
      dropped += 1  # 没有可核对的原文证据：不交给用户
      continue
    notes.append({
      "title": str(item.get("title") or "补充").strip(),
      "observation": str(item.get("observation") or "").strip(),
      "quotes": grounded,
    })
  return notes[:MAX_NOTES], dropped + max(0, len(notes) - MAX_NOTES)
