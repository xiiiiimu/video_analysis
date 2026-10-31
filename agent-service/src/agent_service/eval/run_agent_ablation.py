from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_service.config import get_settings
from agent_service.eval.agent_ablation import (
  AgentEvalFinding,
  AgentEvalPrediction,
  AgentEvalRunner,
  validate_agent_eval_dataset,
)
from agent_service.graph.builder import build_diagnosis_graph, build_parallel_skills_graph
from agent_service.harness.types import HarnessLimits
from agent_service.knowledge import default_video_diagnosis_corpus
from agent_service.services.harness_setup import create_diagnosis_harness
from agent_service.skills import SkillLoader
from agent_service.tools.adapters.knowledge_retrieval import KnowledgeRetrievalToolAdapter

COMPONENT_MODES = [
  "VIDEO_EVIDENCE_ONLY",
  "VIDEO_EVIDENCE_PLUS_RAG",
  "RAG_PLUS_LOCAL_REACT",
  "FULL_SINGLE_WORKFLOW",
]
ARCHITECTURE_MODES = ["PARALLEL_SKILLS", "SPECIALIST_MULTI_AGENT"]
STRICTLY_RUNNABLE_COMPONENTS = {"FULL_SINGLE_WORKFLOW"}


def build_empty_report(runner: AgentEvalRunner) -> dict[str, Any]:
  component_modes = runner.component_modes()
  architecture_modes = runner.architecture_modes()
  predictions = [
    AgentEvalPrediction(case.case_id, mode)
    for case in runner.golden_cases
    for mode in [*component_modes, *architecture_modes]
  ]
  component = runner.run_with_predictions(
    [item for item in predictions if item.mode in component_modes],
    report_kind="COMPONENT_ABLATION",
  )
  architecture = runner.run_with_predictions(
    [item for item in predictions if item.mode in architecture_modes],
    report_kind="ARCHITECTURE_ABLATION",
  )
  return {
    "datasetVersion": runner.dataset_version,
    "status": component["status"],
    "verifiedCaseCount": component["verifiedCaseCount"],
    "pendingCaseCount": component["pendingCaseCount"],
    "model": runner.model,
    "runtimeConfig": component["runtimeConfig"],
    "componentModeDefinitions": component_modes,
    "architectureModeDefinitions": architecture_modes,
    "componentAblation": component,
    "architectureAblation": architecture,
    "realLlmEval": "REAL_LLM_EVAL_NOT_RUN",
    "notes": [
      "Real LLM evaluation was not requested for this empty report path.",
      "Retrieval benchmark remains separate and unchanged.",
    ],
  }


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--dataset-path", default="benchmarks/agent_eval_golden.json")
  parser.add_argument("--output-dir", default="benchmark-reports/agent-ablation")
  parser.add_argument("--run-real-llm", action="store_true")
  args = parser.parse_args()

  dataset_path = Path(args.dataset_path)
  output_dir = Path(args.output_dir)
  runner = AgentEvalRunner.from_file(dataset_path)

  if not args.run_real_llm:
    report = build_empty_report(runner)
    _write_report(report, output_dir)
    print("REAL_LLM_EVAL_NOT_RUN")
    return

  report = run_real_llm_evaluation(dataset_path)
  _write_report(report, output_dir)
  print(f"wrote {output_dir / 'agent_ablation_report.json'}")
  print(f"wrote {output_dir / 'agent_ablation_report.md'}")


