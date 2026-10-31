"""内置评分点 md 文件：内容与检索评测的冻结快照一致、格式错误能指出位置、Golden Query 引用的 id 都还在。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_service.knowledge import diagnosis_rubric_corpus, load_benchmark_corpus
from agent_service.knowledge.rubric_loader import (
  RubricFormatError,
  default_rubric_dir,
  load_rubric_dir,
)

BENCHMARKS = Path(__file__).resolve().parents[1] / "benchmarks"


def _key(item):
  return (item.knowledge_type, item.skill_code, item.title, item.content, tuple(item.tags))


def test_md_rubric_matches_frozen_v03_snapshot() -> None:
  items = load_rubric_dir(default_rubric_dir())
  md = {item.id: _key(item) for item in items if not item.category}
  frozen = {item.id: _key(item) for item in load_benchmark_corpus("v0.3")}
  assert md == frozen  # 通用评分点：迁移只换了存放位置，内容不变
  assert len([item for item in diagnosis_rubric_corpus() if not item.category]) == 34
  private = [item for item in items if item.category]
  assert len(private) == 5 and {item.category for item in private} == {"知识教程"}


def test_category_rubric_only_applies_to_matching_jobs_and_is_always_included() -> None:
  from agent_service.retrieval import InMemoryHybridKnowledgeRetriever, KnowledgeQuery

  retriever = InMemoryHybridKnowledgeRetriever(diagnosis_rubric_corpus())
  general = retriever.retrieve(KnowledgeQuery("开头 收益", "hook_analysis", "RUBRIC", category="", top_k=6))
  assert not any(item.category for item in general.items)
  edu = retriever.retrieve(KnowledgeQuery("开头 收益", "hook_analysis", "RUBRIC", category="知识教程", top_k=6))
  ids = [item.id for item in edu.items]
  assert ids[:2] == ["private-edu-hook-title-2s-v1", "private-edu-hook-no-question-v1"] and len(ids) == 8
  other = retriever.retrieve(KnowledgeQuery("开头 收益", "hook_analysis", "RUBRIC", category="美妆", top_k=6))
  assert not any(item.category for item in other.items)


def test_mixed_file_requires_skill_per_item(tmp_path: Path) -> None:
  (tmp_path / "p.md").write_text("---\nskill: mixed\n---\n## x\n- id: a\n- type: 规则\n\n正文\n", encoding="utf-8")
  with pytest.raises(RubricFormatError, match="必须写 `- skill:`"):
    load_rubric_dir(tmp_path)


def test_golden_queries_still_point_to_existing_rubric_items() -> None:
  """改 md 时如果删掉或改了被 Golden Query 标注的 id，这里会提醒（检索评测本身用冻结快照，不受影响）。"""
  ids = {item.id for item in diagnosis_rubric_corpus()}
  missing = set()
  for name in ("retrieval_golden_dev.v0.5.json", "retrieval_golden_test.v0.5.json"):
    for case in json.loads((BENCHMARKS / name).read_text(encoding="utf-8"))["cases"]:
      missing |= set(case.get("expectedKnowledgeIds") or []) - ids
  assert not missing, f"Golden Query 引用的评分点在 md 里不存在：{sorted(missing)}"


def _write(tmp_path: Path, body: str, skill: str = "hook_analysis") -> Path:
  (tmp_path / "hook.md").write_text(f"---\nskill: {skill}\n---\n\n# 说明\n\n- id：这是说明，不是评分点\n\n{body}", encoding="utf-8")
  return tmp_path


def test_new_item_is_loaded_and_chinese_type_is_mapped(tmp_path: Path) -> None:
  items = load_rubric_dir(_write(tmp_path, "## 开头露出品牌\n- id: hook-rule-brand-v1\n- type: 规则\n- tags: 品牌, logo\n\n前三秒内出现品牌名或 logo。\n"))
  assert len(items) == 1
  assert (items[0].id, items[0].knowledge_type, items[0].skill_code, items[0].tags) == (
    "hook-rule-brand-v1", "ANALYSIS_RULE", "hook_analysis", ["品牌", "logo"],
  )
  pattern = load_rubric_dir(_write(tmp_path, "## 模式\n- id: x\n- type: 模式\n\n正文\n"))
  assert pattern[0].knowledge_type == "HOOK_PATTERN"


@pytest.mark.parametrize(
  ("body", "skill", "message"),
  [
    ("## 无 id\n- type: 规则\n\n正文\n", "hook_analysis", "缺少 `- id:`"),
    ("## 类型错\n- id: a\n- type: 随便\n\n正文\n", "hook_analysis", "type「随便」无效"),
    ("## 没正文\n- id: a\n- type: 规则\n", "hook_analysis", "没有判定重点正文"),
    ("## 维度错\n- id: a\n- type: 规则\n\n正文\n", "cover_analysis", "skill 必须是"),
    ("## 重复\n- id: a\n- type: 规则\n\n正文\n\n## 重复2\n- id: a\n- type: 规则\n\n正文\n", "hook_analysis", "id 重复"),
  ],
)
def test_format_errors_point_to_the_item(tmp_path: Path, body: str, skill: str, message: str) -> None:
  with pytest.raises(RubricFormatError, match=message):
    load_rubric_dir(_write(tmp_path, body, skill))
