"""quality rules v2：原文引用、分类表、分析窗口、跨维度矛盾、优势不进改进清单、优先级与合成一致。"""

from __future__ import annotations

from typing import Any

import pytest
from test_agent_workflow import FakeGraphHarness, _harness, _skill, _tools

from agent_service.eval.quality_cases import build_cases
from agent_service.graph.evidence_timeline import ground_quotes
from agent_service.graph.nodes.evaluator import evaluator_node
from agent_service.graph.result_contract import normalize_specialist_result
from agent_service.graph.synthesis import (
  assign_priorities,
  build_rule_synthesis,
  persistable_findings,
)

pytestmark = pytest.mark.quality_v2
CONFIG = {"configurable": {"harness": FakeGraphHarness(), "harness_ctx": None}}
CASES = {case.case_id: case for case in build_cases()}


def _pack(case_id: str) -> dict[str, Any]:
  return CASES[case_id].evidence_pack()


def _finding(skill_key: str, dimension: str, **overrides: Any) -> dict[str, Any]:
  row = {
    "skill_key": skill_key,
    "dimension": dimension,
    "outcome": "FINDING",
    "polarity": "GAP",
    "finding_type": "other",
    "observation": "obs",
    "suggested_action": "把第 3 秒的内容提前",
    "evidence_refs": ["ASR:T@00:00:00"],
    "video_evidence_refs": ["ASR:T@00:00:00"],
    "cited_refs": ["ASR:T@00:00:00"],
    "grounded_quotes": [{"ref": "ASR:T@00:00:00", "text": "原文"}, {"ref": "ASR:R1@00:00:00", "text": "参考原文"}],
    "target_score": 2.0,
    "reference_scores": {"R1": 4.0},
    "confidence": 0.8,
  }
  row.update(overrides)
  return row


def _state(findings: list[dict[str, Any]], pack: dict[str, Any], **overrides: Any) -> dict[str, Any]:
  plan = [_skill(item["skill_key"]) for item in findings]
  state = {
    "run_id": "r",
    "job_id": "j",
    "plan": plan,
    "findings": findings,
    "evidence_pack": pack,
    "evidence_gaps": [],
    "handoff_requests": [],
    "handoff_answers": [],
    "dropped_handoffs": [],
    "evaluation_results": [],
    "iteration_count": 0,
    "global_replan_count": 0,
    "max_global_replans": 1,
    "skill_execution_status": {item["skill_key"]: "COMPLETED" for item in findings},
    "step_traces": [],
  }
  state.update(overrides)
  return state


# ---------------------------------------------------------------- 原文引用


def test_quotes_must_exist_verbatim_and_refs_are_corrected() -> None:
  pack = _pack("c03_value_late")
  grounded, issues = ground_quotes(
    [
      {"ref": "ASR:T@00:01:10", "text": "这样每天早上只要五分钟，能省二十分钟"},  # 原文（标点无关）
      {"ref": "ASR:T@00:00:00", "text": "省20分钟"},  # 实际是 OCR 第 70 秒：修正 ref
      {"ref": "ASR:T@00:00:01", "text": "三分钟学会做早餐"},  # 编造
    ],
    pack,
  )

  assert [item["ref"] for item in grounded] == ["ASR:T@00:01:10", "OCR:T@00:01:10"]
  assert any("找不到" in item for item in issues)


def test_finding_without_grounded_quote_is_sent_back(monkeypatch: pytest.MonkeyPatch) -> None:
  pack = _pack("c01_hook_no_promise")
  findings = [
    _finding("hook_analysis", "HOOK", finding_type="hook_no_value_promise", grounded_quotes=[], cited_refs=["FRAME:T@00:00:01"]),
    _finding("structure_rhythm_analysis", "STRUCTURE_RHYTHM", polarity="PARITY", finding_type="parity",
             grounded_quotes=[], cited_refs=["SCENE:T#2"]),
  ]
  result = evaluator_node(_state(findings, pack), CONFIG)

  assert result["next_action"] == "diagnose"
  assert set(result["retry_feedback"]) == {"hook_analysis"}  # 结构节奏用 SCENE 数据可以不引原文
  assert "逐字引用" in result["retry_feedback"]["hook_analysis"][0]


def test_unknown_finding_type_is_sent_back_with_allowed_list() -> None:
  findings = [_finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="weak_value")]
  result = evaluator_node(_state(findings, _pack("c03_value_late")), CONFIG)

  feedback = result["retry_feedback"]["value_delivery_analysis"]
  assert any("value_late" in item and "no_cta" in item for item in feedback)