def run_real_llm_evaluation(dataset_path: Path) -> dict[str, Any]:
  started_at = datetime.now(UTC).isoformat()
  dataset_hash_before = _sha256(dataset_path)
  validation = validate_agent_eval_dataset(dataset_path)
  if not _dataset_ready(validation):
    return _not_run_report(dataset_path, dataset_hash_before, validation, "DATASET_INTEGRITY_CHECK_FAILED")

  settings = get_settings()
  if not settings.chat_api_key:
    return _not_run_report(dataset_path, dataset_hash_before, validation, "REAL_LLM_EVAL_NOT_RUN")

  dataset_payload = json.loads(dataset_path.read_text(encoding="utf-8"))
  golden_cases = AgentEvalRunner.from_file(dataset_path).golden_cases
  skill_snapshots = _load_skill_snapshots()
  corpus = default_video_diagnosis_corpus()
  model_config = {
    "provider": _provider_name(settings.chat_base_url),
    "model": settings.chat_model,
    "baseUrl": _redacted_base_url(settings.chat_base_url),
    "temperature": 0.2,
    "topP": "unavailable",
    "maxTokens": "unavailable",
    "timestamp": started_at,
  }

  component_predictions: list[AgentEvalPrediction] = []
  architecture_predictions: list[AgentEvalPrediction] = []
  execution_failures: list[dict[str, Any]] = []
  case_diagnostics: list[dict[str, Any]] = []

  for mode in COMPONENT_MODES:
    if mode not in STRICTLY_RUNNABLE_COMPONENTS:
      continue
    for raw_case in dataset_payload["cases"]:
      prediction, diagnostic = _run_case(raw_case, mode, build_parallel_skills_graph())
      component_predictions.append(prediction)
      case_diagnostics.append(diagnostic)
      if diagnostic.get("executionFailure"):
        execution_failures.append(diagnostic["executionFailure"])

  for mode in ARCHITECTURE_MODES:
    graph = build_parallel_skills_graph() if mode == "PARALLEL_SKILLS" else build_diagnosis_graph()
    for raw_case in dataset_payload["cases"]:
      prediction, diagnostic = _run_case(raw_case, mode, graph)
      architecture_predictions.append(prediction)
      case_diagnostics.append(diagnostic)
      if diagnostic.get("executionFailure"):
        execution_failures.append(diagnostic["executionFailure"])

  eval_runner = AgentEvalRunner(
    golden_cases,
    dataset_version=validation["datasetVersion"],
    model=settings.chat_model,
    knowledge_corpus_version="runtime",
    skill_snapshots=skill_snapshots,
  )
  component_report = eval_runner.run_with_predictions(
    [
      *component_predictions,
      *[
        AgentEvalPrediction(case.case_id, mode)
        for mode in COMPONENT_MODES
        if mode not in STRICTLY_RUNNABLE_COMPONENTS
        for case in golden_cases
      ],
    ],
    report_kind="COMPONENT_ABLATION",
  )
  architecture_report = eval_runner.run_with_predictions(
    architecture_predictions,
    report_kind="ARCHITECTURE_ABLATION",
  )
  full_metrics = _architecture_summary(golden_cases, architecture_predictions)
  cross_metrics = _subset_summary(
    golden_cases,
    architecture_predictions,
    lambda case: case.expected_handoff_capability != "NONE",
  )
  normal_metrics = _subset_summary(
    golden_cases,
    architecture_predictions,
    lambda case: case.expected_handoff_capability == "NONE",
  )
  handoff_metrics = _handoff_metrics(golden_cases, case_diagnostics)
  failure_analysis = _failure_analysis(golden_cases, architecture_predictions, case_diagnostics)
  dataset_hash_after = _sha256(dataset_path)
  successful_model_calls = sum(item.model_call_count for item in [*component_predictions, *architecture_predictions])
  real_llm_status = (
    "REAL_LLM_EVAL_RUN"
    if successful_model_calls > 0
    else "REAL_LLM_EVAL_ATTEMPTED_NO_SUCCESSFUL_MODEL_CALLS"
  )
  run_status = "OK"
  if dataset_hash_before != dataset_hash_after:
    run_status = "INVALID_DATASET_HASH_CHANGED"
  elif not successful_model_calls:
    run_status = "EXECUTION_FAILED_BEFORE_LLM_CALL"
  report = {
    "datasetVersion": validation["datasetVersion"],
    "datasetHashBefore": dataset_hash_before,
    "datasetHashAfter": dataset_hash_after,
    "goldenDatasetModifiedDuringRun": dataset_hash_before != dataset_hash_after,
    "status": run_status,
    "realLlmEval": real_llm_status,
    "runStartedAt": started_at,
    "runFinishedAt": datetime.now(UTC).isoformat(),
    "modelConfig": model_config,
    "verifiedCaseCount": validation["verifiedCount"],
    "pendingCaseCount": validation["pendingCount"],
    "knowledgeCorpusVersion": "runtime",
    "knowledgeCorpusSize": len(corpus),
    "skillSnapshots": skill_snapshots,
    "runtimeConfig": eval_runner._runtime_config(),
    "componentModeDefinitions": _component_mode_definitions(),
    "architectureModeDefinitions": eval_runner.architecture_modes(),
    "componentAblation": component_report,
    "architectureAblation": architecture_report,
    "architectureSummary": full_metrics,
    "crossSkillAmbiguitySubset": cross_metrics,
    "normalCasesSubset": normal_metrics,
    "handoffMetrics": handoff_metrics,
    "executionFailures": execution_failures,
    "failureAnalysis": failure_analysis,
    "caseDiagnostics": case_diagnostics,
    "retrievalBenchmarkReference": "benchmark-reports/v0.5-final-test/",
    "notes": [
      "single-run evaluation",
      "Component modes other than FULL_SINGLE_WORKFLOW are NOT_STRICTLY_ISOLATABLE without runtime changes.",
      "Finding metrics use the existing exact-label harness; no LLM judge or semantic matcher was added.",
      "Token usage comes from harness.call_model (provider usage metadata); 'unavailable' when no real LLM call ran.",
      "If modelCallCount is 0 with execution failures, the run did not produce successful real LLM outputs.",
    ],
  }
  return report


