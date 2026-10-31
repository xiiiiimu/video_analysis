"""
跨维度合成：把三个 Specialist 的结论合成为一份带优先级的总体诊断。

- 规则版（确定性，总是可用）：按维度权重 × 置信度排序，列出待补证据和交接情况；
- LLM 版（可选）：在规则版的基础上让模型写总体总结、合并重复建议；
  输出经过校验（只能引用已有维度），任何失败都回退到规则版，不影响 run 成功。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_service.graph.finding_types import GAP, PARITY, STRENGTH
from agent_service.llm.prompts.diagnosis import DIMENSION_LABELS

logger = logging.getLogger(__name__)

# 维度权重：开场钩子决定是否继续观看，优先级最高
DIMENSION_WEIGHT = {"HOOK": 1.0, "VALUE_DELIVERY": 0.9, "STRUCTURE_RHYTHM": 0.8}

SYNTHESIS_SYSTEM_PROMPT = """
你是短视频诊断的总编辑。输入是多个维度 Specialist 已经通过质量评估的结论（findings）和规则排序结果（priorities）。
任务：
1. 写一段 2-3 句的总体总结（summary），说明目标视频与参考视频最关键的差距。
2. 给出最终的改进优先级（priorities），只能使用输入里出现过的 skillKey，可以调整顺序，并为每条写一句理由。
3. 合并重复或互相依赖的建议，输出 mergedActions（每条可执行、具体）。
约束：不得引入输入中没有的事实；polarity 为 STRENGTH / PARITY 的维度是目标的优势或与参考相当，
不能写进 priorities 和 mergedActions，只能在 summary 里作为优势提及；输出 JSON，不要 markdown 代码块。
输出格式：
{"summary": "...", "priorities": [{"skillKey": "...", "rationale": "..."}], "mergedActions": ["..."]}
""".strip()


def build_rule_synthesis(
  findings: list[dict[str, Any]],
  *,
  completion_status: str,
  evaluation_results: list[dict[str, Any]] | None = None,
  handoff_answers: list[dict[str, Any]] | None = None,
  dropped_handoffs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
  conclusive_all = [item for item in findings if item.get("outcome", "FINDING") == "FINDING"]
  abstained = [item for item in findings if item.get("outcome") == "ABSTAIN"]
  v2 = _quality_v2()
  # v2：只有 GAP（目标比参考差）进入改进优先级；优势 / 相当单独列出
  conclusive = [item for item in conclusive_all if not v2 or str(item.get("polarity") or GAP) == GAP]
  strengths = [_brief(item) for item in conclusive_all if v2 and str(item.get("polarity")) == STRENGTH]
  parity = [_brief(item) for item in conclusive_all if v2 and str(item.get("polarity")) == PARITY]

  ranked = sorted(
    conclusive,
    key=lambda item: DIMENSION_WEIGHT.get(str(item.get("dimension")), 0.5) * float(item.get("confidence") or 0),
    reverse=True,
  )
  priorities = [
    {
      "rank": index + 1,
      "skillKey": item.get("skill_key"),
      "dimension": item.get("dimension"),
      "findingType": item.get("finding_type") or "",
      "suggestedAction": item.get("suggested_action") or "",
      "confidence": float(item.get("confidence") or 0),
      "rationale": f"{DIMENSION_LABELS.get(str(item.get('dimension')), item.get('dimension'))}：{item.get('observation') or ''}",
    }
    for index, item in enumerate(ranked)
  ]
  gaps = [
    {
      "skillKey": item.get("skill_key"),
      "dimension": item.get("dimension"),
      "reason": item.get("reason") or item.get("observation") or "",
      "systemFailure": bool(item.get("system_failure")),
    }
    for item in abstained
  ]
  last_eval = (evaluation_results or [{}])[-1] if evaluation_results else {}
  conflicts = [reason for reason in last_eval.get("reasons") or [] if "conflicting" in str(reason)]

  if priorities:
    top = priorities[0]
    label = DIMENSION_LABELS.get(str(top["dimension"]), top["dimension"])
    summary = f"共 {len(priorities)} 个维度需要改进，最优先改进「{label}」：{top['suggestedAction']}"
  elif strengths or parity:
    summary = "目标视频在已诊断的维度上不弱于参考视频，没有需要优先改进的问题。"
  else:
    summary = "各维度均未形成可靠结论，需要补充证据后重新诊断。"
  if strengths:
    summary += "优势：" + "、".join(DIMENSION_LABELS.get(str(item["dimension"]), str(item["dimension"])) for item in strengths) + "。"
  if gaps:
    summary += f"（另有 {len(gaps)} 个维度因证据不足未下结论）"

  return {
    "source": "rule",
    "summary": summary,
    "priorities": priorities,
    "mergedActions": [item["suggestedAction"] for item in priorities if item["suggestedAction"]],
    "evidenceGaps": gaps,
    "strengths": strengths,
    "parity": parity,
    "conflicts": conflicts,
    "handoffs": [
      {
        "requestId": item.get("request_id"),
        "fromAgent": item.get("from_agent"),
        "toAgent": item.get("to_agent"),
        "question": item.get("question"),
        "status": item.get("status"),
      }
      for item in handoff_answers or []
    ],
    "droppedHandoffs": len(dropped_handoffs or []),
    "completionStatus": completion_status,
  }


def refine_with_llm(base: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
  """用 LLM 改写总结与优先级；输出校验失败或调用失败时返回 base。"""
  from agent_service.config import get_settings
  from agent_service.harness.context import call_model

  settings = get_settings()
  if not settings.chat_api_key or getattr(settings, "llm_mock", False) or not base["priorities"]:
    return base
  from agent_service.llm.provider import get_chat_model

  payload = {
    "findings": [
      {
        "skillKey": item.get("skill_key"),
        "dimension": item.get("dimension"),
        "outcome": item.get("outcome"),
        "polarity": item.get("polarity") or GAP,
        "findingType": item.get("finding_type"),
        "observation": item.get("observation"),
        "differenceText": item.get("difference_text"),
        "suggestedAction": item.get("suggested_action"),
        "quotes": item.get("grounded_quotes") or [],
        "confidence": item.get("confidence"),
      }
      for item in findings
    ],
    "strengths": base.get("strengths") or [],
    "priorities": base["priorities"],
    "evidenceGaps": base["evidenceGaps"],
    "conflicts": base["conflicts"],
  }
  try:
    _, parsed = call_model(
      get_chat_model().invoke,
      [
        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
      ],
      parse=lambda response: _parse_json(str(response.content)),
    )
  except Exception as exc:  # noqa: BLE001 - 合成增强失败不影响 run
    logger.warning("llm_synthesis_failed error=%s", exc)
    return base
  return merge_llm_synthesis(base, parsed)


def merge_llm_synthesis(base: dict[str, Any], parsed: Any) -> dict[str, Any]:
  if not isinstance(parsed, dict) or not str(parsed.get("summary") or "").strip():
    return base
  by_skill = {item["skillKey"]: item for item in base["priorities"]}
  ordered: list[dict[str, Any]] = []
  for item in parsed.get("priorities") or []:
    skill_key = item.get("skillKey") if isinstance(item, dict) else None
    if skill_key in by_skill and all(row["skillKey"] != skill_key for row in ordered):
      ordered.append({**by_skill[skill_key], "rationale": str(item.get("rationale") or by_skill[skill_key]["rationale"])})
  # 模型漏掉的维度按规则顺序补在后面；模型编造的维度直接忽略
  ordered.extend(row for row in base["priorities"] if all(o["skillKey"] != row["skillKey"] for o in ordered))
  for index, row in enumerate(ordered):
    row["rank"] = index + 1
  actions = [str(item) for item in parsed.get("mergedActions") or [] if str(item).strip()]
  return {
    **base,
    "source": "llm",
    "summary": str(parsed["summary"]).strip(),
    "priorities": ordered,
    "mergedActions": actions or base["mergedActions"],
  }


def _parse_json(text: str) -> dict[str, Any]:
  from agent_service.llm.diagnosis_llm import _extract_json

  return _extract_json(text)


def assign_priorities(findings: list[dict[str, Any]], synthesis: dict[str, Any]) -> list[dict[str, Any]]:
  """
  按合成后的最终排序给结论分配优先级：第 1 名 P0、第 2 名 P1、其余 P2。
  Java 结果接口用这个优先级排序，保证与 synthesis 的排序一致（改造前 Java 按置信度 ≥0.85 自行判定 P0）。
  """
  rank_by_skill = {str(item.get("skillKey")): int(item.get("rank") or 0) for item in synthesis.get("priorities") or []}
  rows = []
  for finding in findings:
    rank = rank_by_skill.get(str(finding.get("skill_key")))
    if rank:
      finding = {**finding, "priority": "P0" if rank == 1 else ("P1" if rank == 2 else "P2")}
    rows.append(finding)
  return rows


def persistable_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
  """v2：只有 GAP 结论和 ABSTAIN 作为 Finding 落库；优势 / 相当只出现在 synthesis 里。"""
  if not _quality_v2():
    return findings
  return [
    item
    for item in findings
    if item.get("outcome", "FINDING") != "FINDING" or str(item.get("polarity") or GAP) == GAP
  ]


def _brief(item: dict[str, Any]) -> dict[str, Any]:
  return {
    "skillKey": item.get("skill_key"),
    "dimension": item.get("dimension"),
    "observation": item.get("observation") or "",
    "quotes": list(item.get("grounded_quotes") or [])[:2],
    # 打回用尽仍违反硬规则、由 GAP 降级而来的条目，注明原因（例如"开场与参考相同"）
    "downgraded": item.get("downgraded") or None,
  }


def _quality_v2() -> bool:
  from agent_service.config import get_settings

  return get_settings().quality_rules != "v1"