def test_result_contract_keeps_v2_types_instead_of_unknown() -> None:
  normalized = normalize_specialist_result({"outcome": "FINDING", "finding_type": "value_late"}, _skill("value_delivery_analysis"))
  assert normalized["finding_type"] == "value_late"


# ---------------------------------------------------------------- 分析窗口 / 矛盾


def test_missing_cta_claim_outside_analysis_window_is_rejected() -> None:
  findings = [_finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="no_cta")]
  result = evaluator_node(_state(findings, _pack("c13_truncated_long_video")), CONFIG)

  assert any("窗口" in item for item in result["retry_feedback"]["value_delivery_analysis"])


def test_hook_vs_value_contradiction_on_opening_is_flagged() -> None:
  """线上第一次真实运行暴露的问题：钩子说'开场没有价值承诺'，价值传递却引用了开场第 0 秒的收益原文。"""
  pack = _pack("c11_contradiction_bait")
  findings = [
    _finding("hook_analysis", "HOOK", finding_type="hook_no_value_promise"),
    _finding(
      "value_delivery_analysis",
      "VALUE_DELIVERY",
      polarity="PARITY",
      finding_type="parity",
      grounded_quotes=[{"ref": "ASR:T@00:00:00", "text": "三个技巧，让你的早餐五分钟就能做好"}],
    ),
  ]
  result = evaluator_node(_state(findings, pack), CONFIG)

  assert result["next_action"] == "diagnose"
  hook_feedback = result["retry_feedback"]["hook_analysis"]
  assert any(item.startswith("价值传递专家引用了开场") for item in hook_feedback)
  # 第四轮：口播与参考相同 → 硬规则直接指出应改为 hook_weak_visual_text
  assert any("hook_weak_visual_text" in item for item in hook_feedback)
  assert any("conflicting" in reason for reason in result["evaluation_results"][-1]["reasons"])


# ---------------------------------------------------------------- 合成


def test_strengths_are_not_prioritized_or_persisted_and_priority_follows_rank() -> None:
  findings = [
    _finding("hook_analysis", "HOOK", polarity="STRENGTH", finding_type="strength", confidence=0.95),
    _finding("structure_rhythm_analysis", "STRUCTURE_RHYTHM", finding_type="pacing_too_dense", confidence=0.9),
    _finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="value_late", confidence=0.9),
  ]
  synthesis = build_rule_synthesis(findings, completion_status="COMPLETED")

  assert [row["dimension"] for row in synthesis["priorities"]] == ["VALUE_DELIVERY", "STRUCTURE_RHYTHM"]
  assert [row["dimension"] for row in synthesis["strengths"]] == ["HOOK"]
  assert "优势" in synthesis["summary"]

  persisted = persistable_findings(assign_priorities(findings, synthesis))
  assert {row["dimension"]: row["priority"] for row in persisted} == {"VALUE_DELIVERY": "P0", "STRUCTURE_RHYTHM": "P1"}


def test_end_to_end_strength_not_saved_and_priority_sent(monkeypatch: pytest.MonkeyPatch) -> None:
  pack = _pack("c09_strength_hook")
  plans = {
    "HOOK": {"polarity": "STRENGTH", "finding_type": "strength", "target_score": 5, "reference_scores": {"R1": 2},
             "quotes": [{"ref": "ASR:T@00:00:00", "text": "三个技巧，让你的早餐五分钟就能做好"}]},
    "STRUCTURE_RHYTHM": {"polarity": "PARITY", "finding_type": "parity", "evidence_refs": ["SCENE:T#2"], "quotes": [],
                         "target_score": 3, "reference_scores": {"R1": 3}},
    "VALUE_DELIVERY": {"polarity": "GAP", "finding_type": "no_proof", "target_score": 2, "reference_scores": {"R1": 4},
                       "quotes": [{"ref": "OCR:T@00:01:05", "text": "以前25分钟 → 现在5分钟"},
                                  {"ref": "OCR:R1@00:01:05", "text": "以前25分钟 → 现在5分钟"}]},
  }

  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any], **_: Any) -> dict[str, Any]:
    return {
      "outcome": "FINDING",
      "dimension": dimension,
      "observation": f"{dimension} obs",
      "suggested_action": "具体改法",
      "target_frame_refs": [],
      "reference_frame_refs": [],
      "evidence_refs": [],
      "confidence": 0.85,
      **plans[dimension],
    }

  batches: list[dict[str, Any]] = []
  tools = _tools(pack)
  tools["save_diagnosis_result"] = lambda **kwargs: batches.append(kwargs) or {"findingIds": ["f1"]}
  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = _harness(tools).run("job-v2", {"job_id": "job-v2", "agent_run_id": "run-v2"})

  assert result.status == "success"
  saved = batches[0]["findings"]
  assert [row["dimension"] for row in saved] == ["VALUE_DELIVERY"]
  assert saved[0]["priority"] == "P0"
  synthesis = result.output["synthesis"]
  assert [row["dimension"] for row in synthesis["strengths"]] == ["HOOK"]
  assert [row["dimension"] for row in synthesis["parity"]] == ["STRUCTURE_RHYTHM"]