def _run_case(raw_case: dict[str, Any], mode: str, graph: Any) -> tuple[AgentEvalPrediction, dict[str, Any]]:
  case_id = raw_case["case_id"]
  started = time.perf_counter()
  harness = create_diagnosis_harness(_tools_for_case(raw_case), graph=graph, limits=_eval_limits())
  run_id = f"eval-{mode}-{case_id}"
  result = harness.run(case_id, {"job_id": case_id, "agent_run_id": run_id})
  latency_ms = (time.perf_counter() - started) * 1000
  # 改造后 harness 在预算用完/超时时也会返回最后的 state；评测口径保持不变：非 success 的 run 不计 findings
  output = (result.output or {}) if result.status == "success" else {}
  findings = [_prediction_finding(item) for item in output.get("findings") or []]
  prediction = AgentEvalPrediction(
    case_id=case_id,
    mode=mode,
    findings=findings,
    execution_success=result.status == "success" and output.get("status") != "FAILED",
    failure_reason=result.error or output.get("error", ""),
    latency_ms=latency_ms,
    model_call_count=_model_call_count(output),
    agent_call_count=_agent_call_count(output),
    tool_call_count=_tool_call_count(output),
    handoff_count=len(output.get("routing_history") or []),
    replan_count=int(output.get("global_replan_count") or 0),
    token_usage=result.usage if result.usage.get("totalTokens") else "unavailable",
  )
  diagnostic = {
    "caseId": case_id,
    "mode": mode,
    "status": result.status,
    "runtimeStatus": output.get("status", ""),
    "latencyMs": latency_ms,
    "routingHistory": output.get("routing_history") or [],
    "evaluationResults": output.get("evaluation_results") or [],
    "predictedLabels": [finding.label for finding in findings],
    "predictedFindingTypes": [finding.finding_type for finding in findings],
    "expectedHandoffCapability": raw_case.get("expected_handoff_capability", ""),
  }
  if result.status != "success" or output.get("status") == "FAILED":
    diagnostic["executionFailure"] = {
      "case_id": case_id,
      "mode": mode,
      "failure_type": output.get("status") or result.status,
      "message": result.error or output.get("error", ""),
    }
  return prediction, diagnostic


def _tools_for_case(raw_case: dict[str, Any]) -> dict[str, Any]:
  evidence = _runtime_evidence(raw_case)
  knowledge_tool = KnowledgeRetrievalToolAdapter()
  saved: list[dict[str, Any]] = []
  progress: list[dict[str, Any]] = []

  return {
    "get_job_context": lambda job_id: {
      "jobId": job_id,
      "targetVideoId": evidence["targetEvidence"].get("videoAssetId"),
      "referenceVideoIds": [item.get("videoAssetId") for item in evidence.get("referenceEvidence") or []],
      "useKnowledge": True,
      "category": raw_case.get("primary_skill", ""),
      "inputSnapshotJson": json.dumps(raw_case.get("input") or {}, ensure_ascii=False),
    },
    "get_video_evidence": lambda job_id: evidence,
    "retrieve_knowledge": knowledge_tool.retrieve_knowledge,
    "save_diagnosis_hypothesis": lambda job_id, hypothesis: saved.append(hypothesis)
    or {"findingId": f"eval-finding-{len(saved)}"},
    "save_agent_draft_result": lambda job_id, draft_observations: {"ok": True},
    "report_agent_progress": lambda **kwargs: progress.append(kwargs) or {"ok": True},
  }


