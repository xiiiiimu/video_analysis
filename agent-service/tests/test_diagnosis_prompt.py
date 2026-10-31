from __future__ import annotations

import dataclasses

import pytest

from agent_service.config import get_settings
from agent_service.llm.diagnosis_llm import _build_user_payload, render_dimension_system_prompt


def _use_rules(monkeypatch: pytest.MonkeyPatch, version: str) -> None:
  settings = dataclasses.replace(get_settings(), quality_rules=version)
  monkeypatch.setattr("agent_service.llm.diagnosis_llm.get_settings", lambda: settings)


def test_dimension_prompt_keeps_json_literal_and_replaces_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
  _use_rules(monkeypatch, "v1")
  prompt = render_dimension_system_prompt("HOOK")

  assert "正在分析维度：HOOK" in prompt
  assert '"finding_type": "稳定的 snake_case 诊断类型；不确定时使用 evidence_gap 或 unknown"' in prompt
  assert '"observation": "客观观察（1-2句）"' in prompt
  assert '"handoff_requests"' in prompt
  assert '"target_frame_refs": ["FRAME:T@00:00:01", "FRAME:T@00:00:03"]' in prompt


def test_v2_prompt_requires_polarity_quotes_and_taxonomy(monkeypatch: pytest.MonkeyPatch) -> None:
  _use_rules(monkeypatch, "v2")
  prompt = render_dimension_system_prompt("VALUE_DELIVERY")

  assert "正在分析维度：VALUE_DELIVERY" in prompt
  assert '"polarity": "GAP | STRENGTH | PARITY"' in prompt
  assert '"quotes"' in prompt
  assert "value_late（收益出现太晚）" in prompt
  assert "{taxonomy}" not in prompt and "{dimension}" not in prompt


def test_skill_procedure_with_braces_is_not_formatted() -> None:
  skill_procedure = 'Use snapshot rule with literal JSON: {"step": "{do_not_format}"}'

  payload = _build_user_payload(
    "HOOK",
    {"jobId": "job-1", "targetVideoId": "target-1"},
    {
      "targetEvidence": {
        "videoAssetId": "target-1",
        "transcriptText": "前三秒直接给出痛点",
        "keyframes": ["FRAME:target-1"],
        "sceneJson": "{}",
        "ocrJson": "痛点",
      },
      "referenceEvidence": [],
    },
    skill_procedure,
  )

  assert payload["skillProcedure"] == skill_procedure
  assert "{do_not_format}" in payload["skillProcedure"]


@pytest.mark.quality_v2
def test_lite_prompt_drops_hardcoded_definitions_but_keeps_the_output_contract(monkeypatch: pytest.MonkeyPatch) -> None:
  from agent_service.config import get_settings
  from agent_service.llm.diagnosis_llm import render_dimension_system_prompt

  full = render_dimension_system_prompt("VALUE_DELIVERY")
  monkeypatch.setenv("PROMPT_PROFILE", "lite")
  get_settings.cache_clear()
  lite = render_dimension_system_prompt("VALUE_DELIVERY")
  assert "概念定义" in full and "概念定义" not in lite
  assert "first_benefit_seconds" in lite and "{concept_definitions}" not in lite
