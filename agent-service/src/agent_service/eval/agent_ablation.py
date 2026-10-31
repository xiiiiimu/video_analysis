from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from agent_service.config import get_settings
from agent_service.graph.builder import build_diagnosis_graph, build_parallel_skills_graph

AgentEvalMode = Literal[
  "VIDEO_EVIDENCE_ONLY",
  "VIDEO_EVIDENCE_PLUS_RAG",
  "RAG_PLUS_LOCAL_REACT",
  "FULL_SINGLE_WORKFLOW",
]
ArchitectureMode = Literal["PARALLEL_SKILLS", "SPECIALIST_MULTI_AGENT"]


@dataclass(frozen=True)
class AgentEvalFinding:
  skill_code: str
  label: str
  required_evidence_refs: list[str] = field(default_factory=list)
  acceptable_variants: list[str] = field(default_factory=list)
  finding_type: str = ""


@dataclass(frozen=True)
class AgentEvalGoldenCase:
  case_id: str
  verification_status: str
  input: dict[str, Any]
  expected_findings: list[AgentEvalFinding] = field(default_factory=list)
  primary_skill: str = ""
  case_type: str = ""
  cross_skill_ambiguity: bool = False
  expected_handoff_capability: str = ""
  expected_conflict_resolution: str = ""

  @property
  def is_verified(self) -> bool:
    return self.verification_status == "VERIFIED"


@dataclass(frozen=True)
class AgentEvalPrediction:
  case_id: str
  mode: str
  findings: list[AgentEvalFinding] = field(default_factory=list)
  execution_success: bool = True
  failure_reason: str = ""
  latency_ms: float = 0.0
  model_call_count: int = 0
  agent_call_count: int = 0
  tool_call_count: int = 0
  handoff_count: int = 0
  replan_count: int = 0
  token_usage: str | dict[str, Any] = "unavailable"


