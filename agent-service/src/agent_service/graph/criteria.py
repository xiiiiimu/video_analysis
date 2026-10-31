"""
用户自定义评分标准。

用户随任务上传一段任意格式的文字（txt），这里负责：

1. 拆分：按行 / 编号 / 分号拆成一条条可检查的标准，原文保留（U1、U2 ...）；
2. 归类：每条归到三个专家之一（HOOK / STRUCTURE_RHYTHM / VALUE_DELIVERY），都不属于的归 OTHER，
   由补充分析节点处理。有模型时由模型归类（可校验的 JSON），失败或 mock 时用关键词规则兜底；
3. 回应：专家必须对分到自己的每一条给出 MET / NOT_MET / UNKNOWN（criteria_verdicts），Evaluator 检查覆盖；
4. 报告：解析出的标准 + 逐条对照结果。

用户标准优先级高于内置评分点：两者冲突时以用户标准为准（提示词里明确要求）。
用户标准只属于本任务，不写入公共知识库。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

DIMENSIONS = ("HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY")
OTHER = "OTHER"
DIMENSION_LABELS = {"HOOK": "开场钩子", "STRUCTURE_RHYTHM": "结构节奏", "VALUE_DELIVERY": "价值传递", OTHER: "补充分析"}
VERDICTS = ("MET", "NOT_MET", "UNKNOWN")
VERDICT_LABELS = {"MET": "满足", "NOT_MET": "不满足", "UNKNOWN": "无法判断"}
MAX_CRITERIA = 40
# 系统能看到什么：口播转写、屏幕文字（OCR）、镜头切分统计。看不到画面内容，听不到背景音乐 / 音效 / 语气
OBSERVABILITY = ("full", "partial", "none")
OBSERVABILITY_LABELS = {"full": "可完整检查", "partial": "仅能依据口播和字幕检查", "none": "无法检查（需要看画面或听音频）"}
PARTIAL_LIMITATION = "系统看不到画面、听不到背景音乐，只能依据口播和屏幕文字判断；画面 / 音频部分无法检查"
NONE_REASON = "这条标准需要看画面或听音频才能判断，系统只能分析口播、屏幕文字和镜头切换，无法判断。"
_VISUAL_AUDIO = re.compile(r"logo|LOGO|画面|配色|颜色|着装|穿着|服装|表情|形象|背景音乐|BGM|bgm|音乐|音效|配乐|滤镜|光线|构图|美颜|贴纸|特效")
MAX_CRITERION_CHARS = 300

_BULLET = re.compile(r"^\s*(?:[-*•·●]|\d{1,2}[.、．)）]|[（(]\d{1,2}[)）]|[一二三四五六七八九十]{1,3}[、.．])\s*")
_HEADING = re.compile(r"^\s*(?:#+\s*)?(?:[一二三四五六七八九十]{1,3}[、.．]\s*)?(.{1,12})[:：]\s*$")
_SENTENCE_SPLIT = re.compile(r"[；;]\s*|。(?=\S)")

# 关键词兜底归类：按顺序匹配，开场优先（"开头 3 秒说出卖点"属于开场钩子）
_KEYWORDS: list[tuple[str, re.Pattern[str]]] = [
  ("HOOK", re.compile(r"开头|开场|片头|首屏|前\s*[0-9一二三四五六七八九十]+\s*秒|钩子|第一句|封面")),
  ("STRUCTURE_RHYTHM", re.compile(r"节奏|镜头|转场|剪辑|切换|结构|段落|分段|步骤|时长|拖沓|信息密度|字幕")),
  ("VALUE_DELIVERY", re.compile(r"收益|价值|卖点|好处|结尾|行动|关注|收藏|下单|购买|直播间|引导|证明|案例|对比|效果|数据|干货")),
]


# ---------------------------------------------------------------- 拆分 / 归类


def criteria_input(job_context: dict[str, Any]) -> tuple[str, bool]:
  """从任务输入快照里取出用户标准原文和"整体补充分析"开关。"""
  raw = job_context.get("inputSnapshotJson") or job_context.get("inputSnapshot") or {}
  if isinstance(raw, str):
    try:
      raw = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
      raw = {}
  if not isinstance(raw, dict):
    raw = {}
  text = str(raw.get("criteriaText") or "").strip()
  return text, bool(raw.get("supplementaryAnalysis"))


def split_criteria(text: str) -> list[dict[str, Any]]:
  """规则拆分：每行一条（去掉编号），一行里用分号隔开的再拆；"开场：" 这类小标题作为后续条目的分组提示。"""
  items: list[dict[str, Any]] = []
  section = ""
  for line in (text or "").splitlines():
    stripped = line.strip()
    if not stripped:
      continue
    heading = _HEADING.match(stripped)
    if heading and not _BULLET.match(stripped):
      section = heading.group(1).strip()
      continue
    body = _BULLET.sub("", stripped).strip()
    for part in _SENTENCE_SPLIT.split(body):
      part = part.strip(" 。.\t")
      if len(part) >= 2:
        items.append({"text": part[:MAX_CRITERION_CHARS], "section": section})
  for index, item in enumerate(items[:MAX_CRITERIA], start=1):
    item["id"] = f"U{index}"
  return items[:MAX_CRITERIA]


def classify_by_keywords(text: str, section: str = "") -> str:
  if re.search(r"其他|其它|补充|合规|品牌", section):
    return OTHER
  for dimension, pattern in _KEYWORDS:
    if pattern.search(f"{section} {text}"):
      return dimension
  return OTHER


CRITERIA_PARSE_PROMPT = """
你在帮短视频对比诊断系统整理用户上传的评分标准（输入 criteriaText，格式任意：可能是列表、段落、带小标题的文档）。

