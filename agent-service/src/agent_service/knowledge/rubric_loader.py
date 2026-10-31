"""
从 md 文件加载诊断评分点（内置知识库）。

目录结构（默认 ``agent-service/knowledge/rubric``，Docker 里由 ``RUBRIC_DIR`` 指定并挂载）::

    hook.md / structure_rhythm.md / value_delivery.md

每个文件开头的 front matter 写 ``skill: hook_analysis``（或 ``skill: mixed``，每条再写 ``- skill:``）；
每条评分点是一个 ``## 标题`` 小节，紧跟几行 ``- 字段: 值``（id / type 必填，tags / focus / group / category 可选），
之后的段落是判定重点。写了 ``category`` 的评分点只对同品类的任务生效（私有规范）。
格式错误直接抛 ``RubricFormatError``，指出文件和行号：写错一条不能让检索静默失效。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from agent_service.retrieval.models import KnowledgeEvidence

logger = logging.getLogger(__name__)

SKILLS = ("hook_analysis", "structure_rhythm_analysis", "value_delivery_analysis")
_PATTERN_TYPE = {
  "hook_analysis": "HOOK_PATTERN",
  "structure_rhythm_analysis": "STRUCTURE_PATTERN",
  "value_delivery_analysis": "VALUE_DELIVERY_PATTERN",
}
_TYPE_ALIASES = {
  "规则": "ANALYSIS_RULE",
  "好例": "GOOD_CASE",
  "反例": "BAD_CASE",
  "平台规则": "PLATFORM_GUIDELINE",
  "品类最佳实践": "CATEGORY_BEST_PRACTICE",
}
_CODES = {"HOOK_PATTERN", "STRUCTURE_PATTERN", "VALUE_DELIVERY_PATTERN", *_TYPE_ALIASES.values()}
_FIELD = re.compile(r"^-\s*([A-Za-z_]+)\s*[:：]\s*(.*)$")


MIXED = "mixed"


class RubricFormatError(ValueError):
  pass


def default_rubric_dir() -> Path:
  # 源码布局：agent-service/src/agent_service/knowledge/rubric_loader.py → agent-service/knowledge/rubric
  return Path(__file__).resolve().parents[3] / "knowledge" / "rubric"


def load_rubric_dir(directory: str | Path) -> list[KnowledgeEvidence]:
  path = Path(directory)
  files = sorted(path.glob("*.md"))
  if not files:
    raise RubricFormatError(f"评分点目录 {path} 下没有 .md 文件")
  items: list[KnowledgeEvidence] = []
  for file in files:
    items.extend(parse_rubric_file(file))
  seen: dict[str, str] = {}
  for item in items:
    if item.id in seen:
      raise RubricFormatError(f"评分点 id 重复：{item.id}（{seen[item.id]} 与 {item.metadata['source_file']}）")
    seen[item.id] = str(item.metadata["source_file"])
  return items


def parse_rubric_file(file: Path) -> list[KnowledgeEvidence]:
  lines = file.read_text(encoding="utf-8").splitlines()
  skill, body_start = _front_matter(file, lines)
  items: list[KnowledgeEvidence] = []
  current: dict[str, object] | None = None

  def flush() -> None:
    if current is not None:
      items.append(_build(file, skill, current))

  for number, raw in enumerate(lines[body_start:], start=body_start + 1):
    line = raw.strip()
    if raw.startswith("## "):
      flush()
      current = {"title": raw[3:].strip(), "line": number, "fields": {}, "content": []}
      continue
    if current is None:
      continue  # 第一条评分点之前的说明文字
    match = _FIELD.match(line)
    if match and not current["content"]:
      value = re.split(r"\s+#", match.group(2), maxsplit=1)[0]  # 允许行尾 "# 注释"
      current["fields"][match.group(1).lower()] = value.strip()  # type: ignore[index]
    elif line:
      current["content"].append(line)  # type: ignore[union-attr]
  flush()
  if not items:
    raise RubricFormatError(f"{file.name}：没有任何 `## 标题` 评分点")
  return items


def _front_matter(file: Path, lines: list[str]) -> tuple[str, int]:
  if not lines or lines[0].strip() != "---":
    raise RubricFormatError(f"{file.name}:1 缺少 front matter（第一行应为 ---，并写 skill: hook_analysis 等）")
  meta: dict[str, str] = {}
  for index in range(1, len(lines)):
    if lines[index].strip() == "---":
      skill = meta.get("skill", "")
      # mixed：一个文件里放多个维度的评分点（例如某个品类的私有规范），每条用 `- skill:` 指定维度
      if skill not in (*SKILLS, MIXED):
        raise RubricFormatError(
          f"{file.name}: front matter 的 skill 必须是 {', '.join(SKILLS)} 或 {MIXED}，当前为「{skill}」"
        )
      return skill, index + 1
    key, _, value = lines[index].partition(":")
    meta[key.strip()] = value.strip()
  raise RubricFormatError(f"{file.name}: front matter 没有结束的 ---")


def _build(file: Path, skill: str, block: dict[str, object]) -> KnowledgeEvidence:
  fields: dict[str, str] = block["fields"]  # type: ignore[assignment]
  where = f"{file.name}:{block['line']}「{block['title']}」"
  item_id = fields.get("id", "")
  if not item_id:
    raise RubricFormatError(f"{where} 缺少 `- id:`")
  if skill == MIXED:
    skill = fields.get("skill", "")
    if skill not in SKILLS:
      raise RubricFormatError(f"{where} 所在文件是 mixed，必须写 `- skill:`（{' / '.join(SKILLS)}）")
  raw_type = fields.get("type", "")
  knowledge_type = _PATTERN_TYPE[skill] if raw_type == "模式" else _TYPE_ALIASES.get(raw_type, raw_type)
  if knowledge_type not in _CODES:
    raise RubricFormatError(f"{where} 的 type「{raw_type}」无效，可选：模式 / {' / '.join(_TYPE_ALIASES)}")
  content = " ".join(block["content"])  # type: ignore[arg-type]
  if not content:
    raise RubricFormatError(f"{where} 没有判定重点正文")
  group = [part.strip() for part in fields.get("group", "").split(",") if part.strip()]
  return KnowledgeEvidence(
    id=item_id,
    knowledge_type=knowledge_type,
    skill_code=skill,
    # 品类专属评分点（例如某平台 / 某企业的私有规范）：只对 category 相同的任务生效
    category=fields.get("category", ""),
    title=str(block["title"]),
    content=content,
    source=f"rubric/{file.name}",
    tags=[part.strip() for part in fields.get("tags", "").split(",") if part.strip()],
    version="md",
    created_at="",
    metadata={
      "diagnosticFocus": fields.get("focus", ""),
      "confusionGroup": group[0] if len(group) == 1 else group,
      "source_file": file.name,
    },
  )