def _runtime_evidence(raw_case: dict[str, Any]) -> dict[str, Any]:
  target = (raw_case.get("input") or {}).get("target_evidence") or {}
  refs = [str(item) for item in target.get("evidence_refs") or []]
  return {
    "targetEvidence": {
      "videoAssetId": raw_case["case_id"],
      "transcriptText": target.get("asr", ""),
      "keyframes": [ref for ref in refs if ref.startswith("FRAME:")],
      "sceneJson": target.get("metadata", ""),
      "ocrJson": target.get("ocr", ""),
    },
    "referenceEvidence": [
      {
        "videoAssetId": f"{raw_case['case_id']}-ref-{index}",
        "transcriptText": ref.get("asr", ""),
        "keyframes": [item for item in ref.get("evidence_refs") or [] if str(item).startswith("FRAME:")],
        "ocrJson": ref.get("ocr", ""),
      }
      for index, ref in enumerate((raw_case.get("input") or {}).get("reference_evidence") or [], start=1)
    ],
  }


def _prediction_finding(finding: dict[str, Any]) -> AgentEvalFinding:
  label = " | ".join(
    item
    for item in [
      str(finding.get("observation") or ""),
      str(finding.get("hypothesis_text") or ""),
      str(finding.get("suggested_action") or ""),
    ]
    if item
  )
  return AgentEvalFinding(
    skill_code=str(finding.get("skill_key") or ""),
    label=label,
    required_evidence_refs=list(finding.get("evidence_refs") or []),
    finding_type=str(finding.get("finding_type") or ""),
  )


def _architecture_summary(cases: list[Any], predictions: list[AgentEvalPrediction]) -> dict[str, Any]:
  return {
    mode: _aggregate_predictions(cases, [item for item in predictions if item.mode == mode])
    for mode in ARCHITECTURE_MODES
  }


def _subset_summary(cases: list[Any], predictions: list[AgentEvalPrediction], predicate: Any) -> dict[str, Any]:
  subset = [case for case in cases if predicate(case)]
  return {
    "caseCount": len(subset),
    "modes": {
      mode: _aggregate_predictions(subset, [item for item in predictions if item.mode == mode])
      for mode in ARCHITECTURE_MODES
    },
  }


def _aggregate_predictions(cases: list[Any], predictions: list[AgentEvalPrediction]) -> dict[str, Any]:
  if not cases:
    return _empty_metrics()
  prediction_by_case = {item.case_id: item for item in predictions}
  rows = []
  for case in cases:
    prediction = prediction_by_case.get(case.case_id, AgentEvalPrediction(case.case_id, "MISSING"))
    expected_scope = _expected_scope(case)
    expected = [
      _golden_finding(index, finding)
      for index, finding in enumerate(case.expected_findings)
    ]
    actual = [
      _predicted_finding(index, finding)
      for index, finding in enumerate(prediction.findings)
      if not expected_scope or finding.skill_code in expected_scope
    ]
    metrics = _evaluate_agent_findings(expected, actual)
    abstention_case = _is_abstention_case(case)
    correct_abstention = 1.0 if abstention_case and _has_abstention_prediction(prediction.findings, expected_scope) else 0.0
    metrics["executionSuccessRate"] = 1.0 if prediction.execution_success else 0.0
    metrics["executionFailureRate"] = 0.0 if prediction.execution_success else 1.0
    metrics["abstentionCaseCount"] = 1.0 if abstention_case else 0.0
    metrics["correctAbstentionCount"] = correct_abstention
    metrics["abstentionAccuracy"] = correct_abstention if abstention_case else 0.0
    metrics["endToEndLatencyMs"] = prediction.latency_ms
    metrics["modelCallCount"] = float(prediction.model_call_count)
    metrics["agentCallCount"] = float(prediction.agent_call_count)
    metrics["toolCallCount"] = float(prediction.tool_call_count)
    metrics["handoffCount"] = float(prediction.handoff_count)
    metrics["replanCount"] = float(prediction.replan_count)
    rows.append(metrics)
  keys = [key for key in rows[0] if key not in {"abstentionCaseCount", "correctAbstentionCount", "abstentionAccuracy"}]
  aggregated = {key: sum(row[key] for row in rows) / len(rows) for key in keys}
  abstention_cases = sum(row["abstentionCaseCount"] for row in rows)
  correct_abstentions = sum(row["correctAbstentionCount"] for row in rows)
  aggregated["abstentionCaseCount"] = abstention_cases
  aggregated["correctAbstentionCount"] = correct_abstentions
  aggregated["abstentionAccuracy"] = correct_abstentions / abstention_cases if abstention_cases else 0.0
  return aggregated | {"tokenUsage": "unavailable"}


