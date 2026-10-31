"""
诊断质量评测（mock 证据包 + 真实 LLM）。

用法（在 agent-service 容器里，需要已配置 LLM key）：

    python -m agent_service.eval.quality_benchmark --rules v1,v2
    python -m agent_service.eval.quality_benchmark --rules v2 --repeat 3 --cases c01_hook_no_promise,c11_contradiction_bait
    python -m agent_service.eval.quality_benchmark --rules v2 --repeat 3 --cases hard     # 只跑 hard 组（c20 起）
    python -m agent_service.eval.quality_benchmark --rules v2 --rag on,off --repeat 2      # 有 / 无评分点检索（RAG）对比
    python -m agent_service.eval.quality_benchmark --rules v2 --prompt lite --rag on,off --repeat 2  # 去掉写死的定义后再比

同一份评测集分别用 v1（改造前规则）和 v2（新规则）跑，输出对比表（Markdown 打印到终端，JSON 写到 --output-dir）。

判定全部基于规则，不用 LLM 打分（避免"自己出题自己判卷"）：
- 命中预埋问题：对应维度的 GAP 结论，finding_type 与预埋类型一致；
  v1 没有分类表（finding_type 多为 unknown），退化为"维度 + 关键词"匹配（会偏宽松，结果仅供参考）。
- 误报：forbidden 里的问题被报成 GAP，或优势维度被报成 GAP。
- 原文引用：结论里至少有一段 ≥6 个字与证据原文（口播 / 屏幕文字）逐字一致。
- 引用有效：模型引用的条目在证据包中真实存在（时间级引用按时间位置校验）。

模型账户不可用（key 无效 / 余额不足）时 run 以 stop_reason=model_fatal 结束，评测立即中止，
报告标记为"中止"，避免把一堆空结果算成漏报（第一次跑 gpt-5.6-terra 时就出现过）。
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import statistics
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_service.config import get_settings
from agent_service.eval.quality_cases import DIMENSIONS, ISSUE_TYPES, QualityCase, build_cases
from agent_service.graph import diagnosis_skill
from agent_service.graph.builder import build_diagnosis_graph
from agent_service.graph.diagnosis_skill import _invalid_cited_refs
from agent_service.graph.evidence_timeline import (
  normalize_text,
  ocr_items,
  transcript_segments,
  video_aliases,
)
from agent_service.harness.types import HarnessLimits
from agent_service.services.harness_setup import create_diagnosis_harness
from agent_service.tools.adapters.knowledge_retrieval import KnowledgeRetrievalToolAdapter

QUOTE_MIN_CHARS = 6


# ---------------------------------------------------------------- 运行


def run_case(case: QualityCase) -> dict[str, Any]:
  pack = case.evidence_pack()
  saved: dict[str, Any] = {}
  tools = {
    "get_job_context": lambda job_id: {
      "jobId": job_id,
      "targetVideoId": pack["targetEvidence"]["videoAssetId"],
      "referenceVideoIds": [item["videoAssetId"] for item in pack["referenceEvidence"]],
      "inputSnapshotJson": json.dumps(
        {
          "targetTitle": case.title,
          "criteriaText": case.criteria_text,
          "supplementaryAnalysis": case.supplementary,
          "category": case.category,
        },
        ensure_ascii=False,
      ),
    },
    "get_video_evidence": lambda job_id: pack,
    # 评分点检索走真实的运行时知识库（与线上一致）；RAG_MODE=off 时诊断流程不会调用它
    "retrieve_knowledge": KnowledgeRetrievalToolAdapter().retrieve_knowledge,
    "save_diagnosis_result": lambda **kwargs: saved.update(kwargs) or {"findingIds": []},
    "save_diagnosis_hypothesis": lambda job_id, hypothesis: {"findingId": "x"},
    "save_agent_draft_result": lambda job_id, draft_observations: {"ok": True},
    "report_agent_progress": lambda **kwargs: {"ok": True},
  }
  settings = get_settings()
  limits = HarnessLimits(
    max_turns=settings.harness_max_turns,
    max_tokens=settings.harness_max_tokens,
    max_graph_steps=max(settings.harness_max_graph_steps, 80),
    timeout_seconds=max(settings.harness_timeout_seconds, 300),
  )
  # 记录每一次专家调用（含被评估打回后的重写），便于看清"第一轮说了什么、为什么被打回、最后变成了什么"
  attempts: list[dict[str, Any]] = []
  original = diagnosis_skill.diagnose_dimension

  @functools.wraps(original)
  def recording(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
    draft = original(dimension, job_context, evidence_pack, *args, **kwargs)
    attempts.append({
      "dimension": dimension,
      "executionMode": job_context.get("execution_mode", "FULL_DIAGNOSIS"),
      "evaluatorFeedback": list(job_context.get("evaluator_feedback") or []),
      "outcome": draft.get("outcome"),
      "polarity": draft.get("polarity"),
      "findingType": draft.get("finding_type"),
      "confidence": draft.get("confidence"),
      "targetScore": draft.get("target_score"),
      "referenceScores": draft.get("reference_scores") or {},
      "firstBenefitSeconds": draft.get("first_benefit_seconds") or {},
      "quotes": draft.get("quotes") or [],
      "rubricRefs": draft.get("rubric_refs") or [],
      "retrievedRubricRefs": [str(item.get("ref")) for item in job_context.get("rubric") or []],
      "reason": draft.get("reason") or "",
      "observation": draft.get("observation") or "",
    })
    return draft

  started = time.perf_counter()
  diagnosis_skill.diagnose_dimension = recording
  try:
    harness = create_diagnosis_harness(tools, graph=build_diagnosis_graph(), limits=limits)
    result = harness.run(case.case_id, {"job_id": case.case_id, "agent_run_id": f"bench-{case.case_id}"})
  finally:
    diagnosis_skill.diagnose_dimension = original
  latency = time.perf_counter() - started
  output = result.output or {}
  all_results = list(output.get("findings") or [])
  findings = [item for item in all_results if str(item.get("outcome") or "FINDING") == "FINDING"]
  abstained = [str(item.get("dimension")) for item in all_results if str(item.get("outcome")) == "ABSTAIN"]
  score = score_case(case, findings)
  score["abstained"] = abstained
  synthesis = output.get("synthesis") or {}
  if case.expected_criteria:
    score["criteria"] = score_criteria(case, list(synthesis.get("criteriaReport") or []))
  if case.depends_on:
    score["dependencies"] = score_dependencies(case, attempts, findings)
  return {
    "caseId": case.case_id,
    "status": result.status,
    "stopReason": result.stop_reason,
    "error": result.error or output.get("error") or "",
    "latencySeconds": round(latency, 1),
    "usage": result.usage,
    "retries": int(output.get("iteration_count") or 0),
    "findings": [_compact(item) for item in findings],
    "abstained": abstained,
    "attempts": attempts,
    "evaluatorReasons": [item.get("reasons") or [] for item in output.get("evaluation_results") or []],
    # 专家执行失败（异常 / 工具失败）的原因，之前评测里出现过 SPECIALIST_SYSTEM_FAILURE 却看不到原因
    "specialistErrors": [
      {"node": step.get("node"), "summary": step.get("output_summary")}
      for step in output.get("step_traces") or []
      if step.get("status") == "FAILED"
    ],
    "synthesis": output.get("synthesis") or {},
    "score": score,
  }


def _compact(item: dict[str, Any]) -> dict[str, Any]:
  return {
    "dimension": item.get("dimension"),
    "polarity": item.get("polarity") or "GAP",
    "findingType": item.get("finding_type"),
    "observation": item.get("observation"),
    "differenceText": item.get("difference_text"),
    "suggestedAction": item.get("suggested_action"),
    "quotes": item.get("grounded_quotes") or item.get("quotes") or [],
    "citedRefs": item.get("cited_refs") or [],
    "rubricRefs": item.get("rubric_refs") or [],
    "retrievedRubricRefs": item.get("retrieved_rubric_refs") or [],
    "confidence": item.get("confidence"),
    "targetScore": item.get("target_score"),
    "referenceScores": item.get("reference_scores") or {},
    "polarityOverridden": item.get("polarity_overridden") or None,
    "typeCorrected": item.get("type_corrected") or None,
    "downgraded": item.get("downgraded") or None,
  }


# ---------------------------------------------------------------- 打分


def _finding_text(item: dict[str, Any]) -> str:
  parts = [item.get("observation"), item.get("difference_text"), item.get("hypothesis_text"), item.get("suggested_action")]
  parts.extend(str(quote.get("text") or "") for quote in item.get("quotes") or [] if isinstance(quote, dict))
  return " ".join(str(part or "") for part in parts)


def matched_issue_types(item: dict[str, Any]) -> tuple[set[str], str]:
  """一条 GAP 结论对应的问题类型；有分类表类型时只认类型，否则退化为关键词匹配。"""
  dimension = str(item.get("dimension") or "")
  finding_type = str(item.get("finding_type") or "")
  if finding_type in ISSUE_TYPES and ISSUE_TYPES[finding_type]["dimension"] == dimension:
    return {finding_type}, "type"
  text = _finding_text(item)
  hits = {
    key
    for key, meta in ISSUE_TYPES.items()
    if meta["dimension"] == dimension and any(word in text for word in meta["keywords"])
  }
  return hits, "keyword"


def _evidence_texts(pack: dict[str, Any]) -> list[str]:
  texts: list[str] = []
  for _, video in video_aliases(pack):
    texts.extend(str(item.get("text") or "") for item in transcript_segments(video))
    texts.extend(str(item.get("text") or "") for item in ocr_items(video))
  return [normalize_text(text) for text in texts if text]


def has_verbatim_quote(item: dict[str, Any], evidence_texts: list[str]) -> bool:
  text = normalize_text(_finding_text(item))
  for source in evidence_texts:
    for start in range(max(0, len(source) - QUOTE_MIN_CHARS) + 1):
      if source[start : start + QUOTE_MIN_CHARS] in text:
        return True
  return False


def score_case(case: QualityCase, findings: list[dict[str, Any]]) -> dict[str, Any]:
  pack = case.evidence_pack()
  evidence_texts = _evidence_texts(pack)
  gaps = [item for item in findings if str(item.get("polarity") or "GAP") == "GAP"]
  matched: dict[str, set[str]] = {}
  match_modes: list[str] = []
  for item in gaps:
    types, mode = matched_issue_types(item)
    matched.setdefault(str(item.get("dimension")), set()).update(types)
    match_modes.append(mode)
  all_matched = set().union(*matched.values()) if matched else set()

  hits = [issue for issue in case.expected if all_matched & {issue, *case.accept.get(issue, [])}]
  false_alarms = [issue for issue in case.forbidden if issue in all_matched]
  strength_misreported = [dim for dim in case.strength_dims if dim in {str(item.get("dimension")) for item in gaps}]

  invalid_refs = 0
  cited_refs = 0
  for item in findings:
    refs = {
      "target_frame_refs": item.get("target_frame_refs") or [],
      "reference_frame_refs": item.get("reference_frame_refs") or [],
      "evidence_refs": item.get("cited_refs") or item.get("evidence_refs") or [],
    }
    cited_refs += sum(len(value) for value in refs.values())
    invalid_refs += len(_invalid_cited_refs(refs, pack, [])) + len(item.get("invalid_evidence_refs") or [])

  quoted = sum(1 for item in findings if has_verbatim_quote(item, evidence_texts))
  typed = sum(
    1
    for item in findings
    if str(item.get("finding_type") or "") in ISSUE_TYPES or str(item.get("finding_type") or "") in {"strength", "parity"}
  )
  return {
    "expected": list(case.expected),
    "hits": hits,
    "forbidden": list(case.forbidden),
    "falseAlarms": false_alarms,
    "strengthDims": list(case.strength_dims),
    "strengthMisreported": strength_misreported,
    "findingCount": len(findings),
    "gapCount": len(gaps),
    "quotedFindings": quoted,
    "typedFindings": typed,
    "citedRefs": cited_refs,
    "invalidRefs": invalid_refs,
    "matchModes": dict(Counter(match_modes)),
  }


_SKILL_DIMENSION = {
  "hook_analysis": "HOOK",
  "structure_rhythm_analysis": "STRUCTURE_RHYTHM",
  "value_delivery_analysis": "VALUE_DELIVERY",
}


def score_dependencies(
  case: QualityCase, attempts: list[dict[str, Any]], findings: list[dict[str, Any]]
) -> dict[str, Any]:
  """rag 组：这道题依赖的评分点有没有被检索到、最终结论有没有引用它。"""
  from agent_service.knowledge import diagnosis_rubric_corpus

  skill_of = {item.id: item.skill_code for item in diagnosis_rubric_corpus()}
  rows = []
  for rubric_id in case.depends_on:
    dimension = _SKILL_DIMENSION.get(skill_of.get(rubric_id, ""), "")
    ref = f"KNOWLEDGE:{rubric_id}"
    retrieved = any(ref in (item.get("retrievedRubricRefs") or []) for item in attempts if item.get("dimension") == dimension)
    cited = any(ref in (item.get("rubric_refs") or []) for item in findings if str(item.get("dimension")) == dimension)
    rows.append({"id": rubric_id, "dimension": dimension, "retrieved": retrieved, "cited": cited})
  return {"total": len(rows), "retrieved": sum(row["retrieved"] for row in rows), "cited": sum(row["cited"] for row in rows), "rows": rows}


def score_criteria(case: QualityCase, report: list[dict[str, Any]]) -> dict[str, Any]:
  """用户标准：拆出的条数、归属维度、逐条结果和覆盖情况，按顺序与期望对照。"""
  rows = [
    {
      "id": row.get("id"),
      "text": row.get("text"),
      "dimension": row.get("dimension"),
      "verdict": row.get("verdict"),
      "covered": row.get("verdictLabel") != "未覆盖",
      "expectedDimension": expected[0] if expected else None,
      "expectedVerdict": expected[1] if expected else None,
    }
    for row, expected in zip(report, [*case.expected_criteria, *[None] * max(0, len(report) - len(case.expected_criteria))])
  ]
  return {
    "expectedCount": len(case.expected_criteria),
    "parsedCount": len(report),
    "dimensionCorrect": sum(1 for row in rows if row["expectedDimension"] and row["dimension"] == row["expectedDimension"]),
    # 期望结果可以写成 "MET|UNKNOWN"：需要看画面才能完全确认的标准，只依据口播字幕判满足或判无法判断都算对
    "verdictCorrect": sum(
      1 for row in rows if row["expectedVerdict"] and row["verdict"] in str(row["expectedVerdict"]).split("|")
    ),
    "covered": sum(1 for row in rows if row["covered"]),
    "rows": rows,
  }


def aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
  ok = [run for run in runs if run["status"] == "success"]
  scores = [run["score"] for run in ok]
  expected = sum(len(s["expected"]) for s in scores)
  forbidden = sum(len(s["forbidden"]) for s in scores)
  strength = sum(len(s["strengthDims"]) for s in scores)
  findings = sum(s["findingCount"] for s in scores)
  cited = sum(s["citedRefs"] for s in scores)
  tokens = [int((run.get("usage") or {}).get("totalTokens") or 0) for run in ok]
  counts: dict[str, list[int]] = {}

  def rate(key: str, numerator: int, denominator: int) -> float | None:
    # 报告里所有比例都同时给出分子 / 分母，避免只看百分比
    counts[key] = [numerator, denominator]
    return _ratio(numerator, denominator)

  return {
    "runs": len(runs),
    "failedRuns": len(runs) - len(ok),
    "issueRecall": rate("issueRecall", sum(len(s["hits"]) for s in scores), expected),
    "falseAlarmRate": rate("falseAlarmRate", sum(len(s["falseAlarms"]) for s in scores), forbidden),
    "strengthMisreportRate": rate("strengthMisreportRate", sum(len(s["strengthMisreported"]) for s in scores), strength),
    "quotedFindingRate": rate("quotedFindingRate", sum(s["quotedFindings"] for s in scores), findings),
    "typedFindingRate": rate("typedFindingRate", sum(s["typedFindings"] for s in scores), findings),
    "invalidRefRate": rate("invalidRefRate", sum(s["invalidRefs"] for s in scores), cited),
    "abstainRate": rate("abstainRate", sum(len(s.get("abstained") or []) for s in scores), len(scores) * len(DIMENSIONS)),
    # RAG：检索到评分点的结论里，注明了依据评分点的比例
    "rubricCitedRate": rate(
      "rubricCitedRate",
      sum(1 for run in ok for row in run["findings"] if row.get("retrievedRubricRefs") and row.get("rubricRefs")),
      sum(1 for run in ok for row in run["findings"] if row.get("retrievedRubricRefs")),
    ),
    # 用户评分标准（criteria 组）：拆分条数是否正确、归属维度、逐条结果、是否每条都有回应
    "criteriaSplitAccuracy": rate(
      "criteriaSplitAccuracy",
      sum(1 for s in scores if s.get("criteria") and s["criteria"]["parsedCount"] == s["criteria"]["expectedCount"]),
      sum(1 for s in scores if s.get("criteria")),
    ),
    "criteriaDimensionAccuracy": rate(
      "criteriaDimensionAccuracy",
      sum(s["criteria"]["dimensionCorrect"] for s in scores if s.get("criteria")),
      sum(s["criteria"]["expectedCount"] for s in scores if s.get("criteria")),
    ),
    "criteriaVerdictAccuracy": rate(
      "criteriaVerdictAccuracy",
      sum(s["criteria"]["verdictCorrect"] for s in scores if s.get("criteria")),
      sum(s["criteria"]["expectedCount"] for s in scores if s.get("criteria")),
    ),
    "criteriaCoverage": rate(
      "criteriaCoverage",
      sum(s["criteria"]["covered"] for s in scores if s.get("criteria")),
      sum(s["criteria"]["parsedCount"] for s in scores if s.get("criteria")),
    ),
    # rag 组：题目依赖的评分点被检索到 / 被最终结论引用的比例（关闭 RAG 时都为 0）
    "dependencyRetrievedRate": rate(
      "dependencyRetrievedRate",
      sum(s["dependencies"]["retrieved"] for s in scores if s.get("dependencies")),
      sum(s["dependencies"]["total"] for s in scores if s.get("dependencies")),
    ),
    "dependencyCitedRate": rate(
      "dependencyCitedRate",
      sum(s["dependencies"]["cited"] for s in scores if s.get("dependencies")),
      sum(s["dependencies"]["total"] for s in scores if s.get("dependencies")),
    ),
    # 系统纠正模型的次数：评分改写方向 / 按事实改写类型 / 打回用尽后降级。越多说明模型越"不听话"
    "polarityOverrides": sum(1 for run in ok for row in run["findings"] if row.get("polarityOverridden")),
    "typeCorrections": sum(1 for run in ok for row in run["findings"] if row.get("typeCorrected")),
    "downgrades": sum(1 for run in ok for row in run["findings"] if row.get("downgraded")),
    "specialistErrors": sum(len(run.get("specialistErrors") or []) for run in runs),
    "avgRetries": round(statistics.mean([run["retries"] for run in ok]), 2) if ok else None,
    "avgTokens": round(statistics.mean(tokens)) if tokens else None,
    "avgLatencySeconds": round(statistics.mean([run["latencySeconds"] for run in ok]), 1) if ok else None,
    "counts": counts,
  }


def stability(runs: list[dict[str, Any]], counts: dict[str, list[int]] | None = None) -> float | None:
  """同一样本多次运行，各维度 (polarity, 问题类型) 与众数一致的比例。"""
  by_case: dict[str, list[dict[str, Any]]] = {}
  for run in runs:
    if run["status"] == "success":
      by_case.setdefault(run["caseId"], []).append(run)
  agree = total = 0
  for case_runs in by_case.values():
    if len(case_runs) < 2:
      continue
    for dimension in DIMENSIONS:
      labels = []
      for run in case_runs:
        row = next((item for item in run["findings"] if item["dimension"] == dimension), None)
        if row is None:
          labels.append("ABSENT")
          continue
        if row["polarity"] != "GAP":
          # 相当 / 优势只比较方向。之前这里也按关键词匹配问题类型，两次措辞不同（如提到"字幕"）就被算成不一致，
          # 一致性被系统性低估：4o-mini 82%→实际 90%、luna 96%→100%、flash 84%→95%
          labels.append(str(row["polarity"]))
          continue
        types, _ = matched_issue_types(
          {"dimension": dimension, "finding_type": row["findingType"], "observation": row["observation"],
           "difference_text": row["differenceText"], "suggested_action": row["suggestedAction"]}
        )
        labels.append(f"{row['polarity']}:{','.join(sorted(types))}")
      top = Counter(labels).most_common(1)[0][1]
      agree += top
      total += len(labels)
  if counts is not None:
    counts["stability"] = [agree, total]
  return _ratio(agree, total)


def _ratio(numerator: int, denominator: int) -> float | None:
  return round(numerator / denominator, 3) if denominator else None


# ---------------------------------------------------------------- 报告


METRIC_ROWS = [
  ("issueRecall", "预埋问题命中率", "越高越好"),
  ("falseAlarmRate", "误报率（不该报的问题被报出）", "越低越好"),
  ("strengthMisreportRate", "优势被当成问题的比例", "越低越好"),
  ("quotedFindingRate", "带原文引用的结论占比", "越高越好"),
  ("typedFindingRate", "结论类型在分类表内的占比", "越高越好"),
  ("invalidRefRate", "无效引用占比", "越低越好"),
  ("abstainRate", "弃权（ABSTAIN）占比", "越低越好；弃权不计入命中"),
  ("rubricCitedRate", "结论注明依据评分点的占比（RAG）", "越高越好；关闭 RAG 时为 -"),
  ("dependencyRetrievedRate", "题目依赖的评分点被检索到", "rag 组；关闭 RAG 时为 0"),
  ("dependencyCitedRate", "题目依赖的评分点被结论引用", "rag 组；关闭 RAG 时为 0"),
  ("criteriaSplitAccuracy", "用户标准拆分条数正确的样本占比", "criteria 组；越高越好"),
  ("criteriaDimensionAccuracy", "用户标准归属维度正确率", "criteria 组；越高越好"),
  ("criteriaVerdictAccuracy", "用户标准逐条结果正确率", "criteria 组；越高越好"),
  ("criteriaCoverage", "用户标准有回应的占比", "criteria 组；应为 100%"),
  ("stability", "多次运行一致性（--repeat ≥2）", "越高越好"),
  ("avgRetries", "平均评估打回次数", "参考"),
  ("polarityOverrides", "评分改写方向的次数", "参考：模型自报方向与评分不一致"),
  ("typeCorrections", "系统按事实改写类型的次数", "参考"),
  ("downgrades", "打回用尽后降级为相当的次数", "参考：越少说明模型越听反馈"),
  ("specialistErrors", "专家执行失败次数", "越低越好"),
  ("avgTokens", "平均每个样本 token", "参考"),
  ("avgLatencySeconds", "平均耗时（秒）", "参考"),
  ("failedRuns", "运行失败数", "越低越好"),
]


def render_markdown(report: dict[str, Any]) -> str:
  versions = list(report["results"])
  lines = [
    "# 诊断质量评测",
    "",
    f"- 时间：{report['finishedAt']}",
    f"- 模型：{report['model']}（{report.get('provider') or '-'}）",
    f"- 样本数：{report['caseCount']}，每个样本重复 {report['repeat']} 次；评分点检索（RAG）：{report.get('rag', 'on')}；提示词档位：{report.get('prompt', 'full')}",
    *([f"- **已中止**：{report['aborted']}（结果不完整，不能用于比较）"] if report.get("aborted") else []),
    "",
    "| 指标 | " + " | ".join(versions) + " | 说明 |",
    "|---|" + "---|" * len(versions) + "---|",
  ]
  for key, label, note in METRIC_ROWS:
    values = [
      _fmt(
        report["results"][version]["summary"].get(key),
        percent=key in RATE_KEYS,
        count=(report["results"][version]["summary"].get("counts") or {}).get(key),
      )
      for version in versions
    ]
    lines.append(f"| {label} | " + " | ".join(values) + f" | {note} |")
  lines += ["", "## 逐样本", "", "| 样本 | 预埋 | " + " | ".join(f"{v} 命中/误报" for v in versions) + " |", "|---|---|" + "---|" * len(versions)]
  for case_id, case in report["cases"].items():
    cells = []
    for version in versions:
      runs = [run for run in report["results"][version]["runs"] if run["caseId"] == case_id]
      if not runs:
        cells.append("-")
        continue
      hit = sum(len(run["score"]["hits"]) for run in runs if run["status"] == "success")
      alarms = sum(len(run["score"]["falseAlarms"]) + len(run["score"]["strengthMisreported"]) for run in runs if run["status"] == "success")
      failed = sum(1 for run in runs if run["status"] != "success")
      abstains = sum(len(run.get("abstained") or []) for run in runs)
      cells.append(
        f"{hit}/{len(case['expected']) * len(runs)} · 误报 {alarms} · 弃权 {abstains}" + (f" · 失败 {failed}" if failed else "")
      )
    planted = "、".join(case["expected"]) or ("优势:" + "、".join(case["strengthDims"]) if case["strengthDims"] else "无（应无明显问题）")
    lines.append(f"| {case_id} | {planted} | " + " | ".join(cells) + " |")
  lines += [
    "",
    "说明：v1 没有分类表，命中/误报按'维度 + 关键词'匹配，偏宽松；mock 评测只衡量诊断逻辑，不代表真实视频上的准确率。",
  ]
  return "\n".join(lines)


RATE_KEYS = {
  "issueRecall", "falseAlarmRate", "strengthMisreportRate", "quotedFindingRate",
  "typedFindingRate", "invalidRefRate", "abstainRate", "stability", "rubricCitedRate",
  "criteriaSplitAccuracy", "criteriaDimensionAccuracy", "criteriaVerdictAccuracy", "criteriaCoverage",
  "dependencyRetrievedRate", "dependencyCitedRate",
}


def _fmt(value: Any, *, percent: bool = False, count: list[int] | None = None) -> str:
  if value is None:
    return "-"
  if percent:
    return f"{value:.0%}" + (f"（{count[0]}/{count[1]}）" if count else "")
  return str(value)


# ---------------------------------------------------------------- 入口


def _provider(base_url: str) -> str:
  host = (base_url or "").split("//")[-1].split("/")[0]
  return host or "api.openai.com"


def main() -> None:
  parser = argparse.ArgumentParser(description="诊断质量 mock 评测（需要真实 LLM key）")
  parser.add_argument("--rules", default="v1,v2", help="逗号分隔的规则版本，如 v1,v2")
  parser.add_argument("--rag", default="on", help="评分点检索：on / off / on,off（对比）")
  parser.add_argument("--prompt", default="full", help="提示词档位：full（带写死的概念定义）/ lite（去掉）/ full,lite")
  parser.add_argument("--repeat", type=int, default=1, help="每个样本重复次数（≥2 时计算一致性）")
  parser.add_argument("--cases", default="", help="只跑指定样本，逗号分隔；也可以写分组名 base / hard")
  parser.add_argument("--output-dir", default="/tmp/quality-reports")
  args = parser.parse_args()

  settings = get_settings()
  if not settings.chat_api_key or settings.llm_mock:
    raise SystemExit("需要真实 LLM：请配置 CHAT_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY，且 LLM_MOCK=0")

  cases = build_cases()
  if args.cases:
    wanted = {item.strip() for item in args.cases.split(",") if item.strip()}
    cases = [case for case in cases if case.case_id in wanted or case.group in wanted]
    if not cases:
      raise SystemExit(f"没有匹配的样本：{args.cases}")
  rules = [item.strip() for item in args.rules.split(",") if item.strip()]
  rag_modes = [item.strip() for item in args.rag.split(",") if item.strip()]
  prompts = [item.strip() for item in args.prompt.split(",") if item.strip()]
  # 结果按"规则版本 / 提示词档位 / RAG 开关"分列（只有一个取值的维度不出现在列名里）
  versions = [(rule, prompt, rag) for rule in rules for prompt in prompts for rag in rag_modes]
  original = os.environ.get("QUALITY_RULES")
  original_rag = os.environ.get("RAG_MODE")
  original_prompt = os.environ.get("PROMPT_PROFILE")
  results: dict[str, Any] = {}
  aborted = ""
  try:
    for rule, prompt, rag in versions:
      if aborted:
        break
      version = "/".join(
        [rule, *([f"prompt-{prompt}"] if len(prompts) > 1 else []), *([f"rag-{rag}"] if len(rag_modes) > 1 else [])]
      )
      os.environ["QUALITY_RULES"] = rule
      os.environ["RAG_MODE"] = "always" if rag == "on" else "off"
      os.environ["PROMPT_PROFILE"] = prompt
      get_settings.cache_clear()
      runs = []
      for case in cases:
        if aborted:
          break
        for attempt in range(max(1, args.repeat)):
          print(f"[{version}] {case.case_id} #{attempt + 1} ...", flush=True)
          try:
            run = run_case(case)
          except Exception as exc:  # noqa: BLE001 - 单个样本失败不影响整体评测
            run = {"caseId": case.case_id, "status": "exception", "error": str(exc), "findings": [], "abstained": [], "score": {}, "retries": 0}
          runs.append(run)
          print(
            f"    status={run['status']} hits={run['score'].get('hits')} falseAlarms={run['score'].get('falseAlarms')}"
            f" abstained={run.get('abstained')}",
            flush=True,
          )
          if run.get("stopReason") == "model_fatal":
            aborted = f"模型账户不可用（key 无效或余额不足），在 {case.case_id} 中止：{run.get('error')}"
            print(f"\n!! {aborted}\n", flush=True)
            break
      summary = aggregate(runs)
      summary["stability"] = stability(runs, summary.get("counts")) if args.repeat > 1 else None
      results[version] = {"summary": summary, "runs": runs}
  finally:
    if original is None:
      os.environ.pop("QUALITY_RULES", None)
    else:
      os.environ["QUALITY_RULES"] = original
    for key, value in (("RAG_MODE", original_rag), ("PROMPT_PROFILE", original_prompt)):
      if value is None:
        os.environ.pop(key, None)
      else:
        os.environ[key] = value
    get_settings.cache_clear()

  report = {
    "finishedAt": datetime.now(UTC).isoformat(),
    "model": settings.chat_model,
    "provider": _provider(settings.chat_base_url),
    "rag": args.rag,
    "prompt": args.prompt,
    "aborted": aborted,
    "caseCount": len(cases),
    "repeat": args.repeat,
    "cases": {
      case.case_id: {"description": case.description, "expected": case.expected, "forbidden": case.forbidden, "strengthDims": case.strength_dims}
      for case in cases
    },
    "results": results,
  }
  output_dir = Path(args.output_dir)
  output_dir.mkdir(parents=True, exist_ok=True)
  stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
  (output_dir / f"quality-{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
  markdown = render_markdown(report)
  (output_dir / f"quality-{stamp}.md").write_text(markdown, encoding="utf-8")
  print()
  print(markdown)
  print()
  print(f"报告已写入 {output_dir}/quality-{stamp}.json / .md")


if __name__ == "__main__":
  main()