class AgentEvalRunner:
  """Shared deterministic evaluation harness for component and architecture ablations."""

  def __init__(
    self,
    golden_cases: list[AgentEvalGoldenCase],
    *,
    dataset_version: str,
    model: str = "scripted-or-real-runtime",
    knowledge_corpus_version: str = "runtime",
    skill_snapshots: dict[str, dict[str, str]] | None = None,
  ) -> None:
    self.golden_cases = list(golden_cases)
    self.dataset_version = dataset_version
    self.model = model
    self.knowledge_corpus_version = knowledge_corpus_version
    self.skill_snapshots = skill_snapshots or {}
    self.settings = get_settings()

  @classmethod
  def from_file(cls, path: Path) -> AgentEvalRunner:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = [
      AgentEvalGoldenCase(
        case_id=row["case_id"],
        verification_status=row.get("verification_status", "PENDING"),
        input=dict(row.get("input") or {}),
        expected_findings=[
          AgentEvalFinding(
            skill_code=item["skill_code"],
            label=item.get("label") or item.get("finding_type") or "",
            finding_type=item.get("finding_type", ""),
            required_evidence_refs=list(item.get("required_evidence_refs") or []),
            acceptable_variants=list(item.get("acceptable_variants") or []),
          )
          for item in row.get("expected_findings") or []
        ],
        primary_skill=str(row.get("primary_skill", "")),
        case_type=str(row.get("case_type", "")),
        cross_skill_ambiguity=bool(row.get("cross_skill_ambiguity", False)),
        expected_handoff_capability=str(row.get("expected_handoff_capability", "")),
        expected_conflict_resolution=str(row.get("expected_conflict_resolution", "")),
      )
      for row in payload.get("cases") or []
    ]
    return cls(cases, dataset_version=payload.get("dataset_version", "agent-eval-unknown"))

  def run_with_predictions(
    self,
    predictions: list[AgentEvalPrediction],
    *,
    report_kind: str,
  ) -> dict[str, Any]:
    started = _now_ms()
    verified = [case for case in self.golden_cases if case.is_verified]
    pending_count = sum(1 for case in self.golden_cases if case.verification_status == "PENDING")
    prediction_map = {(item.case_id, item.mode): item for item in predictions}
    modes = sorted({item.mode for item in predictions})
    aggregates = {
      mode: self._aggregate_mode(verified, [prediction_map[(case.case_id, mode)] for case in verified if (case.case_id, mode) in prediction_map])
      for mode in modes
    }
    ambiguity_cases = [case for case in verified if case.cross_skill_ambiguity]
    ambiguity = {
      mode: self._aggregate_mode(ambiguity_cases, [prediction_map[(case.case_id, mode)] for case in ambiguity_cases if (case.case_id, mode) in prediction_map])
      for mode in modes
    }
    status = "OK" if verified else "INSUFFICIENT_VERIFIED_GOLDEN_DATA"
    return {
      "datasetVersion": self.dataset_version,
      "reportKind": report_kind,
      "status": status,
      "verifiedCaseCount": len(verified),
      "pendingCaseCount": pending_count,
      "model": self.model,
      "knowledgeCorpusVersion": self.knowledge_corpus_version,
      "skillSnapshots": self.skill_snapshots,
      "runtimeConfig": self._runtime_config(),
      "runStartedAtMs": started,
      "runFinishedAtMs": _now_ms(),
      "modes": aggregates,
      "crossSkillAmbiguitySubset": ambiguity,
      "caseResults": [
        {
          "caseId": prediction.case_id,
          "mode": prediction.mode,
          "verificationStatus": next((case.verification_status for case in self.golden_cases if case.case_id == prediction.case_id), "UNKNOWN"),
          "latencyMs": prediction.latency_ms,
          "modelCallCount": prediction.model_call_count,
          "agentCallCount": prediction.agent_call_count,
          "toolCallCount": prediction.tool_call_count,
          "handoffCount": prediction.handoff_count,
          "replanCount": prediction.replan_count,
          "executionSuccess": prediction.execution_success,
          "failureReason": prediction.failure_reason,
          "tokenUsage": prediction.token_usage,
        }
        for prediction in predictions
      ],
    }

  def graph_for_architecture(self, mode: ArchitectureMode):
    if mode == "PARALLEL_SKILLS":
      return build_parallel_skills_graph()
    return build_diagnosis_graph()

  def component_modes(self) -> dict[str, dict[str, Any]]:
    return {
      "VIDEO_EVIDENCE_ONLY": {
        "rag": False,
        "localReact": False,
        "evaluator": "basic_result_check",
        "status": "NOT_ISOLATABLE_WITHOUT_RUNTIME_REWRITE",
      },
      "VIDEO_EVIDENCE_PLUS_RAG": {
        "rag": True,
        "localReact": False,
        "evaluator": "basic_result_check",
        "status": "NOT_ISOLATABLE_WITHOUT_RUNTIME_REWRITE",
      },
      "RAG_PLUS_LOCAL_REACT": {
        "rag": True,
        "localReact": True,
        "evaluator": False,
        "status": "NOT_ISOLATABLE_WITHOUT_RUNTIME_REWRITE",
      },
      "FULL_SINGLE_WORKFLOW": {
        "rag": True,
        "localReact": True,
        "evaluator": True,
        "graph": "build_parallel_skills_graph",
        "status": "RUNNABLE",
      },
    }

  def architecture_modes(self) -> dict[str, dict[str, Any]]:
    return {
      "PARALLEL_SKILLS": {"graph": "build_parallel_skills_graph", "supervisor": False, "structuredHandoff": False, "globalReplanning": False},
      "SPECIALIST_MULTI_AGENT": {"graph": "build_diagnosis_graph", "supervisor": True, "structuredHandoff": True, "globalReplanning": True},
    }

  def _aggregate_mode(
    self,
    cases: list[AgentEvalGoldenCase],
    predictions: list[AgentEvalPrediction],
  ) -> dict[str, Any]:
    if not cases:
      return _empty_metrics()
    prediction_by_case = {prediction.case_id: prediction for prediction in predictions}
    metric_rows: list[dict[str, float]] = []
    for case in cases:
      prediction = prediction_by_case.get(case.case_id, AgentEvalPrediction(case.case_id, "MISSING"))
      metric_rows.append(_finding_metrics(case, prediction))
    count = len(metric_rows)
    aggregated = {
      key: sum(row[key] for row in metric_rows) / count
      for key in [
        "findingPrecision",
        "findingRecall",
        "findingF1",
        "executionSuccessRate",
        "executionFailureRate",
        "evidenceRefPresenceRate",
        "evidenceGroundingRate",
        "unsupportedFindingRate",
        "conflictResolutionRate",
        "handoffSuccessRate",
        "endToEndLatencyMs",
        "modelCallCount",
        "agentCallCount",
        "toolCallCount",
        "handoffCount",
        "replanCount",
      ]
    }
    abstention_cases = sum(row["abstentionCaseCount"] for row in metric_rows)
    correct_abstentions = sum(row["correctAbstentionCount"] for row in metric_rows)
    aggregated["abstentionCaseCount"] = abstention_cases
    aggregated["correctAbstentionCount"] = correct_abstentions
    aggregated["abstentionAccuracy"] = correct_abstentions / abstention_cases if abstention_cases else 0.0
    return aggregated | {"tokenUsage": "unavailable"}

  def _runtime_config(self) -> dict[str, Any]:
    return {
      "maxReactIterations": self.settings.max_react_iterations,
      "maxGlobalReplans": self.settings.max_global_replans,
      "maxAgentHandoffs": self.settings.max_agent_handoffs,
      "retrievalTopK": self.settings.retrieval_top_k,
      "rerankEnabled": self.settings.rerank_enabled,
      "tokenUsage": "unavailable",
    }