def _handoff_metrics(cases: list[Any], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
  by_case_mode = {(item["caseId"], item["mode"]): item for item in diagnostics}
  expected_handoff_cases = [case for case in cases if case.expected_handoff_capability != "NONE"]
  normal_cases = [case for case in cases if case.expected_handoff_capability == "NONE"]
  multi_success = 0
  wrong = 0
  missed = 0
  for case in expected_handoff_cases:
    diagnostic = by_case_mode.get((case.case_id, "SPECIALIST_MULTI_AGENT"), {})
    capabilities = _routed_capabilities(diagnostic)
    expected = _canonical_capability(case.expected_handoff_capability)
    if expected in capabilities:
      multi_success += 1
    elif capabilities:
      wrong += 1
    else:
      missed += 1
  unnecessary = 0
  for case in normal_cases:
    diagnostic = by_case_mode.get((case.case_id, "SPECIALIST_MULTI_AGENT"), {})
    if _routed_capabilities(diagnostic):
      unnecessary += 1
  return {
    "handoffEvaluatedCaseCount": len(expected_handoff_cases),
    "handoffSuccessCount": multi_success,
    "handoffSuccessRate": multi_success / len(expected_handoff_cases) if expected_handoff_cases else 0.0,
    "wrongHandoffCount": wrong,
    "missedHandoffCount": missed,
    "normalCaseCount": len(normal_cases),
    "unnecessaryHandoffCount": unnecessary,
    "unnecessaryHandoffRate": unnecessary / len(normal_cases) if normal_cases else 0.0,
  }


def _failure_analysis(cases: list[Any], predictions: list[AgentEvalPrediction], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
  prediction_by_case_mode = {(item.case_id, item.mode): item for item in predictions}
  false_positives: list[dict[str, Any]] = []
  false_negatives: list[dict[str, Any]] = []
  for case in cases:
    for mode in ARCHITECTURE_MODES:
      prediction = prediction_by_case_mode.get((case.case_id, mode))
      if prediction is None:
        continue
      expected_scope = _expected_scope(case)
      expected_labels = {_finding_key(finding) for finding in case.expected_findings}
      predicted_labels = {
        _finding_key(finding)
        for finding in prediction.findings
        if not expected_scope or finding.skill_code in expected_scope
      }
      for label in sorted(predicted_labels - expected_labels):
        false_positives.append({"caseId": case.case_id, "mode": mode, "label": label})
      for label in sorted(expected_labels - predicted_labels):
        false_negatives.append({"caseId": case.case_id, "mode": mode, "label": label})
  return {
    "falsePositiveCount": len(false_positives),
    "falseNegativeCount": len(false_negatives),
    "falsePositives": false_positives[:20],
    "falseNegatives": false_negatives[:20],
    "wrongHandoffCases": _handoff_case_rows(cases, diagnostics, "wrong"),
    "missedHandoffCases": _handoff_case_rows(cases, diagnostics, "missed"),
    "unnecessaryHandoffCases": _handoff_case_rows(cases, diagnostics, "unnecessary"),
    "executionFailureCategories": _execution_failure_categories(diagnostics),
  }


def _handoff_case_rows(cases: list[Any], diagnostics: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
  rows = []
  by_case_mode = {(item["caseId"], item["mode"]): item for item in diagnostics}
  for case in cases:
    diagnostic = by_case_mode.get((case.case_id, "SPECIALIST_MULTI_AGENT"), {})
    routed = _routed_capabilities(diagnostic)
    expected = _canonical_capability(case.expected_handoff_capability)
    if kind == "wrong" and expected != "NONE" and routed and expected not in routed:
      rows.append({"caseId": case.case_id, "expected": expected, "actual": routed})
    if kind == "missed" and expected != "NONE" and not routed:
      rows.append({"caseId": case.case_id, "expected": expected, "actual": routed})
    if kind == "unnecessary" and expected == "NONE" and routed:
      rows.append({"caseId": case.case_id, "expected": expected, "actual": routed})
  return rows


def _routed_capabilities(diagnostic: dict[str, Any]) -> list[str]:
  return [
    _canonical_capability(str(item.get("targetCapability") or item.get("target_capability") or ""))
    for item in diagnostic.get("routingHistory") or []
    if item.get("targetCapability") or item.get("target_capability")
  ]


def _canonical_capability(capability: str) -> str:
  aliases = {
    "structure_rhythm": "structure_rhythm_analysis",
    "structure_rhythm_analysis": "structure_rhythm_analysis",
    "value_delivery": "value_delivery",
    "value_delivery_analysis": "value_delivery",
    "hook": "hook_analysis",
    "hook_analysis": "hook_analysis",
  }
  return aliases.get(str(capability or ""), str(capability or ""))


def _golden_finding(index: int, finding: Any) -> Any:
  from agent_service.retrieval.benchmark import GoldenFinding

  return GoldenFinding(f"g{index}", finding.skill_code, finding.label, finding.required_evidence_refs, finding.finding_type)


def _predicted_finding(index: int, finding: AgentEvalFinding) -> Any:
  from agent_service.retrieval.benchmark import PredictedFinding

  return PredictedFinding(
    f"p{index}",
    finding.skill_code,
    finding.label,
    finding.required_evidence_refs,
    supported=bool(finding.required_evidence_refs),
    finding_type=finding.finding_type,
  )


def _evaluate_agent_findings(expected: list[Any], predicted: list[Any]) -> dict[str, float]:
  expected_keys = {_agent_finding_key(item.skill_code, item.label, item.finding_type) for item in expected}
  predicted_keys = [_agent_finding_key(item.skill_code, item.label, item.finding_type) for item in predicted]
  predicted_key_set = set(predicted_keys)
  true_positive = len(expected_keys & predicted_key_set)
  precision = true_positive / len(predicted_keys) if predicted_keys else 0.0
  recall = true_positive / len(expected_keys) if expected_keys else 0.0
  f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
  grounded = [item for item in predicted if item.evidence_refs]
  unsupported = [item for item in predicted if not item.supported or not item.evidence_refs]
  return {
    "findingPrecision": precision,
    "findingRecall": recall,
    "findingF1": f1,
    "evidenceRefPresenceRate": len(grounded) / len(predicted) if predicted else 0.0,
    "evidenceGroundingRate": len(grounded) / len(predicted) if predicted else 0.0,
    "unsupportedFindingRate": len(unsupported) / len(predicted) if predicted else 0.0,
  }


def _expected_scope(case: Any) -> set[str]:
  primary_skill = str(getattr(case, "primary_skill", "") or "")
  if primary_skill and primary_skill != "cross_skill_ambiguity":
    return {primary_skill}
  return {finding.skill_code for finding in case.expected_findings if finding.skill_code}


def _finding_key(finding: AgentEvalFinding) -> str:
  return f"{finding.skill_code}:{finding.finding_type or finding.label}"


def _agent_finding_key(skill_code: str, label: str, finding_type: str = "") -> str:
  match_value = finding_type or label
  return f"{skill_code}:{' '.join((match_value or '').lower().split())}"


def _is_abstention_case(case: Any) -> bool:
  return any(finding.finding_type in {"evidence_gap", "abstain", "insufficient_evidence"} for finding in case.expected_findings)


def _has_abstention_prediction(findings: list[AgentEvalFinding], expected_scope: set[str]) -> bool:
  abstention_types = {"evidence_gap", "abstain", "insufficient_evidence"}
  return any(
    (not expected_scope or finding.skill_code in expected_scope)
    and finding.finding_type in abstention_types
    for finding in findings
  )


def _execution_failure_categories(diagnostics: list[dict[str, Any]]) -> dict[str, int]:
  categories: dict[str, int] = {}
  for diagnostic in diagnostics:
    failure = diagnostic.get("executionFailure") or {}
    if not failure:
      continue
    for category in _classify_failure(str(failure.get("message") or failure.get("failure_type") or "")):
      categories[category] = categories.get(category, 0) + 1
  return categories


def _classify_failure(message: str) -> list[str]:
  categories: list[str] = []
  if "Missing skill findings" in message:
    categories.append("MISSING_SKILL_FINDING")
  if "confidence below threshold" in message:
    categories.append("LOW_CONFIDENCE")
  if "Unresolved evidence gaps" in message:
    categories.append("UNRESOLVED_EVIDENCE_GAP")
  if "timeout" in message.lower():
    categories.append("TIMEOUT")
  if "parse" in message.lower():
    categories.append("PARSE_FAILURE")
  return categories or ["OTHER"]


def _model_call_count(output: dict[str, Any]) -> int:
  return sum(1 for step in output.get("step_traces") or [] if step.get("step_type") == "REASON" and step.get("status") == "FINAL")


def _agent_call_count(output: dict[str, Any]) -> int:
  return sum(1 for step in output.get("step_traces") or [] if step.get("node") == "skill_react" and step.get("step_type") == "REASON")


def _tool_call_count(output: dict[str, Any]) -> int:
  return sum(len(step.get("tool_calls") or []) for step in output.get("step_traces") or [])


def _eval_limits() -> HarnessLimits:
  settings = get_settings()
  return HarnessLimits(
    max_turns=settings.harness_max_turns,
    max_tokens=settings.harness_max_tokens,
    max_graph_steps=max(settings.harness_max_graph_steps, 80),
    timeout_seconds=settings.harness_timeout_seconds,
  )


def _component_mode_definitions() -> dict[str, dict[str, Any]]:
  runner = AgentEvalRunner([], dataset_version="component-definitions")
  definitions = runner.component_modes()
  for mode, definition in definitions.items():
    if mode not in STRICTLY_RUNNABLE_COMPONENTS:
      definition["status"] = "NOT_STRICTLY_ISOLATABLE"
  return definitions


def _load_skill_snapshots() -> dict[str, dict[str, str]]:
  from agent_service.graph.specialists import SKILL_BINDINGS

  snapshots = SkillLoader().load_many(SKILL_BINDINGS)
  return {
    agent_id: {
      "skill_id": snapshot["skill_id"],
      "version": snapshot["version"],
      "content_hash": snapshot["content_hash"],
    }
    for agent_id, snapshot in snapshots.items()
  }


def _dataset_ready(validation: dict[str, Any]) -> bool:
  return (
    validation["isValid"]
    and validation["datasetVersion"] == "video-diagnosis-agent-eval-v0.3-verified"
    and validation["caseCount"] == 24
    and validation["verifiedCount"] == 24
    and validation["pendingCount"] == 0
  )


def _not_run_report(dataset_path: Path, dataset_hash: str, validation: dict[str, Any], status: str) -> dict[str, Any]:
  settings = get_settings()
  return {
    "datasetVersion": validation.get("datasetVersion", ""),
    "datasetHashBefore": dataset_hash,
    "datasetHashAfter": _sha256(dataset_path),
    "status": status,
    "realLlmEval": "REAL_LLM_EVAL_NOT_RUN",
    "verifiedCaseCount": validation.get("verifiedCount", 0),
    "pendingCaseCount": validation.get("pendingCount", 0),
    "modelConfig": {
      "provider": _provider_name(settings.chat_base_url),
      "model": settings.chat_model,
      "baseUrl": _redacted_base_url(settings.chat_base_url),
      "temperature": 0.2,
    },
    "validation": validation,
  }


def _write_report(report: dict[str, Any], output_dir: Path) -> None:
  output_dir.mkdir(parents=True, exist_ok=True)
  (output_dir / "agent_ablation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
  (output_dir / "agent_ablation_report.md").write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
  lines = [
    "# Agent Ablation Evaluation Report",
    "",
    "## Evaluation Metadata",
    "",
    f"- Status: `{report.get('status', '')}`",
    f"- Real LLM eval: `{report.get('realLlmEval', '')}`",
    f"- Dataset version: `{report.get('datasetVersion', '')}`",
    f"- Dataset hash before: `{report.get('datasetHashBefore', '')}`",
    f"- Dataset hash after: `{report.get('datasetHashAfter', '')}`",
    f"- VERIFIED cases: `{report.get('verifiedCaseCount', 0)}`",
    f"- PENDING cases: `{report.get('pendingCaseCount', 0)}`",
    f"- Model config: `{json.dumps(report.get('modelConfig', {}), ensure_ascii=False)}`",
    "",
    "## Existing Retrieval Benchmark",
    "",
    "Retrieval evaluation is separate from Agent Evaluation. Existing retrieval results remain under `benchmark-reports/v0.5-final-test/`.",
    "",
    "## Component Ablation",
    "",
  ]
  lines.extend(_component_table(report))
  lines.extend(["", "## Architecture Ablation", ""])
  lines.extend(_architecture_table(report.get("architectureSummary", {})))
  lines.extend(["", "## Cross-Skill Ambiguity Subset", ""])
  lines.extend(_subset_table(report.get("crossSkillAmbiguitySubset", {})))
  lines.extend(["", "## Normal Cases", ""])
  lines.extend(_subset_table(report.get("normalCasesSubset", {})))
  lines.extend(["", "## Handoff Metrics", ""])
  lines.append(f"- Handoff success rate: `{(report.get('handoffMetrics') or {}).get('handoffSuccessRate', 0):.4f}`")
  lines.append(f"- Unnecessary handoff rate: `{(report.get('handoffMetrics') or {}).get('unnecessaryHandoffRate', 0):.4f}`")
  lines.extend(["", "## Failure Cases", ""])
  lines.append(f"- Execution failures: `{len(report.get('executionFailures') or [])}`")
  analysis = report.get("failureAnalysis") or {}
  lines.append(f"- False positives: `{analysis.get('falsePositiveCount', 0)}`")
  lines.append(f"- False negatives: `{analysis.get('falseNegativeCount', 0)}`")
  lines.append(f"- Wrong handoff cases: `{len(analysis.get('wrongHandoffCases') or [])}`")
  lines.append(f"- Missed handoff cases: `{len(analysis.get('missedHandoffCases') or [])}`")
  lines.append(f"- Unnecessary handoff cases: `{len(analysis.get('unnecessaryHandoffCases') or [])}`")
  if report.get("notes"):
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report["notes"])
  return "\n".join(lines)


def _component_table(report: dict[str, Any]) -> list[str]:
  definitions = report.get("componentModeDefinitions") or {}
  modes = (report.get("componentAblation") or {}).get("modes") or {}
  lines = [
    "| Mode | Status | Precision | Recall | F1 | Execution Success | Evidence Ref Presence | Unsupported | Latency | Model Calls | Agent Calls | Tool Calls | Tokens |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
  ]
  for mode in COMPONENT_MODES:
    metric = modes.get(mode) or _empty_metrics()
    status = (definitions.get(mode) or {}).get("status", "UNKNOWN")
    lines.append(_metric_row(mode, status, metric))
  return lines


def _architecture_table(summary: dict[str, Any]) -> list[str]:
  parallel = summary.get("PARALLEL_SKILLS") or _empty_metrics()
  multi = summary.get("SPECIALIST_MULTI_AGENT") or _empty_metrics()
  lines = ["| Metric | Parallel Skills | Specialist Multi-Agent | Delta |", "|---|---:|---:|---:|"]
  for key in [
    "findingPrecision",
    "findingRecall",
    "findingF1",
    "executionSuccessRate",
    "evidenceRefPresenceRate",
    "unsupportedFindingRate",
    "endToEndLatencyMs",
    "modelCallCount",
    "agentCallCount",
    "toolCallCount",
    "handoffCount",
    "replanCount",
  ]:
    delta = float(multi.get(key, 0.0)) - float(parallel.get(key, 0.0))
    lines.append(f"| {key} | {float(parallel.get(key, 0.0)):.4f} | {float(multi.get(key, 0.0)):.4f} | {delta:.4f} |")
  return lines


def _subset_table(subset: dict[str, Any]) -> list[str]:
  lines = [f"- Case count: `{subset.get('caseCount', 0)}`", ""]
  lines.extend(_architecture_table(subset.get("modes") or {}))
  return lines


def _metric_row(mode: str, status: str, metric: dict[str, Any]) -> str:
  return (
    f"| {mode} | {status} | {float(metric.get('findingPrecision', 0)):.4f} | "
    f"{float(metric.get('findingRecall', 0)):.4f} | {float(metric.get('findingF1', 0)):.4f} | "
    f"{float(metric.get('executionSuccessRate', 0)):.4f} | {float(metric.get('evidenceRefPresenceRate', metric.get('evidenceGroundingRate', 0))):.4f} | "
    f"{float(metric.get('unsupportedFindingRate', 0)):.4f} | "
    f"{float(metric.get('endToEndLatencyMs', 0)):.1f} | {float(metric.get('modelCallCount', 0)):.1f} | "
    f"{float(metric.get('agentCallCount', 0)):.1f} | {float(metric.get('toolCallCount', 0)):.1f} | "
    f"{metric.get('tokenUsage', 'unavailable')} |"
  )


def _empty_metrics() -> dict[str, Any]:
  return {
    "findingPrecision": 0.0,
    "findingRecall": 0.0,
    "findingF1": 0.0,
    "executionSuccessRate": 0.0,
    "executionFailureRate": 0.0,
    "abstentionAccuracy": 0.0,
    "abstentionCaseCount": 0.0,
    "correctAbstentionCount": 0.0,
    "evidenceRefPresenceRate": 0.0,
    "evidenceGroundingRate": 0.0,
    "unsupportedFindingRate": 0.0,
    "endToEndLatencyMs": 0.0,
    "modelCallCount": 0.0,
    "agentCallCount": 0.0,
    "toolCallCount": 0.0,
    "handoffCount": 0.0,
    "replanCount": 0.0,
    "tokenUsage": "unavailable",
  }


def _sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def _provider_name(base_url: str) -> str:
  if "deepseek" in base_url.lower():
    return "deepseek"
  if "openai" in base_url.lower():
    return "openai"
  return "openai-compatible"


def _redacted_base_url(base_url: str) -> str:
  return base_url.rstrip("/")


if __name__ == "__main__":
  main()
