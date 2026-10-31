"""RAG 评分点：每次诊断前按维度检索知识库里的评分点，结论必须注明依据，Evaluator 校验。"""

from __future__ import annotations

from typing import Any

import pytest

from agent_service.config import get_settings
from agent_service.eval.quality_benchmark import aggregate, run_case
from agent_service.eval.quality_cases import build_cases
from agent_service.graph.nodes.evaluator import _rubric_issues
from agent_service.graph.rubric import rubric_query
from agent_service.knowledge import diagnosis_rubric_corpus
from agent_service.llm.diagnosis_llm import render_dimension_system_prompt
from agent_service.tools.adapters.knowledge_retrieval import KnowledgeRetrievalToolAdapter

CASES = {case.case_id: case for case in build_cases()}


def _titles(case_id: str, skill: str, top_k: int = 6) -> list[str]:
  result = KnowledgeRetrievalToolAdapter().retrieve_knowledge(
    query_text=rubric_query(skill, CASES[case_id].evidence_pack()),
    skill_code=skill,
    knowledge_type="RUBRIC",
    top_k=top_k,
  )
  return [item["title"] for item in result["items"]]


def test_runtime_rubric_is_the_34_scoring_points() -> None:
  corpus = [item for item in diagnosis_rubric_corpus() if not item.category]  # 通用评分点；私有规范见 private_edu.md
  assert len(corpus) == 34
  assert {item.skill_code for item in corpus} == {"hook_analysis", "structure_rhythm_analysis", "value_delivery_analysis"}


def test_rubric_retrieval_stays_in_dimension_and_follows_the_video() -> None:
  corpus = {item.title: item.skill_code for item in diagnosis_rubric_corpus()}
  titles = _titles("c04_no_cta", "value_delivery_analysis")
  assert all(corpus[title] == "value_delivery_analysis" for title in titles)
  # 目标结尾没有行动号召 → 检索到"行动号召匹配价值"；开场空镜 → 检索到"避免收益后置"
  assert "行动号召匹配价值" in titles
  assert "避免收益后置" in _titles("c02_hook_slow_start", "hook_analysis")
  assert "信息密度与画面补偿" in _titles("c07_pacing_slow", "structure_rhythm_analysis")


@pytest.mark.rag
@pytest.mark.quality_v2
def test_prompt_includes_rubric_rules_only_when_rag_is_on(monkeypatch: pytest.MonkeyPatch) -> None:
  assert "rubric_refs 必须列出" in render_dimension_system_prompt("HOOK")
  monkeypatch.setenv("RAG_MODE", "off")
  get_settings.cache_clear()
  assert "rubric_refs 必须列出" not in render_dimension_system_prompt("HOOK")


@pytest.mark.rag
@pytest.mark.quality_v2
def test_every_dimension_retrieves_rubric_and_cites_it(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setenv("LLM_MOCK", "1")
  get_settings.cache_clear()
  seen_payloads: list[dict[str, Any]] = []
  from agent_service.llm import diagnosis_llm

  original = diagnosis_llm._build_user_payload

  def spy(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = original(*args, **kwargs)
    seen_payloads.append(payload)
    return payload

  monkeypatch.setattr(diagnosis_llm, "_build_user_payload", spy)
  run = run_case(CASES["c01_hook_no_promise"])

  assert run["status"] == "success"
  # 三个维度的模型输入里都带着检索到的评分点
  assert len(seen_payloads) >= 3 and all(payload.get("rubric") for payload in seen_payloads)
  assert all(str(item["ref"]).startswith("KNOWLEDGE:") for item in seen_payloads[0]["rubric"])
  first_attempts = {item["dimension"]: item for item in run["attempts"]}
  assert set(first_attempts) == {"HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY"}
  for attempt in first_attempts.values():
    assert attempt["retrievedRubricRefs"]
    assert set(attempt["rubricRefs"]) <= set(attempt["retrievedRubricRefs"])
  assert aggregate([run])["rubricCitedRate"] == 1.0


@pytest.mark.quality_v2
def test_rag_off_does_not_retrieve(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setenv("LLM_MOCK", "1")
  get_settings.cache_clear()
  run = run_case(CASES["c01_hook_no_promise"])
  assert run["status"] == "success"
  assert all(not item["retrievedRubricRefs"] for item in run["attempts"])
  assert aggregate([run])["rubricCitedRate"] is None


@pytest.mark.rag
@pytest.mark.quality_v2
def test_evaluator_requires_valid_rubric_refs() -> None:
  base = {"skill_key": "hook_analysis", "retrieved_rubric_refs": ["KNOWLEDGE:a", "KNOWLEDGE:b"]}
  missing = _rubric_issues({**base, "rubric_refs": []})
  assert len(missing) == 1 and "没有注明依据的评分点" in missing[0][2]
  invented = _rubric_issues({**base, "rubric_refs": ["KNOWLEDGE:a"], "invalid_rubric_refs": ["KNOWLEDGE:zzz"]})
  assert len(invented) == 1 and "KNOWLEDGE:zzz" in invented[0][2]
  assert _rubric_issues({**base, "rubric_refs": ["KNOWLEDGE:a"]}) == []
  # 知识库不可用（没检索到任何评分点）时不强制
  assert _rubric_issues({"skill_key": "hook_analysis", "rubric_refs": []}) == []


def test_rag_group_dependencies_are_retrievable() -> None:
  """rag 组每道题依赖的评分点（含私有规范）都能被本题的检索 query 找出来，否则题目测的就不是"有没有 RAG"。"""
  rag_cases = [case for case in CASES.values() if case.group == "rag"]
  assert len(rag_cases) >= 20
  skill_of = {item.id: item.skill_code for item in diagnosis_rubric_corpus()}
  adapter = KnowledgeRetrievalToolAdapter()
  for case in rag_cases:
    for rubric_id in case.depends_on:
      skill = skill_of[rubric_id]
      result = adapter.retrieve_knowledge(
        query_text=rubric_query(skill, case.evidence_pack()), skill_code=skill, knowledge_type="RUBRIC",
        category=case.category, top_k=6,
      )
      assert rubric_id in [item["id"] for item in result["items"]], (case.case_id, rubric_id)


@pytest.mark.rag
@pytest.mark.quality_v2
def test_private_rubric_reaches_the_model_only_for_its_category(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setenv("LLM_MOCK", "1")
  get_settings.cache_clear()
  edu = run_case(CASES["r20_edu_follow_only_cta"])
  plain = run_case(CASES["r21_no_category_follow_only_cta"])
  assert edu["score"]["dependencies"]["retrieved"] == 1
  edu_refs = {ref for item in edu["attempts"] for ref in item["retrievedRubricRefs"]}
  plain_refs = {ref for item in plain["attempts"] for ref in item["retrievedRubricRefs"]}
  assert "KNOWLEDGE:private-edu-value-cta-keyword-v1" in edu_refs
  assert not any("private-edu" in ref for ref in plain_refs)
  assert aggregate([edu])["dependencyRetrievedRate"] == 1.0