def load_or_create_agent_eval_dataset(path: Path) -> list[AgentEvalGoldenCase]:
  if not path.exists():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_agent_eval_template(), ensure_ascii=False, indent=2), encoding="utf-8")
  return AgentEvalRunner.from_file(path).golden_cases


def write_agent_ablation_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "agent_ablation_report.json"
  md_path = output_dir / "agent_ablation_report.md"
  json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
  md_path.write_text(render_agent_ablation_markdown(report), encoding="utf-8")
  return json_path, md_path


def validate_agent_eval_dataset(path: Path) -> dict[str, Any]:
  payload = json.loads(path.read_text(encoding="utf-8"))
  cases = payload.get("cases") or []
  errors: list[str] = []
  seen_case_ids: set[str] = set()
  status_counts = {"VERIFIED": 0, "PENDING": 0, "REJECTED": 0}
  valid_statuses = set(status_counts)
  valid_source_types = {"EXISTING_FIXTURE", "EXISTING_BENCHMARK", "SYNTHETIC"}

  for index, case in enumerate(cases):
    case_id = str(case.get("case_id") or "")
    if not case_id:
      errors.append(f"cases[{index}] missing case_id")
    elif case_id in seen_case_ids:
      errors.append(f"duplicate case_id: {case_id}")
    seen_case_ids.add(case_id)

    status = str(case.get("verification_status") or "")
    if status not in valid_statuses:
      errors.append(f"{case_id} invalid verification_status: {status}")
    else:
      status_counts[status] += 1

    source_type = str(case.get("source_type") or "")
    if source_type and source_type not in valid_source_types:
      errors.append(f"{case_id} invalid source_type: {source_type}")

    findings = case.get("expected_findings")
    if not isinstance(findings, list):
      errors.append(f"{case_id} expected_findings must be a list")
      findings = []
    for finding_index, finding in enumerate(findings):
      _validate_finding(case_id, finding_index, finding, errors)

    if bool(case.get("cross_skill_ambiguity", False)):
      handoff = str(case.get("expected_handoff_capability") or "")
      if not handoff:
        errors.append(f"{case_id} cross_skill_ambiguity=true requires expected_handoff_capability or NONE")

  return {
    "datasetVersion": payload.get("dataset_version", ""),
    "caseCount": len(cases),
    "verifiedCount": status_counts["VERIFIED"],
    "pendingCount": status_counts["PENDING"],
    "rejectedCount": status_counts["REJECTED"],
    "errors": errors,
    "isValid": not errors,
  }