系统有三个分析专家：
- HOOK：开场钩子（前几秒、开头说了什么、第一印象）
- STRUCTURE_RHYTHM：结构节奏（段落 / 步骤、镜头切换、剪辑节奏、时长、字幕分段）
- VALUE_DELIVERY：价值传递（收益 / 卖点表达、结果证明、结尾行动号召）
不属于这三类的（例如品牌露出、禁用词、合规、背景音乐、人物形象、画面风格）归为 OTHER。

要求：
1. 拆成一条条可以单独对照视频检查的标准。一句话里包含多个独立要求时拆开；同一个要求的补充说明合并在同一条里。
2. text：保留用户原话（从原文里截取，不要改写、不要编造）。
3. 小标题、背景介绍、和视频本身无关的话（例如"请帮我看看"）不算标准，不要输出。
4. 不要遗漏用户的任何要求，也不要新增用户没提的要求。
5. dimension：从 HOOK / STRUCTURE_RHYTHM / VALUE_DELIVERY / OTHER 中选一个。
6. check：把这条标准改写成一句可以对照视频检查的话（写清看哪里、看什么），不改变用户的意思。
7. 系统能看到的只有：口播转写、屏幕文字（OCR）、镜头切换的时间和统计。看不到画面内容（人物、logo、配色、商品外观），
   听不到背景音乐、音效和语气。observability 标明这条能检查到什么程度：
   - full：只靠口播 / 屏幕文字 / 镜头数据就能完整判断；
   - partial：一部分能判断，另一部分要看画面或听音频（例如"不能出现竞品"——口播和字幕能查，画面里的 logo 查不到）；
   - none：完全要看画面或听音频（例如"背景音乐要轻快""人物要穿正装"）。
   check 只能写系统能检查的部分，不要写"看画面"；partial 时在 check 末尾注明"（画面 / 音频部分无法检查）"。

