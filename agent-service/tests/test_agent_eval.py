from __future__ import annotations

from pathlib import Path

from agent_service.eval.agent_ablation import (
  AgentEvalFinding,
  AgentEvalGoldenCase,
  AgentEvalPrediction,
  AgentEvalRunner,
  load_or_create_agent_eval_dataset,
  validate_agent_eval_dataset,
  write_agent_ablation_report,
  write_agent_eval_review_markdown,
)
from agent_service.eval.run_agent_ablation import _handoff_metrics


def _verified_case() -> AgentEvalGoldenCase:
  return AgentEvalGoldenCase(
    case_id="case-1",
    verification_status="VERIFIED",
    input={"target_evidence": {"keyframes": ["FRAME:1"]}, "reference_evidence": []},
    expected_findings=[
      AgentEvalFinding("hook_analysis", "opening hook weak", ["FRAME:1"]),
      AgentEvalFinding("value_delivery_analysis", "value unclear", ["ASR:1"]),
    ],
    cross_skill_ambiguity=True,
    expected_handoff_capability="value_delivery",
    expected_conflict_resolution="value boundary resolved",
  )


def test_eval_metric_precision_recall_f1() -> None:
  runner = AgentEvalRunner([_verified_case()], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-1",
        "FULL_SINGLE_WORKFLOW",
        findings=[
          AgentEvalFinding("hook_analysis", "opening hook weak", ["FRAME:1"]),
          AgentEvalFinding("structure_rhythm_analysis", "extra unsupported", []),
        ],
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  metrics = report["modes"]["FULL_SINGLE_WORKFLOW"]
  assert metrics["findingPrecision"] == 1.0
  assert metrics["findingRecall"] == 0.5
  assert round(metrics["findingF1"], 4) == 0.6667


def test_failed_execution_can_still_score_matching_finding() -> None:
  case = AgentEvalGoldenCase(
    case_id="case-failed-but-matched",
    verification_status="VERIFIED",
    input={"target_evidence": {}, "reference_evidence": []},
    primary_skill="hook_analysis",
    expected_findings=[
      AgentEvalFinding("hook_analysis", "human label", ["FRAME:1"], finding_type="strong_opening_hook"),
    ],
  )
  runner = AgentEvalRunner([case], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-failed-but-matched",
        "FULL_SINGLE_WORKFLOW",
        findings=[AgentEvalFinding("hook_analysis", "runtime long label", ["FRAME:1"], finding_type="strong_opening_hook")],
        execution_success=False,
        failure_reason="structure_rhythm_analysis confidence below threshold.",
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  metrics = report["modes"]["FULL_SINGLE_WORKFLOW"]
  assert metrics["findingF1"] == 1.0
  assert metrics["executionSuccessRate"] == 0.0
  assert metrics["executionFailureRate"] == 1.0


def test_agent_finding_match_uses_structured_type_before_label() -> None:
  case = AgentEvalGoldenCase(
    case_id="case-structured",
    verification_status="VERIFIED",
    input={"target_evidence": {}, "reference_evidence": []},
    primary_skill="hook_analysis",
    expected_findings=[
      AgentEvalFinding("hook_analysis", "short human label", ["FRAME:1"], finding_type="strong_opening_hook"),
    ],
  )
  runner = AgentEvalRunner([case], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-structured",
        "FULL_SINGLE_WORKFLOW",
        findings=[AgentEvalFinding("hook_analysis", "long runtime observation", ["FRAME:1"], finding_type="strong_opening_hook")],
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  assert report["modes"]["FULL_SINGLE_WORKFLOW"]["findingF1"] == 1.0


def test_agent_same_label_different_finding_type_does_not_match() -> None:
  case = AgentEvalGoldenCase(
    case_id="case-structured-mismatch",
    verification_status="VERIFIED",
    input={"target_evidence": {}, "reference_evidence": []},
    primary_skill="hook_analysis",
    expected_findings=[
      AgentEvalFinding("hook_analysis", "same label", ["FRAME:1"], finding_type="strong_opening_hook"),
    ],
  )
  runner = AgentEvalRunner([case], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-structured-mismatch",
        "FULL_SINGLE_WORKFLOW",
        findings=[AgentEvalFinding("hook_analysis", "same label", ["FRAME:1"], finding_type="weak_opening_hook")],
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  assert report["modes"]["FULL_SINGLE_WORKFLOW"]["findingF1"] == 0.0


def test_handoff_metric_canonicalizes_structure_rhythm_alias() -> None:
  case = AgentEvalGoldenCase(
    case_id="case-handoff-alias",
    verification_status="VERIFIED",
    input={"target_evidence": {}, "reference_evidence": []},
    expected_handoff_capability="structure_rhythm",
  )
  metrics = _handoff_metrics(
    [case],
    [
      {
        "caseId": "case-handoff-alias",
        "mode": "SPECIALIST_MULTI_AGENT",
        "routingHistory": [{"targetCapability": "structure_rhythm_analysis"}],
      }
    ],
  )

  assert metrics["handoffSuccessCount"] == 1
  assert metrics["missedHandoffCount"] == 0


def test_primary_skill_scope_ignores_other_skill_runtime_noise() -> None:
  case = AgentEvalGoldenCase(
    case_id="case-hook-scope",
    verification_status="VERIFIED",
    input={"target_evidence": {}, "reference_evidence": []},
    primary_skill="hook_analysis",
    expected_findings=[
      AgentEvalFinding("hook_analysis", "human label", ["FRAME:1"], finding_type="strong_opening_hook"),
    ],
  )
  runner = AgentEvalRunner([case], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-hook-scope",
        "FULL_SINGLE_WORKFLOW",
        findings=[
          AgentEvalFinding("hook_analysis", "runtime label", ["FRAME:1"], finding_type="strong_opening_hook"),
          AgentEvalFinding("structure_rhythm_analysis", "unrelated structure failure", [], finding_type="low_density"),
        ],
        execution_success=False,
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  metrics = report["modes"]["FULL_SINGLE_WORKFLOW"]
  assert metrics["findingPrecision"] == 1.0
  assert metrics["findingRecall"] == 1.0


def test_evidence_gap_abstention_scores_separately() -> None:
  case = AgentEvalGoldenCase(
    case_id="case-abstain",
    verification_status="VERIFIED",
    input={"target_evidence": {}, "reference_evidence": []},
    primary_skill="hook_analysis",
    expected_findings=[
      AgentEvalFinding("hook_analysis", "insufficient opening evidence", [], finding_type="evidence_gap"),
    ],
  )
  runner = AgentEvalRunner([case], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-abstain",
        "FULL_SINGLE_WORKFLOW",
        findings=[AgentEvalFinding("hook_analysis", "abstain", [], finding_type="evidence_gap")],
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  metrics = report["modes"]["FULL_SINGLE_WORKFLOW"]
  assert metrics["findingF1"] == 1.0
  assert metrics["abstentionCaseCount"] == 1.0
  assert metrics["correctAbstentionCount"] == 1.0
  assert metrics["abstentionAccuracy"] == 1.0


def test_evidence_grounding_metric() -> None:
  runner = AgentEvalRunner([_verified_case()], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-1",
        "FULL_SINGLE_WORKFLOW",
        findings=[AgentEvalFinding("hook_analysis", "opening hook weak", ["FRAME:1"])],
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  assert report["modes"]["FULL_SINGLE_WORKFLOW"]["evidenceGroundingRate"] == 1.0


def test_unsupported_finding_metric() -> None:
  runner = AgentEvalRunner([_verified_case()], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-1",
        "FULL_SINGLE_WORKFLOW",
        findings=[AgentEvalFinding("hook_analysis", "opening hook weak", [])],
      )
    ],
    report_kind="COMPONENT_ABLATION",
  )

  assert report["modes"]["FULL_SINGLE_WORKFLOW"]["unsupportedFindingRate"] == 1.0


def test_conflict_resolution_metric() -> None:
  runner = AgentEvalRunner([_verified_case()], dataset_version="agent-test")
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction(
        "case-1",
        "SPECIALIST_MULTI_AGENT",
        findings=[
          AgentEvalFinding("hook_analysis", "opening hook weak", ["FRAME:1"]),
          AgentEvalFinding("value_delivery_analysis", "value unclear", ["ASR:1"]),
        ],
        handoff_count=1,
        replan_count=1,
      )
    ],
    report_kind="ARCHITECTURE_ABLATION",
  )

  metrics = report["crossSkillAmbiguitySubset"]["SPECIALIST_MULTI_AGENT"]
  assert metrics["conflictResolutionRate"] == 1.0
  assert metrics["handoffSuccessRate"] == 1.0


def test_same_case_runs_parallel_and_multi_agent() -> None:
  runner = AgentEvalRunner([_verified_case()], dataset_version="agent-test")

  parallel = runner.graph_for_architecture("PARALLEL_SKILLS")
  multi = runner.graph_for_architecture("SPECIALIST_MULTI_AGENT")

  assert parallel is not None
  assert multi is not None
  assert runner.architecture_modes()["PARALLEL_SKILLS"]["supervisor"] is False
  assert runner.architecture_modes()["SPECIALIST_MULTI_AGENT"]["supervisor"] is True


def test_experiment_config_is_controlled() -> None:
  runner = AgentEvalRunner([_verified_case()], dataset_version="agent-test")
  parallel = runner.architecture_modes()["PARALLEL_SKILLS"]
  multi = runner.architecture_modes()["SPECIALIST_MULTI_AGENT"]

  assert parallel["graph"] == "build_parallel_skills_graph"
  assert multi["graph"] == "build_diagnosis_graph"
  assert runner.knowledge_corpus_version == "runtime"
  assert runner.component_modes()["FULL_SINGLE_WORKFLOW"]["graph"] == "build_parallel_skills_graph"


def test_only_verified_cases_counted() -> None:
  runner = AgentEvalRunner(
    [
      _verified_case(),
      AgentEvalGoldenCase("case-pending", "PENDING", {"target_evidence": {}, "reference_evidence": []}),
    ],
    dataset_version="agent-test",
  )
  report = runner.run_with_predictions(
    [
      AgentEvalPrediction("case-1", "FULL_SINGLE_WORKFLOW"),
      AgentEvalPrediction("case-pending", "FULL_SINGLE_WORKFLOW"),
    ],
    report_kind="COMPONENT_ABLATION",
  )

  assert report["verifiedCaseCount"] == 1
  assert report["pendingCaseCount"] == 1


def test_report_generation(tmp_path: Path) -> None:
  dataset_path = tmp_path / "agent_eval_golden.json"
  cases = load_or_create_agent_eval_dataset(dataset_path)
  runner = AgentEvalRunner(cases, dataset_version="agent-test", model="REAL_LLM_EVAL_NOT_RUN")
  component = runner.run_with_predictions(
    [AgentEvalPrediction(case.case_id, "FULL_SINGLE_WORKFLOW") for case in cases],
    report_kind="COMPONENT_ABLATION",
  )
  architecture = runner.run_with_predictions(
    [AgentEvalPrediction(case.case_id, "PARALLEL_SKILLS") for case in cases],
    report_kind="ARCHITECTURE_ABLATION",
  )
  report = {
    "datasetVersion": runner.dataset_version,
    "status": component["status"],
    "verifiedCaseCount": component["verifiedCaseCount"],
    "pendingCaseCount": component["pendingCaseCount"],
    "model": runner.model,
    "runtimeConfig": component["runtimeConfig"],
    "componentAblation": component,
    "architectureAblation": architecture,
  }

  json_path, md_path = write_agent_ablation_report(report, tmp_path / "reports")

  assert json_path.exists()
  assert md_path.exists()
  assert "INSUFFICIENT_VERIFIED_GOLDEN_DATA" in md_path.read_text(encoding="utf-8")


def test_agent_eval_candidate_dataset_valid() -> None:
  dataset_path = Path(__file__).resolve().parents[1] / "benchmarks" / "agent_eval_golden.json"
  validation = validate_agent_eval_dataset(dataset_path)

  assert validation["isValid"] is True
  assert validation["caseCount"] == 24
  assert validation["verifiedCount"] == 24
  assert validation["pendingCount"] == 0


def test_agent_eval_review_markdown_generation(tmp_path: Path) -> None:
  dataset_path = Path(__file__).resolve().parents[1] / "benchmarks" / "agent_eval_golden.json"

  md_path = write_agent_eval_review_markdown(dataset_path, tmp_path / "agent_eval_review.md")

  content = md_path.read_text(encoding="utf-8")
  assert "Agent Evaluation Golden Case Review" in content
  assert "agent-case-hook-value-boundary-001" in content
  assert "Human Review" in content


def test_agent_eval_validation_rejects_bad_cross_skill_case(tmp_path: Path) -> None:
  dataset_path = tmp_path / "bad_agent_eval.json"
  dataset_path.write_text(
    """
{
  "dataset_version": "bad",
  "cases": [
    {
      "case_id": "bad-cross",
      "verification_status": "PENDING",
      "cross_skill_ambiguity": true,
      "expected_findings": [
        {
          "skill_code": "hook_analysis",
          "label": "bad ref",
          "required_evidence_refs": ["BADREF:1"]
        }
      ]
    }
  ]
}
""",
    encoding="utf-8",
  )

  validation = validate_agent_eval_dataset(dataset_path)

  assert validation["isValid"] is False
  assert any("expected_handoff_capability" in error for error in validation["errors"])
  assert any("invalid evidence ref" in error for error in validation["errors"])