def write_agent_eval_review_markdown(dataset_path: Path, output_path: Path) -> Path:
  payload = json.loads(dataset_path.read_text(encoding="utf-8"))
  lines = [
    "# Agent Evaluation Golden Case Review",
    "",
    f"- Dataset version: `{payload.get('dataset_version', '')}`",
    f"- Dataset role: `{payload.get('dataset_role', 'EVAL_CANDIDATE')}`",
    "- Rule: only human-reviewed cases may be changed to `VERIFIED`.",
    "",
  ]
  for case in payload.get("cases") or []:
    lines.extend(_review_case_lines(case))
  output_path.parent.mkdir(parents=True, exist_ok=True)
  output_path.write_text("\n".join(lines), encoding="utf-8")
  return output_path


def render_agent_ablation_markdown(report: dict[str, Any]) -> str:
  lines = [
    "# Agent Ablation Evaluation Report",
    "",
    f"- Dataset version: `{report['datasetVersion']}`",
    f"- Status: `{report['status']}`",
    f"- VERIFIED cases: `{report['verifiedCaseCount']}`",
    f"- PENDING cases: `{report['pendingCaseCount']}`",
    f"- Model: `{report['model']}`",
    f"- Token usage: `{report['runtimeConfig'].get('tokenUsage', 'unavailable')}`",
    "",
    "## Retrieval Benchmark Summary",
    "",
    "Retrieval evaluation is unchanged. Use existing reports under `benchmark-reports/v0.5-final-test/` for Recall@1/3/5, MRR, and HardNegativeAboveExpectedRate.",
    "",
    "## Component Ablation",
    "",
    "| Mode | Finding Precision | Finding Recall | Finding F1 | Execution Success | Evidence Ref Presence | Unsupported Finding | Latency | Model Calls | Tool Calls | Tokens |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
  ]
  for mode, metrics in report["componentAblation"]["modes"].items():
    lines.append(_mode_row(mode, metrics))
  lines.extend([
    "",
    "## Architecture Ablation",
    "",
    "| Metric | Parallel Skills | Specialist Multi-Agent | Delta |",
    "|---|---:|---:|---:|",
  ])
  lines.extend(_architecture_rows(report["architectureAblation"]["modes"]))
  lines.extend([
    "",
    "## Cross-Skill Ambiguity Subset",
    "",
    "| Metric | Parallel Skills | Specialist Multi-Agent | Delta |",
    "|---|---:|---:|---:|",
  ])
  lines.extend(_architecture_rows(report["architectureAblation"]["crossSkillAmbiguitySubset"]))
  if report["status"] == "INSUFFICIENT_VERIFIED_GOLDEN_DATA":
    lines.extend([
      "",
      "## Conclusion",
      "",
      "INSUFFICIENT_VERIFIED_GOLDEN_DATA: no formal Agent Finding quality conclusion can be drawn. Harness and deterministic tests are available, but Finding F1 must not be reported as a real benchmark until human VERIFIED Agent Golden Cases exist.",
    ])
  return "\n".join(lines)


def _finding_metrics(case: AgentEvalGoldenCase, prediction: AgentEvalPrediction) -> dict[str, float]:
  expected_scope = _expected_scope(case)
  golden = [
    _to_benchmark_golden(index, finding)
    for index, finding in enumerate(case.expected_findings)
  ]
  predicted = [
    _to_benchmark_predicted(index, finding)
    for index, finding in enumerate(prediction.findings)
    if not expected_scope or finding.skill_code in expected_scope
  ]
  base = _evaluate_agent_findings(golden, predicted)
  abstention_case = _is_abstention_case(case)
  correct_abstention = 1.0 if abstention_case and _has_abstention_prediction(prediction.findings, expected_scope) else 0.0
  conflict_resolution = 0.0
  handoff_success = 0.0
  if case.cross_skill_ambiguity:
    expected_keys = {_structured_key(finding) for finding in case.expected_findings}
    predicted_keys = {_structured_key(finding) for finding in prediction.findings}
    conflict_resolution = 1.0 if expected_keys and expected_keys <= predicted_keys else 0.0
    handoff_success = 1.0 if prediction.handoff_count > 0 and prediction.replan_count > 0 else 0.0
  return {
    **base,
    "executionSuccessRate": 1.0 if prediction.execution_success else 0.0,
    "executionFailureRate": 0.0 if prediction.execution_success else 1.0,
    "abstentionCaseCount": 1.0 if abstention_case else 0.0,
    "correctAbstentionCount": correct_abstention,
    "abstentionAccuracy": correct_abstention if abstention_case else 0.0,
    "conflictResolutionRate": conflict_resolution,
    "handoffSuccessRate": handoff_success,
    "endToEndLatencyMs": prediction.latency_ms,
    "modelCallCount": float(prediction.model_call_count),
    "agentCallCount": float(prediction.agent_call_count),
    "toolCallCount": float(prediction.tool_call_count),
    "handoffCount": float(prediction.handoff_count),
    "replanCount": float(prediction.replan_count),
  }