只输出 JSON（不要 markdown 代码块），按原文顺序：
{"items": [{"text": "开头3秒说出卖点", "dimension": "HOOK", "check": "前 3 秒内口播或字幕说出产品卖点", "observability": "full"}]}
""".strip()


def parse_with_llm(text: str, invoke: Any) -> list[dict[str, Any]]:
  """模型一次完成拆分 + 归类 + 检查口径；输出不合法的条目丢弃，全部不合法时返回 []（调用方退回规则）。"""
  from agent_service.harness.context import call_model
  from agent_service.llm.diagnosis_llm import _extract_json

  _, parsed = call_model(
    invoke,
    [
      {"role": "system", "content": CRITERIA_PARSE_PROMPT},
      {"role": "user", "content": json.dumps({"criteriaText": text}, ensure_ascii=False)},
    ],
    parse=lambda response: _extract_json(str(response.content)),
  )
  items: list[dict[str, Any]] = []
  for row in (parsed or {}).get("items") or [] if isinstance(parsed, dict) else []:
    if not isinstance(row, dict):
      continue
    item_text = str(row.get("text") or "").strip()[:MAX_CRITERION_CHARS]
    if len(item_text) < 2:
      continue
    dimension = str(row.get("dimension") or "").upper()
    classified = dimension in (*DIMENSIONS, OTHER)
    items.append({
      "text": item_text,
      "section": "",
      "dimension": dimension if classified else classify_by_keywords(item_text),
      "check": str(row.get("check") or "").strip()[:MAX_CRITERION_CHARS] or item_text,
      "classifiedBy": "llm" if classified else "keywords",
      "splitBy": "llm",
      "observability": _observability(row.get("observability"), item_text),
      # 模型应当逐字截取原文；没在原文里找到时标记出来，报告里能看出这条是模型概括的
      "verbatim": _compact(item_text) in _compact(text),
    })
  return items[:MAX_CRITERIA]


def _observability(value: Any, text: str) -> str:
  normalized = str(value or "").strip().lower()
  if normalized in OBSERVABILITY:
    return normalized
  return "partial" if _VISUAL_AUDIO.search(text) else "full"


def _compact(value: str) -> str:
  return re.sub(r"[\s，。、,.;；:：!！?？\"“”'‘’（）()\-*•·]", "", value)


def parse_user_criteria(text: str, *, use_llm: bool) -> list[dict[str, Any]]:
  """
  有模型时：模型一次完成拆分、归类和检查口径（用户可能写的是一整段话，按行拆不准）；
  模型调用失败或输出不可用时：退回规则拆分 + 关键词归类。``splitBy`` / ``classifiedBy`` 标明每条的来源。
  """
  if not (text or "").strip():
    return []
  items: list[dict[str, Any]] = []
  if use_llm:
    try:
      from agent_service.llm.provider import get_chat_model

      items = parse_with_llm(text, get_chat_model().invoke)
    except Exception as exc:  # noqa: BLE001 - 解析失败退回规则，不影响诊断
      logger.warning("criteria_parse_failed error=%s", exc)
      items = []
  if not items:
    items = split_criteria(text)
    for item in items:
      item["dimension"] = classify_by_keywords(item["text"], item.get("section", ""))
      item["check"] = item["text"]
      item["classifiedBy"] = "keywords"
      item["splitBy"] = "rules"
      item["verbatim"] = True
      # 规则分不清"部分"还是"完全"需要画面：保守标为 partial，由节点依据口播 / 字幕判断并说明局限
      item["observability"] = _observability(None, item["text"])
  for index, item in enumerate(items, start=1):
    item["id"] = f"U{index}"
    item["dimensionLabel"] = DIMENSION_LABELS[item["dimension"]]
    item["observabilityLabel"] = OBSERVABILITY_LABELS[item["observability"]]
    if item["observability"] == "partial" and "无法检查" not in item["check"]:
      item["check"] = f"{item['check']}（画面 / 音频部分无法检查）"
  return items


def criterion_payload(item: dict[str, Any]) -> dict[str, Any]:
  """交给模型的单条标准；只能部分检查的附上局限说明。"""
  row = {"id": item["id"], "text": item["text"], "check": item.get("check") or item["text"]}
  if item.get("observability") == "partial":
    row["limitation"] = PARTIAL_LIMITATION
  return row


def criteria_for_dimension(criteria: list[dict[str, Any]], dimension: str) -> list[dict[str, Any]]:
  """分给某个节点的标准；完全需要画面 / 音频的（observability=none）不交给任何节点，报告里直接标"无法判断"。"""
  return [
    item for item in criteria if item.get("dimension") == dimension and item.get("observability", "full") != "none"
  ]


def normalize_verdicts(raw: Any) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for item in raw if isinstance(raw, list) else []:
    if not isinstance(item, dict) or not item.get("id"):
      continue
    verdict = str(item.get("verdict") or "UNKNOWN").upper()
    rows.append({
      "id": str(item["id"]).strip(),
      "verdict": verdict if verdict in VERDICTS else "UNKNOWN",
      "reason": str(item.get("reason") or "").strip(),
      "suggestion": str(item.get("suggestion") or "").strip(),
      "evidence": [str(ref) for ref in item.get("evidence") or item.get("quote_refs") or [] if str(ref).strip()],
    })
  return rows


def verdict_coverage(assigned_ids: list[str], verdicts: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
  """返回 (缺少回应的标准, 回应了但不是分给自己的标准)。"""
  answered = [row["id"] for row in verdicts]
  return [item for item in assigned_ids if item not in answered], [item for item in answered if item not in assigned_ids]


# ---------------------------------------------------------------- 报告


def build_criteria_report(
  criteria: list[dict[str, Any]],
  findings: list[dict[str, Any]],
  supplementary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
  """逐条对照：每条用户标准一行；没有被回应的标记为 UNKNOWN（未覆盖），不静默丢掉。"""
  answers: dict[str, dict[str, Any]] = {}
  for finding in findings:
    for row in finding.get("criteria_verdicts") or []:
      answers.setdefault(row["id"], {**row, "answeredBy": finding.get("skill_key") or finding.get("dimension")})
  for row in (supplementary or {}).get("verdicts") or []:
    answers.setdefault(row["id"], {**row, "answeredBy": "supplementary_analysis"})
  report = []
  for item in criteria:
    answer = answers.get(item["id"])
    if answer is None and item.get("observability") == "none":
      answer = {"verdict": "UNKNOWN", "reason": NONE_REASON, "suggestion": "", "evidence": [], "answeredBy": "system"}
    report.append({
      "id": item["id"],
      "text": item["text"],
      "check": item.get("check") or item["text"],
      "dimension": item["dimension"],
      "dimensionLabel": DIMENSION_LABELS[item["dimension"]],
      "observability": item.get("observability", "full"),
      "verdict": answer["verdict"] if answer else "UNKNOWN",
      "verdictLabel": VERDICT_LABELS[answer["verdict"]] if answer else "未覆盖",
      "reason": answer["reason"] if answer else "没有节点回应这条标准。",
      "suggestion": answer.get("suggestion", "") if answer else "",
      "evidence": answer.get("evidence", []) if answer else [],
      "answeredBy": answer.get("answeredBy", "") if answer else "",
    })
  return report


def apply_criteria_to_synthesis(synthesis: dict[str, Any], report: list[dict[str, Any]]) -> dict[str, Any]:
  """
  用户标准优先：不满足的标准排在改进优先级最前面，总结开头写明标准满足情况。

  改造前优先级只看三个维度与参考的对比：目标在某维度比参考强（例如参考结尾也没有行动号召），
  即使用户明确要求的标准没满足，总结仍会写"没有需要优先改进的问题"，与逐条对照自相矛盾。
  """
  if not report:
    return synthesis
  unmet = [row for row in report if row["verdict"] == "NOT_MET"]
  unknown = [row for row in report if row["verdict"] == "UNKNOWN"]
  met = [row for row in report if row["verdict"] == "MET"]

  criteria_priorities = [
    {
      "source": "user_criteria",
      "criterionId": row["id"],
      "skillKey": f"user_criteria:{row['id']}",
      "dimension": row["dimension"],
      "findingType": "user_criterion_not_met",
      "suggestedAction": row.get("suggestion") or f"按标准修改：{row['check']}",
      "confidence": 1.0,
      "rationale": f"未满足你的标准 {row['id']}「{row['text']}」：{row['reason']}",
    }
    for row in unmet
  ]
  dimension_priorities = [dict(item) for item in synthesis.get("priorities") or []]
  priorities = [*criteria_priorities, *dimension_priorities]
  for index, item in enumerate(priorities, start=1):
    item["rank"] = index

  parts = [f"你的 {len(report)} 条标准：满足 {len(met)} 条"]
  if unmet:
    parts.append(f"不满足 {len(unmet)} 条（" + "、".join(f"{row['id']} {row['text']}" for row in unmet) + "）")
  if unknown:
    parts.append(f"无法判断 {len(unknown)} 条（" + "、".join(f"{row['id']} {row['text']}" for row in unknown) + "）")
  criteria_sentence = "，".join(parts) + "。"
  if unmet:
    criteria_sentence += "建议优先处理未满足的标准。"

  dimension_summary = str(synthesis.get("summary") or "")
  if unmet and not dimension_priorities:
    # 规则总结在没有维度差距时写的是"没有需要优先改进的问题"，有未满足的用户标准时会自相矛盾
    dimension_summary = dimension_summary.replace("没有需要优先改进的问题", "三个维度上没有明显差距")
  return {
    **synthesis,
    "summary": criteria_sentence + ("与参考视频相比：" + dimension_summary if dimension_summary else ""),
    "dimensionSummary": synthesis.get("summary") or "",
    "priorities": priorities,
    "mergedActions": [item["suggestedAction"] for item in criteria_priorities] + list(synthesis.get("mergedActions") or []),
    "criteriaSummary": {"total": len(report), "met": len(met), "notMet": len(unmet), "unknown": len(unknown)},
  }


def render_report_markdown(synthesis: dict[str, Any], findings: list[dict[str, Any]]) -> str:
  lines = ["# 短视频对比诊断报告", ""]
  if synthesis.get("summary"):
    lines += ["## 总结", "", str(synthesis["summary"]), ""]

  criteria = list(synthesis.get("criteria") or [])
  report = list(synthesis.get("criteriaReport") or [])
  if criteria:
    lines += ["## 解析出的评分标准", "", "| 编号 | 原文 | 归属 | 检查口径 | 可检查范围 |", "|---|---|---|---|---|"]
    lines += [
      f"| {item['id']} | {_cell(item['text'])} | {item['dimensionLabel']} | {_cell(item.get('check') or '')} | "
      f"{OBSERVABILITY_LABELS.get(item.get('observability', 'full'), '')} |"
      for item in criteria
    ]
    if any(item.get("observability", "full") != "full" for item in criteria):
      lines += ["", (
        "说明：系统能分析的是口播转写、屏幕文字和镜头切换，看不到画面内容、听不到背景音乐；"
        "涉及画面 / 音频的部分无法检查，结果仅依据口播和字幕。"
      )]
    lines += ["", "## 逐条对照", "", "| 编号 | 标准 | 结果 | 依据 |", "|---|---|---|---|"]
    lines += [
      f"| {row['id']} | {_cell(row['text'])} | {row['verdictLabel']}"
      + ("（仅依据口播和字幕）" if row.get("observability") == "partial" and row["verdict"] != "UNKNOWN" else "")
      + f" | {_cell(row['reason'])} |"
      for row in report
    ]
    counts = {label: sum(1 for row in report if row["verdictLabel"] == label) for label in ("满足", "不满足", "无法判断", "未覆盖")}
    lines += ["", "合计：" + "，".join(f"{label} {count}" for label, count in counts.items() if count), ""]

  priorities = list(synthesis.get("priorities") or [])
  if priorities:
    lines += ["## 改进优先级", ""]
    for index, item in enumerate(priorities, start=1):
      if isinstance(item, str):
        lines.append(f"{index}. {item}")
        continue
      label = DIMENSION_LABELS.get(str(item.get("dimension")), str(item.get("dimension") or ""))
      if item.get("source") == "user_criteria":
        # 依据已经在逐条对照表里，这里只写改法
        lines.append(f"{index}. 【你的标准 {item.get('criterionId')}】{item.get('suggestedAction') or ''}")
      else:
        lines.append(f"{index}. 【{label}】{item.get('suggestedAction') or item.get('rationale') or ''}")
    lines.append("")

  lines += ["## 三个维度的结论", ""]
  for finding in findings:
    label = DIMENSION_LABELS.get(str(finding.get("dimension")), str(finding.get("dimension")))
    polarity = {"GAP": "差距", "STRENGTH": "优势", "PARITY": "相当"}.get(str(finding.get("polarity") or ""), "")
    lines.append(f"### {label}" + (f"（{polarity}）" if polarity else ""))
    for key, title in (("observation", "观察"), ("difference_text", "与参考的差异"), ("suggested_action", "建议")):
      if finding.get(key):
        lines.append(f"- **{title}**：{finding[key]}")
    lines.append("")

  supplementary = synthesis.get("supplementary") or {}
  notes = list(supplementary.get("notes") or [])
  if notes:
    lines += ["## 补充分析", ""]
    for note in notes:
      lines.append(f"- **{note.get('title') or '补充'}**：{note.get('observation') or ''}")
    lines.append("")
  return "\n".join(lines).rstrip() + "\n"


def _cell(text: str) -> str:
  return str(text or "").replace("|", "\\|").replace("\n", " ")