def test_v2_feedback_does_not_push_towards_abstain_and_metadata_grounds_structure() -> None:
  findings = [
    _finding("hook_analysis", "HOOK", finding_type="hook_no_value_promise", confidence=0.3),
    _finding("structure_rhythm_analysis", "STRUCTURE_RHYTHM", finding_type="pacing_too_dense",
             grounded_quotes=[], cited_refs=["METADATA:T", "METADATA:R1"]),
  ]
  result = evaluator_node(_state(findings, _pack("c06_pacing_dense")), CONFIG)

  hook_feedback = " ".join(result["retry_feedback"]["hook_analysis"])
  assert "不要 ABSTAIN" in hook_feedback and "改为 ABSTAIN" not in hook_feedback
  assert "structure_rhythm_analysis" not in result["retry_feedback"]  # 引用 sceneStats 即可，无需原文


# ---------------------------------------------------------------- 第三轮：评分决定方向、差距必须有参考证据


def test_polarity_is_derived_from_scores_not_from_model_label() -> None:
  from agent_service.graph.diagnosis_skill import apply_score_polarity

  same = {"outcome": "FINDING", "polarity": "GAP", "finding_type": "hook_no_value_promise",
          "target_score": 4, "reference_scores": {"R1": 4}}
  apply_score_polarity(same)
  assert same["polarity"] == "PARITY" and same["finding_type"] == "parity"
  assert same["polarity_overridden"]["model"] == "GAP"

  better = {"outcome": "FINDING", "polarity": "GAP", "finding_type": "hook_no_value_promise",
            "target_score": 4, "reference_scores": {"R1": 2, "R2": 3}}
  apply_score_polarity(better)
  assert better["polarity"] == "STRENGTH"

  worse = {"outcome": "FINDING", "polarity": "GAP", "finding_type": "value_late",
           "target_score": 2, "reference_scores": {"R1": 2, "R2": 4}}
  apply_score_polarity(worse)
  assert worse["polarity"] == "GAP" and "polarity_overridden" not in worse  # 与最好的参考比较


def test_gap_needs_reference_evidence_and_scores() -> None:
  findings = [
    _finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="value_late",
             grounded_quotes=[{"ref": "ASR:T@00:01:10", "text": "原文"}]),
    _finding("hook_analysis", "HOOK", finding_type="hook_no_value_promise", target_score=None, reference_scores={}),
  ]
  result = evaluator_node(_state(findings, _pack("c03_value_late")), CONFIG)

  assert any("参考视频" in item for item in result["retry_feedback"]["value_delivery_analysis"])
  assert any("target_score" in item for item in result["retry_feedback"]["hook_analysis"])


def test_hook_gap_with_identical_opening_is_rejected() -> None:
  identical = evaluator_node(
    _state([_finding("hook_analysis", "HOOK", finding_type="hook_no_value_promise")], _pack("c06_pacing_dense")), CONFIG
  )
  assert any("几乎相同" in item for item in identical["retry_feedback"]["hook_analysis"])

  different = evaluator_node(
    _state([_finding("hook_analysis", "HOOK", finding_type="hook_no_value_promise")], _pack("c01_hook_no_promise")), CONFIG
  )
  assert different["next_action"] == "synthesize"


def test_pacing_gap_requires_different_stats_and_numbers() -> None:
  equal = _finding("structure_rhythm_analysis", "STRUCTURE_RHYTHM", finding_type="pacing_too_dense",
                   grounded_quotes=[], cited_refs=["METADATA:T", "METADATA:R1"], suggested_action="放慢节奏")
  result = evaluator_node(_state([equal], _pack("c14_equal_quality")), CONFIG)
  feedback = " ".join(result["retry_feedback"]["structure_rhythm_analysis"])
  assert "节奏几乎相同" in feedback and "中位" in feedback and "具体数字" in feedback