def _validate_finding(case_id: str, finding_index: int, finding: Any, errors: list[str]) -> None:
  if not isinstance(finding, dict):
    errors.append(f"{case_id} expected_findings[{finding_index}] must be an object")
    return
  if not str(finding.get("skill_code") or ""):
    errors.append(f"{case_id} expected_findings[{finding_index}] missing skill_code")
  if "required_evidence_refs" in finding and not isinstance(finding["required_evidence_refs"], list):
    errors.append(f"{case_id} expected_findings[{finding_index}] required_evidence_refs must be a list")
  for ref in finding.get("required_evidence_refs") or []:
    if not _valid_evidence_ref(str(ref)):
      errors.append(f"{case_id} expected_findings[{finding_index}] invalid evidence ref: {ref}")
  if "acceptable_variants" in finding and not isinstance(finding["acceptable_variants"], list):
    errors.append(f"{case_id} expected_findings[{finding_index}] acceptable_variants must be a list")


def _valid_evidence_ref(ref: str) -> bool:
  return ref.startswith(("ASR:", "OCR:", "FRAME:", "META:", "METADATA:", "KNOWLEDGE:"))


def _review_case_lines(case: dict[str, Any]) -> list[str]:
  target = (case.get("input") or {}).get("target_evidence") or {}
  references = (case.get("input") or {}).get("reference_evidence") or []
  findings = case.get("expected_findings") or []
  lines = [
    f"## {case.get('case_id', '')}",
    "",
    f"- Source type: `{case.get('source_type', '')}`",
    f"- Primary skill: `{case.get('primary_skill', '')}`",
    f"- Case type: `{case.get('case_type', '')}`",
    f"- Candidate only: `{case.get('candidate_only', True)}`",
    "",
    "### Evidence",
    "",
    f"- ASR: {target.get('asr', target.get('transcriptText', ''))}",
    f"- OCR: {target.get('ocr', target.get('ocrJson', ''))}",
    f"- Metadata: {target.get('metadata', target.get('sceneJson', ''))}",
    f"- Frame / Knowledge refs: {', '.join(target.get('evidence_refs') or [])}",
    f"- Reference evidence count: `{len(references)}`",
    "",
    "### Candidate Finding",
    "",
  ]
  for finding in findings:
    lines.extend(
      [
        f"- Skill: `{finding.get('skill_code', '')}`",
        f"- Type: `{finding.get('finding_type', '')}`",
        f"- Label: {finding.get('label', '')}",
        f"- Candidate Evidence Refs: {', '.join(finding.get('required_evidence_refs') or [])}",
        f"- Acceptable Variants: {', '.join(finding.get('acceptable_variants') or [])}",
      ]
    )
  lines.extend(
    [
      "",
      f"- Cross-Skill Ambiguity? `{case.get('cross_skill_ambiguity', False)}`",
      f"- Expected Handoff? `{case.get('expected_handoff_capability', '')}`",
      f"- Review notes: {case.get('review_notes', '')}",
      "",
      "### Human Review",
      "",
      "- [ ] Finding 正确",
      "- [ ] Evidence 正确",
      "- [ ] Finding 需要修改",
      "- [ ] Evidence 需要修改",
      "- [ ] 应该是 insufficient evidence",
      "- [ ] Cross-skill 标记正确",
      "",
      "Final Finding:",
      "",
      "<人工填写>",
      "",
      "Reviewer Notes:",
      "",
      "<人工填写>",
      "",
    ]
  )
  return lines


def _to_benchmark_golden(index: int, finding: AgentEvalFinding):
  from agent_service.retrieval.benchmark import GoldenFinding

  return GoldenFinding(f"g{index}", finding.skill_code, finding.label, finding.required_evidence_refs, finding.finding_type)


