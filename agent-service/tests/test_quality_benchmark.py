"""mock 评测本身的测试：评测集合法、打分规则正确、在假 LLM 下能端到端跑通。"""

from __future__ import annotations

from typing import Any

import pytest

from agent_service.eval.quality_benchmark import aggregate, render_markdown, run_case, score_case
from agent_service.eval.quality_cases import ISSUE_TYPES, build_cases
from agent_service.graph.diagnosis_skill import known_evidence_refs

CASES = {case.case_id: case for case in build_cases()}


def test_cases_are_well_formed() -> None:
  assert len(CASES) >= 15
  for case in CASES.values():
    pack = case.evidence_pack()
    assert "FRAME:T@00:00:00" in known_evidence_refs(pack)
    assert set(case.expected).isdisjoint(case.forbidden)
    for issue in [*case.expected, *case.forbidden]:
      assert issue in ISSUE_TYPES
  # 至少有"目标更好"和"两者相当"的样本，用来测误报
  assert any(case.strength_dims for case in CASES.values())
  assert any(not case.expected for case in CASES.values())


def test_score_uses_type_first_and_keywords_as_v1_fallback() -> None:
  case = CASES["c11_contradiction_bait"]
  v2_style = [{"dimension": "HOOK", "polarity": "GAP", "finding_type": "hook_weak_visual_text", "observation": "开场缺少收益承诺"}]
  v1_style = [{"dimension": "HOOK", "finding_type": "unknown", "observation": "开场缺乏价值预期，观众没有兴趣"}]

  assert score_case(case, v2_style)["hits"] == ["hook_weak_visual_text"]
  assert score_case(case, v2_style)["falseAlarms"] == []  # 有类型时不再按关键词误判
  assert score_case(case, v1_style)["falseAlarms"] == ["hook_no_value_promise"]


def test_strength_reported_as_gap_counts_as_misreport() -> None:
  case = CASES["c09_strength_hook"]
  assert score_case(case, [{"dimension": "HOOK", "polarity": "GAP", "finding_type": "other"}])["strengthMisreported"] == ["HOOK"]
  assert score_case(case, [{"dimension": "HOOK", "polarity": "STRENGTH", "finding_type": "strength"}])["strengthMisreported"] == []


@pytest.mark.quality_v2
def test_benchmark_runs_end_to_end_with_fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
  answers = {
    "HOOK": {"polarity": "GAP", "finding_type": "hook_no_value_promise", "target_score": 2, "reference_scores": {"R1": 4},
             "quotes": [{"ref": "ASR:T@00:00:00", "text": "大家好，我是小王，今天天气不错"},
                        {"ref": "ASR:R1@00:00:00", "text": "三个技巧，让你的早餐五分钟就能做好"}]},
    "STRUCTURE_RHYTHM": {"polarity": "PARITY", "finding_type": "parity", "evidence_refs": ["SCENE:T#2"], "quotes": [],
                         "target_score": 3, "reference_scores": {"R1": 3}},
    "VALUE_DELIVERY": {"polarity": "PARITY", "finding_type": "parity", "target_score": 3, "reference_scores": {"R1": 3},
                       "quotes": [{"ref": "ASR:T@00:01:05", "text": "这样做之后我每天早上只花五分钟"}]},
  }

  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any], **_: Any) -> dict[str, Any]:
    return {"outcome": "FINDING", "dimension": dimension, "observation": "obs", "suggested_action": "保持",
            "target_frame_refs": [], "reference_frame_refs": [], "evidence_refs": [], "confidence": 0.8, **answers[dimension]}

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  run = run_case(CASES["c01_hook_no_promise"])

  assert run["status"] == "success"
  assert run["score"]["hits"] == ["hook_no_value_promise"]
  assert run["score"]["falseAlarms"] == []
  assert run["score"]["invalidRefs"] == 0
  assert {item["dimension"] for item in run["attempts"]} == {"HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY"}
  assert run["abstained"] == []
  summary = aggregate([run])
  assert summary["issueRecall"] == 1.0
  assert summary["abstainRate"] == 0.0
  report = {"finishedAt": "now", "model": "fake", "caseCount": 1, "repeat": 1,
            "cases": {"c01_hook_no_promise": {"expected": ["hook_no_value_promise"], "strengthDims": []}},
            "results": {"v2": {"summary": {**summary, "stability": None}, "runs": [run]}}}
  assert "预埋问题命中率" in render_markdown(report)


def test_hard_group_exists_and_is_selectable() -> None:
  hard = [case for case in CASES.values() if case.group == "hard"]
  assert len(hard) >= 7
  assert all(case.case_id >= "c20" for case in hard)
  # 多个预埋问题、多个参考、无预埋问题（边界）都要有
  assert any(len(case.expected) >= 2 for case in hard)
  assert any(len(case.references) >= 2 for case in hard)
  assert any(not case.expected for case in hard)


def test_uneven_pacing_case_sits_inside_same_pacing_tolerance() -> None:
  """c23 刻意让平均镜头时长落在 15% 以内：用来测 same_pacing 不能只看平均值。"""
  from agent_service.graph.evidence_timeline import scene_stats

  case = CASES["c23_cooking_uneven_pacing"]
  target = scene_stats(case.target, "T")
  reference = scene_stats(case.references[0], "R1")
  assert abs(target["avgShotSeconds"] - reference["avgShotSeconds"]) / reference["avgShotSeconds"] <= 0.15
  assert target["shotsUnder2s"] >= 10 and target["longestShot"]["seconds"] >= 30


def test_accept_alternatives_count_as_hit() -> None:
  case = CASES["c23_cooking_uneven_pacing"]
  slow = [{"dimension": "STRUCTURE_RHYTHM", "polarity": "GAP", "finding_type": "pacing_too_slow", "observation": "x"}]
  assert score_case(case, slow)["hits"] == ["pacing_too_dense"]
  assert score_case(case, [])["hits"] == []


def test_model_account_error_fails_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
  """余额不足时 run 必须失败（stop_reason=model_fatal），不能再显示 success + 空结果。"""
  from agent_service.config import get_settings

  class APIStatusError(Exception):
    status_code = 429

  class Broke:
    def invoke(self, messages: Any) -> Any:
      raise APIStatusError("Error code: 429 - You have no credits remaining.")

  monkeypatch.setenv("LLM_MOCK", "0")
  monkeypatch.setenv("CHAT_API_KEY", "sk-test")
  get_settings.cache_clear()
  monkeypatch.setattr("agent_service.llm.provider.get_chat_model", lambda: Broke())
  try:
    run = run_case(CASES["c01_hook_no_promise"])
  finally:
    get_settings.cache_clear()
  assert run["status"] == "failed"
  assert run["stopReason"] == "model_fatal"
  assert "no credits" in run["error"]


def test_stability_compares_only_direction_for_non_gap_findings() -> None:
  from agent_service.eval.quality_benchmark import stability

  def run(observation: str) -> dict[str, Any]:
    row = {"dimension": "HOOK", "polarity": "PARITY", "findingType": "parity", "observation": observation,
           "differenceText": "", "suggestedAction": ""}
    return {"caseId": "c", "status": "success", "findings": [row]}

  # 两次都是"相当"，措辞不同（一次提到字幕）不应算成不一致
  counts: dict[str, list[int]] = {}
  stability([run("开场相同"), run("开场字幕相同")], counts)
  assert counts["stability"][0] == counts["stability"][1]


def test_retries_are_not_rendered_as_percent() -> None:
  from agent_service.eval.quality_benchmark import _fmt

  assert _fmt(0.47) == "0.47"
  assert _fmt(0.47, percent=True) == "47%"