# ---------------------------------------------------------------- 第四轮：硬规则在打回用尽后强制执行、可计算的事实由系统判定


def test_hard_rule_violations_are_downgraded_when_retries_run_out() -> None:
  findings = [
    _finding("structure_rhythm_analysis", "STRUCTURE_RHYTHM", finding_type="pacing_too_slow",
             grounded_quotes=[], cited_refs=["METADATA:T", "METADATA:R1"], suggested_action="镜头延长到 8 秒"),
    _finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="value_late",
             first_benefit_seconds={"T": 0.4, "R1": 0.4}),
  ]
  state = _state(findings, _pack("c17_finance_value_late"), iteration_count=5)  # 打回次数已用完
  result = evaluator_node(state, CONFIG)

  assert result["next_action"] == "synthesize"
  by_dimension = {item["dimension"]: item for item in result["findings"]}
  assert by_dimension["STRUCTURE_RHYTHM"]["polarity"] == "PARITY"
  assert by_dimension["STRUCTURE_RHYTHM"]["downgraded"]["rule"] == "same_pacing"
  assert by_dimension["VALUE_DELIVERY"]["downgraded"]["rule"] == "benefit_not_late"


def test_same_pacing_needs_median_and_longest_shot_too() -> None:
  """平均镜头接近、分布却很不均（c23）不算节奏相同；c14 那种均匀接近的仍然拦。"""
  from agent_service.eval.quality_cases import build_cases
  from agent_service.graph.evidence_timeline import scene_stats
  from agent_service.graph.nodes.evaluator import hard_rule_violation, same_pacing

  cases = {case.case_id: case for case in build_cases()}
  uneven = cases["c23_cooking_uneven_pacing"]
  assert same_pacing(scene_stats(uneven.target, "T"), scene_stats(uneven.references[0], "R1")) is None
  finding = {"dimension": "STRUCTURE_RHYTHM", "polarity": "GAP", "outcome": "FINDING", "finding_type": "pacing_too_slow",
             "target_score": 2, "reference_scores": {"R1": 4}}
  assert hard_rule_violation(finding, uneven.evidence_pack()) is None

  equal = cases["c14_equal_quality"]
  assert same_pacing(scene_stats(equal.target, "T"), scene_stats(equal.references[0], "R1"))
  assert hard_rule_violation(finding, equal.evidence_pack())["rule"] == "same_pacing"


def test_structure_unclear_rejected_when_step_markers_exist() -> None:
  from agent_service.graph.nodes.evaluator import hard_rule_violation

  finding = _finding("structure_rhythm_analysis", "STRUCTURE_RHYTHM", finding_type="structure_unclear")
  assert hard_rule_violation(finding, _pack("c11_contradiction_bait"))["rule"] == "has_step_markers"
  assert hard_rule_violation(finding, _pack("c08_structure_unclear")) is None


def test_value_late_needs_first_benefit_seconds() -> None:
  findings = [_finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="value_late")]
  result = evaluator_node(_state(findings, _pack("c03_value_late")), CONFIG)
  assert any("first_benefit_seconds" in item for item in result["retry_feedback"]["value_delivery_analysis"])

  ok = [_finding("value_delivery_analysis", "VALUE_DELIVERY", finding_type="value_late", first_benefit_seconds={"T": 70, "R1": 0.5})]
  assert evaluator_node(_state(ok, _pack("c03_value_late")), CONFIG)["next_action"] == "synthesize"


def test_empty_opening_is_typed_as_slow_start_by_the_system() -> None:
  from agent_service.graph.diagnosis_skill import apply_fact_corrections

  slow = {"dimension": "HOOK", "outcome": "FINDING", "polarity": "GAP", "finding_type": "hook_no_value_promise"}
  apply_fact_corrections(slow, _pack("c02_hook_slow_start"))
  assert slow["finding_type"] == "hook_slow_start" and slow["type_corrected"]["from"] == "hook_no_value_promise"

  normal = {"dimension": "HOOK", "outcome": "FINDING", "polarity": "GAP", "finding_type": "hook_no_value_promise"}
  apply_fact_corrections(normal, _pack("c01_hook_no_promise"))
  assert normal["finding_type"] == "hook_no_value_promise"