def _to_benchmark_predicted(index: int, finding: AgentEvalFinding):
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


def _agent_finding_key(skill_code: str, label: str, finding_type: str = "") -> str:
  match_value = finding_type or label
  return f"{skill_code}:{' '.join((match_value or '').lower().split())}"


def _expected_scope(case: AgentEvalGoldenCase) -> set[str]:
  if case.primary_skill and case.primary_skill != "cross_skill_ambiguity":
    return {case.primary_skill}
  return {finding.skill_code for finding in case.expected_findings if finding.skill_code}


def _structured_key(finding: AgentEvalFinding) -> str:
  return f"{finding.skill_code}:{finding.finding_type or finding.label}"


def _is_abstention_case(case: AgentEvalGoldenCase) -> bool:
  return any(finding.finding_type in {"evidence_gap", "abstain", "insufficient_evidence"} for finding in case.expected_findings)


def _has_abstention_prediction(findings: list[AgentEvalFinding], expected_scope: set[str]) -> bool:
  abstention_types = {"evidence_gap", "abstain", "insufficient_evidence"}
  return any(
    (not expected_scope or finding.skill_code in expected_scope)
    and finding.finding_type in abstention_types
    for finding in findings
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
    "conflictResolutionRate": 0.0,
    "handoffSuccessRate": 0.0,
    "endToEndLatencyMs": 0.0,
    "modelCallCount": 0.0,
    "agentCallCount": 0.0,
    "toolCallCount": 0.0,
    "handoffCount": 0.0,
    "replanCount": 0.0,
    "tokenUsage": "unavailable",
  }


def _mode_row(mode: str, metrics: dict[str, Any]) -> str:
  return (
    f"| {mode} | {metrics['findingPrecision']:.4f} | {metrics['findingRecall']:.4f} | "
    f"{metrics['findingF1']:.4f} | {metrics['executionSuccessRate']:.4f} | "
    f"{metrics.get('evidenceRefPresenceRate', metrics['evidenceGroundingRate']):.4f} | "
    f"{metrics['unsupportedFindingRate']:.4f} | {metrics['endToEndLatencyMs']:.1f} | "
    f"{metrics['modelCallCount']:.1f} | {metrics['toolCallCount']:.1f} | {metrics.get('tokenUsage', 'unavailable')} |"
  )


def _architecture_rows(modes: dict[str, dict[str, Any]]) -> list[str]:
  parallel = modes.get("PARALLEL_SKILLS", _empty_metrics())
  multi = modes.get("SPECIALIST_MULTI_AGENT", _empty_metrics())
  rows = []
  for key in [
    "findingPrecision",
    "findingRecall",
    "findingF1",
    "executionSuccessRate",
    "evidenceRefPresenceRate",
    "unsupportedFindingRate",
    "conflictResolutionRate",
    "handoffSuccessRate",
    "endToEndLatencyMs",
    "agentCallCount",
    "toolCallCount",
    "handoffCount",
    "replanCount",
  ]:
    delta = float(multi.get(key, 0.0)) - float(parallel.get(key, 0.0))
    rows.append(f"| {key} | {float(parallel.get(key, 0.0)):.4f} | {float(multi.get(key, 0.0)):.4f} | {delta:.4f} |")
  return rows


def _agent_eval_template() -> dict[str, Any]:
  return {
    "dataset_version": "video-diagnosis-agent-eval-v0.1",
    "annotation_policy": "Only human-reviewed cases may set verification_status=VERIFIED. PENDING cases are excluded from formal metrics.",
    "cases": [
      {
        "case_id": "agent-case-hook-value-boundary-001",
        "verification_status": "PENDING",
        "input": {
          "target_evidence": {},
          "reference_evidence": [],
        },
        "expected_findings": [
          {
            "skill_code": "hook_analysis",
            "finding_type": "opening_value_ambiguity",
            "label": "",
            "required_evidence_refs": [],
            "acceptable_variants": [],
          }
        ],
        "cross_skill_ambiguity": True,
        "expected_handoff_capability": "value_delivery",
        "expected_conflict_resolution": "",
      }
    ],
  }


def _now_ms() -> int:
  return int(time.time() * 1000)
