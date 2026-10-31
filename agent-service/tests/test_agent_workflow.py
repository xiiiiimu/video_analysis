from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agent_service.graph.builder import build_diagnosis_graph, build_parallel_skills_graph
from agent_service.graph.diagnosis_skill import run_diagnosis_skill
from agent_service.graph.nodes.evaluator import evaluator_node
from agent_service.graph.react_loop import DiagnosisReActLoop
from agent_service.graph.result_contract import evaluate_handoff_gate, normalize_specialist_result
from agent_service.graph.specialists import (
  SPECIALIST_AGENTS,
  CapabilityRegistry,
  SpecialistAgentDefinition,
)
from agent_service.graph.state import CORE_DIAGNOSIS_SKILLS
from agent_service.graph.supervisor import CentralSupervisor
from agent_service.harness.runner import HarnessRunner
from agent_service.harness.types import HarnessLimits
from agent_service.retrieval.benchmark import aggregate_metrics, evaluate_ranked_refs
from agent_service.retrieval.hybrid import InMemoryHybridKnowledgeRetriever
from agent_service.retrieval.models import KnowledgeEvidence, KnowledgeQuery
from agent_service.retrieval.rrf import reciprocal_rank_fusion
from agent_service.skills import SkillLoader, SkillLoadError


class FakeHarness:
  def __init__(self, tool: Any | None = None) -> None:
    self.calls: list[dict[str, Any]] = []
    self._tool = tool

  def call_tool(self, ctx: Any, tool_name: str, **args: Any) -> Any:
    self.calls.append({"tool_name": tool_name, "args": args})
    if self._tool:
      return self._tool(tool_name, **args)
    return _rich_evidence()


class FakeGraphHarness:
  def on_graph_step(self, ctx: Any) -> None:
    return None


def _rich_evidence() -> dict[str, Any]:
  return {
    "targetEvidence": {
      "videoAssetId": "target-1",
      "transcriptText": "",
      "keyframes": ["00:00:00-00:00:03"],
      "sceneJson": "{\"duration\": 12}",
      "ocrJson": "{\"ocr\":[{\"text\":\"前三秒直接给出痛点\"}]}",
    },
    "referenceEvidence": [
      {
        "videoAssetId": "ref-1",
        "transcriptText": "",
        "keyframes": ["ref:00:00:00-00:00:03"],
        "ocrJson": "{\"ocr\":[{\"text\":\"参考视频先讲收益\"}]}",
      }
    ],
  }


def _knowledge_payload(ref: str = "KNOWLEDGE:hook-pattern-opening-pain-v1") -> dict[str, Any]:
  return {
    "items": [
      {
        "id": ref.replace("KNOWLEDGE:", ""),
        "evidenceRef": ref,
        "knowledgeType": "HOOK_PATTERN",
        "skillCode": "hook_analysis",
        "category": "",
        "title": "前三秒钩子",
        "content": "开头 3 秒应优先呈现强痛点或明确收益。",
        "source": "test",
        "score": 0.92,
      }
    ],
    "trace": {
      "skill_code": "hook_analysis",
      "query": "前三秒 钩子 收益",
      "knowledge_type": "DOMAIN_KNOWLEDGE",
      "retrieval_method": "HYBRID_RRF_RERANK",
      "bm25_count": 1,
      "vector_count": 1,
      "rrf_count": 1,
      "rerank_count": 1,
      "top_k": 5,
      "latency_ms": 3,
      "selected_evidence_refs": [ref],
    },
  }


def _empty_knowledge_payload() -> dict[str, Any]:
  payload = _knowledge_payload()
  payload["items"] = []
  payload["trace"]["selected_evidence_refs"] = []
  payload["trace"]["bm25_count"] = 0
  payload["trace"]["vector_count"] = 0
  payload["trace"]["rrf_count"] = 0
  payload["trace"]["rerank_count"] = 0
  return payload


def _poor_evidence() -> dict[str, Any]:
  return {
    "targetEvidence": {
      "videoAssetId": "target-1",
      "transcriptText": "",
      "keyframes": [],
      "sceneJson": "",
      "ocrJson": "",
    },
    "referenceEvidence": [],
  }


def _keyframe_only_evidence() -> dict[str, Any]:
  evidence = _poor_evidence()
  evidence["targetEvidence"]["keyframes"] = ["00:00:00-00:00:03"]
  return evidence


def _skill(skill_key: str) -> dict[str, Any]:
  return next(item for item in CORE_DIAGNOSIS_SKILLS if item["skill_key"] == skill_key)


def _harness(tools: dict[str, Any]) -> HarnessRunner:
  return HarnessRunner(
    compiled_graph=build_diagnosis_graph(),
    tools=tools,
    limits=HarnessLimits(max_turns=80, max_tokens=32000, max_graph_steps=120, timeout_seconds=30),
  )


def _tools(evidence: dict[str, Any], saved: list[dict[str, Any]] | None = None) -> dict[str, Any]:
  saved = saved if saved is not None else []
  return {
    "get_job_context": lambda job_id: {"jobId": job_id, "targetVideoId": "target-1"},
    "get_video_evidence": lambda job_id: evidence,
    "retrieve_knowledge": lambda **kwargs: _knowledge_payload(),
    "save_diagnosis_hypothesis": lambda job_id, hypothesis: saved.append(hypothesis)
    or {"findingId": f"finding-{len(saved)}"},
    "save_agent_draft_result": lambda job_id, draft_observations: {"ok": True},
    "report_agent_progress": lambda **kwargs: {"ok": True},
  }


def _patch_diagnosis(monkeypatch: pytest.MonkeyPatch, confidence: float = 0.82) -> dict[str, int]:
  calls: dict[str, int] = {}

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    calls[dimension] = calls.get(dimension, 0) + 1
    target = evidence_pack.get("targetEvidence") or {}
    return {
      "dimension": dimension,
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target opening can be sharper.",
      "suggested_action": "Move value text earlier.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "counter_evidence": "Narrative style may be slower.",
      "confidence": confidence,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)
  return calls


def test_skill_first_round_final_without_tool(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness()

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-1",
    job_context={},
    evidence_pack=_rich_evidence(),
    harness=harness,
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert result["react_iterations"] == 1
  assert harness.calls == []
  assert any(step["step_type"] == "FINAL" for step in result["step_traces"])


def test_skill_load_success() -> None:
  snapshot = SkillLoader().load(agent_id="hook_agent", skill_id="hook_analysis")

  assert snapshot.skill_id == "hook_analysis"
  assert snapshot.version == "1.0.0"
  assert snapshot.content
  assert len(snapshot.content_hash) == 64


def test_missing_skill_fail_fast(tmp_path: Path) -> None:
  with pytest.raises(SkillLoadError) as exc:
    SkillLoader(tmp_path).load(agent_id="missing_agent", skill_id="missing_skill")

  assert "agent_id=missing_agent" in str(exc.value)
  assert "skill_id=missing_skill" in str(exc.value)
  assert "path=" in str(exc.value)


def test_skill_snapshot_per_run(tmp_path: Path) -> None:
  skill_dir = tmp_path / "hook_analysis"
  skill_dir.mkdir()
  skill_file = skill_dir / "skill.md"
  skill_file.write_text("skill_id: hook_analysis\nversion: 1.0.0\n\nv1 procedure", encoding="utf-8")
  loader = SkillLoader(tmp_path)

  run1_snapshot = loader.load(agent_id="hook_agent", skill_id="hook_analysis")
  skill_file.write_text("skill_id: hook_analysis\nversion: 2.0.0\n\nv2 procedure", encoding="utf-8")
  run2_snapshot = loader.load(agent_id="hook_agent", skill_id="hook_analysis")

  assert run1_snapshot.version == "1.0.0"
  assert "v1 procedure" in run1_snapshot.content
  assert run2_snapshot.version == "2.0.0"
  assert run1_snapshot.content_hash != run2_snapshot.content_hash


def test_knowledge_independent_from_skill() -> None:
  snapshot = SkillLoader().load(agent_id="hook_agent", skill_id="hook_analysis")
  corpus = [KnowledgeEvidence("k-hook", "HOOK_PATTERN", "hook_analysis", "", "hook", "前三秒收益", "test")]
  result = InMemoryHybridKnowledgeRetriever(corpus).retrieve(
    KnowledgeQuery("前三秒 收益", "hook_analysis", "DOMAIN_KNOWLEDGE")
  )

  assert result.items[0].id == "k-hook"
  assert "前三秒收益" not in snapshot.content


def test_runtime_diagnosis_uses_skill_snapshot_content(monkeypatch: pytest.MonkeyPatch) -> None:
  seen: dict[str, str] = {}

  def fake_diagnose(
    dimension: str,
    job_context: dict[str, Any],
    evidence_pack: dict[str, Any],
    skill_procedure: str = "",
  ) -> dict[str, Any]:
    seen["skill_procedure"] = skill_procedure
    return {
      "dimension": dimension,
      "observation": "uses snapshot",
      "difference_text": "diff",
      "hypothesis_text": "hypothesis",
      "suggested_action": "action",
      "target_frame_refs": ["00:00:00-00:00:03"],
      "reference_frame_refs": [],
      "counter_evidence": "",
      "confidence": 0.9,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  run_diagnosis_skill(
    {
      "skill_key": "hook_analysis",
      "dimension": "HOOK",
      "goal": "test",
      "skill_snapshot": {
        "skill_id": "hook_analysis",
        "version": "1.0.0",
        "content": "skill_id: hook_analysis\nversion: 1.0.0\n\nv1 procedure",
        "content_hash": "hash-v1",
      },
    },
    {},
    _rich_evidence(),
  )

  assert "v1 procedure" in seen["skill_procedure"]


def test_skill_need_tool_observation_then_final(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness(lambda tool_name, **args: _rich_evidence())

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-2",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=harness,
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert result["react_iterations"] == 2
  assert harness.calls[0]["tool_name"] == "get_video_evidence"
  assert result["observations"][0]["observation_type"] == "FRAME_TEXT"
  assert [step["step_type"] for step in result["step_traces"]] == [
    "REASON",
    "ACTION",
    "OBSERVATION",
    "REASON",
    "SPECIALIST_RESULT",
    "FINAL",
  ]


def test_skill_two_different_evidence_tools_then_final(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  calls = {"count": 0}

  def tool(tool_name: str, **args: Any) -> dict[str, Any]:
    calls["count"] += 1
    return _keyframe_only_evidence() if calls["count"] == 1 else _rich_evidence()

  result = DiagnosisReActLoop(
    skill=_skill("structure_rhythm_analysis"),
    job_id="job-3",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=FakeHarness(tool),
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert [item["observation_type"] for item in result["observations"]] == ["KEY_FRAME", "VIDEO_METADATA"]
  assert result["react_iterations"] == 3


def test_exceeding_max_react_iterations_fails(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  def always_retry(self: DiagnosisReActLoop) -> dict[str, Any]:
    return {"status": "RETRY", "reasoning_summary": "synthetic retry loop"}

  monkeypatch.setattr(DiagnosisReActLoop, "_reason", always_retry)

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-4",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=FakeHarness(lambda tool_name, **args: _poor_evidence()),
    harness_ctx=None,
    max_iterations=2,
  ).run()

  assert result["status"] == "COMPLETED"
  assert result["finding"]["outcome"] == "ABSTAIN"
  assert "Exceeded max_react_iterations" in result["finding"]["reason"]


def test_missing_video_evidence_abstains_without_repeating_tool(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness(lambda tool_name, **args: _poor_evidence())

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-missing-video-evidence",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=harness,
    harness_ctx=None,
    max_iterations=3,
  ).run()

  assert result["status"] == "COMPLETED"
  assert result["finding"]["outcome"] == "ABSTAIN"
  assert "Opening key frame evidence remains unavailable" in result["finding"]["reason"]
  assert [item["observation_type"] for item in result["observations"]] == ["FRAME_TEXT", "KEY_FRAME"]


def test_all_abstain_evidence_gaps_complete_without_retry_loop(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = HarnessRunner(
    compiled_graph=build_diagnosis_graph(),
    tools=_tools(_poor_evidence()),
    limits=HarnessLimits(max_turns=20, max_tokens=32000, max_graph_steps=120, timeout_seconds=30),
  )

  result = harness.run("job-all-abstain", {"job_id": "job-all-abstain"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED_WITH_GAPS"
  assert result.output["iteration_count"] == 0
  assert {item.get("outcome") for item in result.output["findings"]} == {"ABSTAIN"}
  assert all(item["decision"] == "PASS" for item in result.output["evaluation_results"])


def test_non_whitelisted_tool_request_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  def forbidden_reason(self: DiagnosisReActLoop) -> dict[str, Any]:
    return {
      "status": "NEED_TOOL",
      "reasoning_summary": "Bad request",
      "requested_evidence_type": "KEY_FRAME",
      "tool_input": {},
    }

  monkeypatch.setattr(DiagnosisReActLoop, "_reason", forbidden_reason)

  result = DiagnosisReActLoop(
    skill=_skill("value_delivery_analysis"),
    job_id="job-5",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=FakeHarness(),
    harness_ctx=None,
  ).run()

  assert result["status"] == "FAILED"
  assert "not allowed" in result["error"]


def test_specialist_tool_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  restricted_agent = SpecialistAgentDefinition(
    agent_id="restricted_hook_agent",
    role="RestrictedHook",
    goal="test isolation",
    capabilities=("hook_analysis",),
    allowed_tools=("retrieve_knowledge",),
    skill_binding="hook_analysis",
    knowledge_namespaces=("hook_analysis",),
  )

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    agent=restricted_agent,
    job_id="job-isolation",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=FakeHarness(lambda tool_name, **args: _rich_evidence()),
    harness_ctx=None,
  ).run()

  assert result["status"] == "FAILED"
  assert "not allowed to call get_video_evidence" in result["error"]


def test_tool_call_failure_fails_skill(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  def failing_tool(tool_name: str, **args: Any) -> dict[str, Any]:
    raise RuntimeError("java evidence api unavailable")

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-6",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=FakeHarness(failing_tool),
    harness_ctx=None,
  ).run()

  assert result["status"] == "FAILED"
  assert "java evidence api unavailable" in result["error"]


def test_observation_participates_in_next_reason(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness(lambda tool_name, **args: _rich_evidence())

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-7",
    job_context={},
    evidence_pack=_poor_evidence(),
    harness=harness,
    harness_ctx=None,
  ).run()

  second_reason = [step for step in result["step_traces"] if step["step_type"] == "REASON"][1]
  assert second_reason["input_summary"] == "FRAME_TEXT success=True refs=3"


def test_skill_no_knowledge_does_not_call_retriever(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness(lambda tool_name, **args: _knowledge_payload())

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k0",
    job_context={},
    evidence_pack=_rich_evidence(),
    harness=harness,
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert harness.calls == []
  assert result["finding"]["knowledge_evidence_refs"] == []


def test_skill_requests_domain_knowledge_then_final(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness(lambda tool_name, **args: _knowledge_payload())

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k1",
    job_context={"needKnowledge": True},
    evidence_pack=_rich_evidence(),
    harness=harness,
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert harness.calls[0]["tool_name"] == "retrieve_knowledge"
  assert harness.calls[0]["args"]["knowledge_type"] == "DOMAIN_KNOWLEDGE"
  assert result["finding"]["video_evidence_refs"]
  assert result["finding"]["knowledge_evidence_refs"] == ["KNOWLEDGE:hook-pattern-opening-pain-v1"]
  assert result["observations"][0]["retrieval_trace"]["retrieval_method"] == "HYBRID_RRF_RERANK"


def test_skill_uses_video_and_knowledge_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  calls = {"count": 0}

  def tool(tool_name: str, **args: Any) -> dict[str, Any]:
    calls["count"] += 1
    return _rich_evidence() if tool_name == "get_video_evidence" else _knowledge_payload()

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k2",
    job_context={"needKnowledge": True},
    evidence_pack=_poor_evidence(),
    harness=FakeHarness(tool),
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert [call["tool_name"] for call in result["observations"]] == ["get_video_evidence", "retrieve_knowledge"]
  assert result["finding"]["video_evidence_refs"]
  assert result["finding"]["knowledge_evidence_refs"]


def test_knowledge_retrieval_no_result_creates_gap(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = FakeHarness(lambda tool_name, **args: _empty_knowledge_payload())

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k3",
    job_context={"needKnowledge": True},
    evidence_pack=_rich_evidence(),
    harness=harness,
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert result["finding"]["knowledge_evidence_refs"] == []
  assert any(gap["evidenceType"] == "DOMAIN_KNOWLEDGE" for gap in result["finding"]["evidence_gaps"])


def test_knowledge_retrieval_exception_degrades_to_video_only(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  def failing_tool(tool_name: str, **args: Any) -> dict[str, Any]:
    raise RuntimeError("retriever timeout")

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k4",
    job_context={"needKnowledge": True},
    evidence_pack=_rich_evidence(),
    harness=FakeHarness(failing_tool),
    harness_ctx=None,
  ).run()

  assert result["status"] == "COMPLETED"
  assert result["observations"][0]["payload"]["degraded"] is True
  assert "retriever timeout" in result["observations"][0]["error"]
  assert result["finding"]["knowledge_evidence_refs"] == []


def test_disallowed_knowledge_type_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  def forbidden_reason(self: DiagnosisReActLoop) -> dict[str, Any]:
    return {
      "status": "NEED_TOOL",
      "reasoning_summary": "Bad knowledge request",
      "requested_evidence_type": "CUSTOM_KNOWLEDGE",
      "tool_input": {},
    }

  monkeypatch.setattr(DiagnosisReActLoop, "_reason", forbidden_reason)

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k5",
    job_context={"needKnowledge": True},
    evidence_pack=_rich_evidence(),
    harness=FakeHarness(lambda tool_name, **args: _knowledge_payload()),
    harness_ctx=None,
  ).run()

  assert result["status"] == "FAILED"
  assert "not allowed" in result["error"]


def test_rag_observation_enters_next_reason(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-k6",
    job_context={"needKnowledge": True},
    evidence_pack=_rich_evidence(),
    harness=FakeHarness(lambda tool_name, **args: _knowledge_payload()),
    harness_ctx=None,
  ).run()

  second_reason = [step for step in result["step_traces"] if step["step_type"] == "REASON"][1]
  assert second_reason["input_summary"] == "DOMAIN_KNOWLEDGE success=True refs=1"


def test_evaluator_rejects_knowledge_only_finding() -> None:
  state = {
    "run_id": "run-k7",
    "job_id": "job-k7",
    "skill_snapshots": {},
    "agent_states": {},
    "handoff_requests": [],
    "routing_history": [],
    "global_replan_count": 0,
    "max_global_replans": 1,
    "max_agent_handoffs": 2,
    "plan": [_skill("hook_analysis")],
    "current_skill": "hook_analysis",
    "evidence_refs": ["KNOWLEDGE:hook-pattern-opening-pain-v1"],
    "knowledge_evidence_refs": ["KNOWLEDGE:hook-pattern-opening-pain-v1"],
    "findings": [
      {
        "skill_key": "hook_analysis",
        "dimension": "HOOK",
        "observation": "Only standard evidence.",
        "suggested_action": "Add video evidence.",
        "confidence": 0.82,
        "evidence_refs": ["KNOWLEDGE:hook-pattern-opening-pain-v1"],
        "knowledge_evidence_refs": ["KNOWLEDGE:hook-pattern-opening-pain-v1"],
      }
    ],
    "evidence_gaps": [],
    "tool_results": [],
    "evaluation_results": [],
    "iteration_count": 2,
    "react_iterations_by_skill": {},
    "tool_observations": [],
    "knowledge_observations": [],
    "retrieval_traces": [],
    "skill_execution_status": {},
    "status": "EVALUATING",
    "step_traces": [],
    "draft_messages": [],
    "draft_observations": [],
    "draft_hypotheses": [],
    "next_action": "evaluate",
    "done": False,
  }

  result = evaluator_node(state, {"configurable": {"harness": FakeGraphHarness(), "harness_ctx": None}})

  assert result["status"] == "FAILED"
  assert "lacks video evidence refs" in result["error"]


def test_structured_handoff_routes_to_value_agent() -> None:
  request = {
    "from_agent": "hook_agent",
    "target_capability": "value_delivery",
    "reason": "cross_skill_boundary",
    "question": "前3-5秒展示的是产品功能，还是已经表达明确用户收益？",
    "evidence_refs": ["OCR:target-1"],
    "confidence": 0.54,
  }

  decision = CentralSupervisor(CapabilityRegistry()).route(request)

  assert decision.target_agent == "value_agent"
  assert decision.source_agent == "hook_agent"
  assert decision.target_capability == "value_delivery"


def test_finding_result_parses_correctly() -> None:
  result = normalize_specialist_result(
    {
      "outcome": "FINDING",
      "skill_key": "hook_analysis",
      "finding_type": "strong_opening_hook",
      "observation": "Clear opening.",
      "evidence_refs": ["OCR:target-1"],
      "confidence": 0.8,
    },
    _skill("hook_analysis"),
  )

  assert result["outcome"] == "FINDING"
  assert result["finding_type"] == "strong_opening_hook"


def test_abstain_result_parses_correctly() -> None:
  result = normalize_specialist_result(
    {
      "outcome": "ABSTAIN",
      "skill_key": "hook_analysis",
      "reason": "No opening text.",
      "evidence_gaps": [{"reason": "missing frame text"}],
      "confidence": 0.2,
    },
    _skill("hook_analysis"),
  )

  assert result["outcome"] == "ABSTAIN"
  assert result["finding_type"] == "evidence_gap"
  assert result["handoff_requests"] == [] if "handoff_requests" in result else True


def test_needs_capability_result_parses_correctly() -> None:
  result = normalize_specialist_result(
    {
      "outcome": "NEEDS_CAPABILITY",
      "skill_key": "hook_analysis",
      "target_capability": "value_delivery",
      "reason": "Need value check.",
      "question": "Does the opening state a concrete user benefit?",
      "evidence_refs": ["OCR:target-1"],
      "confidence": 0.7,
    },
    _skill("hook_analysis"),
  )

  assert result["outcome"] == "NEEDS_CAPABILITY"
  assert result["target_capability"] == "value_delivery"


def test_finding_with_handoff_request_does_not_enter_supervisor() -> None:
  result = normalize_specialist_result(
    {
      "outcome": "FINDING",
      "skill_key": "hook_analysis",
      "finding_type": "strong_opening_hook",
      "observation": "Clear opening.",
      "handoff_requests": [{"target_capability": "value_delivery"}],
      "evidence_refs": ["OCR:target-1"],
      "confidence": 0.8,
    },
    _skill("hook_analysis"),
  )
  gate = evaluate_handoff_gate(
    result=result,
    agent=SPECIALIST_AGENTS["hook_agent"],
    routing_history=[],
    max_agent_handoffs=2,
  )

  assert result["outcome"] == "FINDING"
  assert not gate.accepted
  assert gate.reason == "outcome_not_needs_capability"


def test_handoff_gate_accepts_valid_needs_capability() -> None:
  result = normalize_specialist_result(
    {
      "outcome": "NEEDS_CAPABILITY",
      "target_capability": "value_delivery",
      "reason": "Need value capability.",
      "question": "Does this feature statement create a concrete user benefit?",
      "evidence_refs": ["OCR:target-1"],
      "confidence": 0.7,
    },
    _skill("hook_analysis"),
  )

  gate = evaluate_handoff_gate(
    result=result,
    agent=SPECIALIST_AGENTS["hook_agent"],
    routing_history=[],
    max_agent_handoffs=2,
  )

  assert gate.accepted
  assert gate.request
  assert gate.request["target_capability"] == "value_delivery"


@pytest.mark.parametrize(
  ("patch", "reason"),
  [
    ({"target_capability": "hook_analysis"}, "self_handoff_rejected"),
    ({"target_capability": "unknown_capability"}, "unregistered_target_capability"),
    ({"question": ""}, "invalid_or_generic_question"),
    ({"evidence_refs": []}, "missing_evidence_refs"),
  ],
)
def test_handoff_gate_rejects_invalid_requests(patch: dict[str, Any], reason: str) -> None:
  payload = {
    "outcome": "NEEDS_CAPABILITY",
    "target_capability": "value_delivery",
    "reason": "Need another capability.",
    "question": "Does this statement create a concrete user benefit?",
    "evidence_refs": ["OCR:target-1"],
    "confidence": 0.7,
  } | patch
  result = normalize_specialist_result(payload, _skill("hook_analysis"))

  gate = evaluate_handoff_gate(
    result=result,
    agent=SPECIALIST_AGENTS["hook_agent"],
    routing_history=[],
    max_agent_handoffs=2,
  )

  assert not gate.accepted
  assert gate.reason == reason


def test_handoff_gate_rejects_duplicate_request() -> None:
  result = normalize_specialist_result(
    {
      "outcome": "NEEDS_CAPABILITY",
      "target_capability": "value_delivery",
      "reason": "Need another capability.",
      "question": "Does this statement create a concrete user benefit?",
      "evidence_refs": ["OCR:target-1"],
      "confidence": 0.7,
    },
    _skill("hook_analysis"),
  )

  gate = evaluate_handoff_gate(
    result=result,
    agent=SPECIALIST_AGENTS["hook_agent"],
    routing_history=[
      {
        "sourceAgent": "hook_agent",
        "targetCapability": "value_delivery",
        "question": "Does this statement create a concrete user benefit?",
      }
    ],
    max_agent_handoffs=2,
  )

  assert not gate.accepted
  assert gate.reason == "duplicate_handoff_rejected"


def test_specialist_structured_handoff_output_enters_skill_result(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
      return {
      "outcome": "NEEDS_CAPABILITY",
      "dimension": dimension,
      "finding_type": "opening_value_boundary",
      "observation": "Opening shows product feature before benefit.",
      "difference_text": "Target is ambiguous.",
      "hypothesis_text": "Value delivery needs a second capability check.",
      "suggested_action": "Clarify user benefit.",
      "target_frame_refs": ["00:00:00-00:00:03"],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "target_capability": "value_delivery",
      "reason": "cross_skill_boundary",
      "question": "Is this feature already a clear user benefit?",
      "evidence_refs": ["OCR:target-1"],
      "confidence": 0.82,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-handoff",
    job_context={"jobId": "job-handoff"},
    evidence_pack=_rich_evidence(),
    harness=FakeHarness(lambda tool_name, **args: _knowledge_payload()),
    harness_ctx=None,
  ).run()

  assert result["handoff_requests"][0]["target_capability"] == "value_delivery"
  assert result["finding"]["finding_type"] == "opening_value_boundary"


def test_no_handoff_request_does_not_create_handoff(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    return {
      "dimension": dimension,
      "finding_type": "strong_opening_hook",
      "observation": "Opening is clear.",
      "difference_text": "Target is direct.",
      "hypothesis_text": "No cross-capability gap.",
      "suggested_action": "Keep the direct opening.",
      "target_frame_refs": ["00:00:00-00:00:03"],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "handoff_requests": [],
      "confidence": 0.82,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = DiagnosisReActLoop(
    skill=_skill("hook_analysis"),
    job_id="job-no-handoff",
    job_context={"jobId": "job-no-handoff"},
    evidence_pack=_rich_evidence(),
    harness=FakeHarness(lambda tool_name, **args: _knowledge_payload()),
    harness_ctx=None,
  ).run()

  assert result["handoff_requests"] == []


def test_global_replan_limit() -> None:
  state = {
    "run_id": "run-replan-limit",
    "job_id": "job-replan-limit",
    "skill_snapshots": {},
    "agent_states": {},
    "handoff_requests": [
      {
        "from_agent": "hook_agent",
        "target_capability": "value_delivery",
        "reason": "cross_skill_boundary",
        "question": "q",
        "evidence_refs": ["OCR:target-1"],
        "confidence": 0.5,
      }
    ],
    "routing_history": [],
    "global_replan_count": 0,
    "max_global_replans": 0,
    "max_agent_handoffs": 2,
    "plan": [_skill("hook_analysis")],
    "current_skill": "hook_analysis",
    "evidence_refs": ["OCR:target-1"],
    "knowledge_evidence_refs": [],
    "findings": [
      {
        "skill_key": "hook_analysis",
        "dimension": "HOOK",
        "observation": "Ambiguous feature opening.",
        "suggested_action": "Clarify user benefit.",
        "confidence": 0.82,
        "evidence_refs": ["OCR:target-1"],
      }
    ],
    "evidence_gaps": [],
    "tool_results": [],
    "evaluation_results": [],
    "iteration_count": 0,
    "react_iterations_by_skill": {},
    "tool_observations": [],
    "knowledge_observations": [],
    "retrieval_traces": [],
    "skill_execution_status": {},
    "status": "EVALUATING",
    "step_traces": [],
    "draft_messages": [],
    "draft_observations": [],
    "draft_hypotheses": [],
    "next_action": "evaluate",
    "done": False,
  }

  result = evaluator_node(state, {"configurable": {"harness": FakeGraphHarness(), "harness_ctx": None}})

  assert result["status"] == "SYNTHESIZING"
  assert result["diagnosis_completion_status"] == "COMPLETED_WITH_GAPS"


def test_no_direct_agent_chat() -> None:
  for definition in SPECIALIST_AGENTS.values():
    assert all(not tool.endswith("_agent") for tool in definition.allowed_tools)


def test_three_skill_knowledge_filters_independent() -> None:
  corpus = [
    KnowledgeEvidence("k-hook", "HOOK_PATTERN", "hook_analysis", "", "hook", "前三秒收益", "test"),
    KnowledgeEvidence("k-structure", "STRUCTURE_PATTERN", "structure_rhythm_analysis", "", "structure", "转场节奏", "test"),
    KnowledgeEvidence("k-value", "VALUE_DELIVERY_PATTERN", "value_delivery_analysis", "", "value", "观众收益", "test"),
  ]
  retriever = InMemoryHybridKnowledgeRetriever(corpus)

  hook = retriever.retrieve(KnowledgeQuery("前三秒 收益", "hook_analysis", "DOMAIN_KNOWLEDGE"))
  structure = retriever.retrieve(KnowledgeQuery("转场 节奏", "structure_rhythm_analysis", "DOMAIN_KNOWLEDGE"))
  value = retriever.retrieve(KnowledgeQuery("观众 收益", "value_delivery_analysis", "DOMAIN_KNOWLEDGE"))

  assert hook.items[0].id == "k-hook"
  assert structure.items[0].id == "k-structure"
  assert value.items[0].id == "k-value"


def test_rrf_ranking_merges_channels() -> None:
  fused = reciprocal_rank_fusion([["a", "b"], ["b", "c"]], lambda item: item, final_top_k=3)

  assert fused[0][0] == "b"
  assert [item for item, score in fused] == ["b", "a", "c"]


def test_hybrid_retrieval_and_rerank_fallback() -> None:
  corpus = [
    KnowledgeEvidence("k1", "HOOK_PATTERN", "hook_analysis", "", "weak", "无关内容", "test"),
    KnowledgeEvidence("k2", "HOOK_PATTERN", "hook_analysis", "", "strong", "前三秒 明确 收益 痛点", "test"),
  ]
  result = InMemoryHybridKnowledgeRetriever(corpus).retrieve(
    KnowledgeQuery("前三秒 收益 痛点", "hook_analysis", "DOMAIN_KNOWLEDGE", top_k=1)
  )

  assert result.items[0].id == "k2"
  assert result.trace.bm25_count >= 1
  assert result.trace.rrf_count >= 1
  assert result.trace.rerank_count >= 1


def test_retrieval_benchmark_metrics() -> None:
  row = evaluate_ranked_refs(["KNOWLEDGE:k2"], ["KNOWLEDGE:k1", "KNOWLEDGE:k2"])
  metrics = aggregate_metrics([row])

  assert row["recallAt5"] == 1.0
  assert row["recallAt10"] == 1.0
  assert row["mrr"] == 0.5
  assert metrics["queryCount"] == 1.0


def test_parallel_skills_do_not_mutate_shared_state(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  result = _harness(_tools(_rich_evidence())).run("job-8", {"job_id": "job-8"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED"
  assert result.output["react_iterations_by_skill"] == {
    "hook_analysis": 1,
    "structure_rhythm_analysis": 1,
    "value_delivery_analysis": 1,
  }
  assert set(result.output["skill_execution_status"].values()) == {"COMPLETED"}


def test_cross_agent_replan_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
  counts: dict[str, int] = {}

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    counts[dimension] = counts.get(dimension, 0) + 1
    target = evidence_pack.get("targetEvidence") or {}
    result = {
      "outcome": "FINDING",
      "dimension": dimension,
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target can be sharper.",
      "suggested_action": "Clarify the opening and value.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "counter_evidence": "May already imply value.",
      "confidence": 0.82,
    }
    if dimension == "HOOK" and counts[dimension] == 1:
      result["outcome"] = "NEEDS_CAPABILITY"
      result["target_capability"] = "value_delivery"
      result["reason"] = "cross_skill_boundary"
      result["question"] = "前3-5秒展示的是产品功能，还是已经表达明确用户收益？"
      result["evidence_refs"] = ["OCR:target-1"]
    return result

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = _harness(_tools(_rich_evidence())).run("job-replan", {"job_id": "job-replan"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED"
  assert result.output["global_replan_count"] == 1
  assert result.output["routing_history"][0]["targetAgent"] == "value_agent"
  assert any(item["decision"] == "REPLAN" for item in result.output["evaluation_results"])
  assert counts["VALUE_DELIVERY"] == 2


def test_hook_to_structure_handoff_does_not_require_ambiguous_magic_field(monkeypatch: pytest.MonkeyPatch) -> None:
  counts: dict[str, int] = {}

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    counts[dimension] = counts.get(dimension, 0) + 1
    target = evidence_pack.get("targetEvidence") or {}
    result = {
      "outcome": "FINDING",
      "dimension": dimension,
      "finding_type": "structured_handoff_test",
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target can be sharper.",
      "suggested_action": "Clarify the opening sequence.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "counter_evidence": "May already imply value.",
      "confidence": 0.82,
    }
    if dimension == "HOOK" and counts[dimension] == 1:
      result["outcome"] = "NEEDS_CAPABILITY"
      result["target_capability"] = "structure_rhythm_analysis"
      result["reason"] = "cross_skill_boundary"
      result["question"] = "Does the opening question get structurally answered quickly enough?"
      result["evidence_refs"] = ["OCR:target-1"]
    return result

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = _harness(_tools(_rich_evidence())).run("job-hook-structure-replan", {"job_id": "job-hook-structure-replan"})

  assert result.status == "success"
  assert result.output["routing_history"][0]["targetCapability"] == "structure_rhythm_analysis"
  assert result.output["routing_history"][0]["targetAgent"] == "structure_agent"
  assert any(item["decision"] == "REPLAN" for item in result.output["evaluation_results"])
  assert counts["STRUCTURE_RHYTHM"] == 2


def test_abstain_is_not_missing_skill_failure(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    target = evidence_pack.get("targetEvidence") or {}
    if dimension == "VALUE_DELIVERY":
      return {
        "outcome": "ABSTAIN",
        "dimension": dimension,
        "reason": "Value evidence is insufficient.",
        "evidence_gaps": [{"reason": "missing value evidence"}],
        "evidence_refs": ["OCR:target-1"],
        "confidence": 0.2,
      }
    return {
      "outcome": "FINDING",
      "dimension": dimension,
      "finding_type": "strong_opening_hook" if dimension == "HOOK" else "structure_opening_pattern_difference",
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target can be sharper.",
      "suggested_action": "Keep improving.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "confidence": 0.82,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = _harness(_tools(_rich_evidence())).run("job-abstain", {"job_id": "job-abstain"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED_WITH_GAPS"
  assert "MISSING_SPECIALIST_RESULT" not in result.output.get("error", "")
  assert any(item.get("outcome") == "ABSTAIN" for item in result.output["findings"])


def test_all_findings_complete_without_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  result = _harness(_tools(_rich_evidence())).run("job-complete", {"job_id": "job-complete"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED"


def test_target_specialist_receives_targeted_reinvestigation_context(monkeypatch: pytest.MonkeyPatch) -> None:
  contexts: list[dict[str, Any]] = []
  counts: dict[str, int] = {}

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    contexts.append(dict(job_context))
    counts[dimension] = counts.get(dimension, 0) + 1
    target = evidence_pack.get("targetEvidence") or {}
    if dimension == "HOOK" and counts[dimension] == 1:
      return {
        "outcome": "NEEDS_CAPABILITY",
        "dimension": dimension,
        "target_capability": "value_delivery",
        "reason": "Need value capability.",
        "question": "Does this feature statement create a concrete user benefit?",
        "target_frame_refs": target.get("keyframes") or [],
        "evidence_refs": ["OCR:target-1"],
        "confidence": 0.7,
      }
    return {
      "outcome": "FINDING",
      "dimension": dimension,
      "finding_type": "proof_before_claim" if dimension == "VALUE_DELIVERY" else "structure_opening_pattern_difference",
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target can be sharper.",
      "suggested_action": "Clarify.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "confidence": 0.82,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = _harness(_tools(_rich_evidence())).run("job-targeted", {"job_id": "job-targeted"})

  targeted = [ctx for ctx in contexts if ctx.get("execution_mode") == "TARGETED_REINVESTIGATION"]
  assert result.status == "success"
  assert result.output["routing_history"][0]["targetAgent"] == "value_agent"
  assert targeted
  assert targeted[0]["handoff_context"]["source_finding"]["skill_key"] == "hook_analysis"
  assert targeted[0]["handoff_context"]["question"] == "Does this feature statement create a concrete user benefit?"


def test_targeted_reinvestigation_cannot_handoff_back_to_source(monkeypatch: pytest.MonkeyPatch) -> None:
  counts: dict[str, int] = {}

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    counts[dimension] = counts.get(dimension, 0) + 1
    target = evidence_pack.get("targetEvidence") or {}
    if dimension == "HOOK" and counts[dimension] == 1:
      return {
        "outcome": "NEEDS_CAPABILITY",
        "dimension": dimension,
        "target_capability": "value_delivery",
        "reason": "Need value capability.",
        "question": "Does this feature statement create a concrete user benefit?",
        "target_frame_refs": target.get("keyframes") or [],
        "evidence_refs": ["OCR:target-1"],
        "confidence": 0.7,
      }
    if dimension == "VALUE_DELIVERY" and job_context.get("execution_mode") == "TARGETED_REINVESTIGATION":
      return {
        "outcome": "NEEDS_CAPABILITY",
        "dimension": dimension,
        "target_capability": "hook_analysis",
        "reason": "Would need to ask hook again.",
        "question": "Should hook inspect the opening again?",
        "evidence_refs": ["OCR:target-1"],
        "confidence": 0.7,
      }
    return {
      "outcome": "FINDING",
      "dimension": dimension,
      "finding_type": "structure_opening_pattern_difference",
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target can be sharper.",
      "suggested_action": "Clarify.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "confidence": 0.82,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = _harness(_tools(_rich_evidence())).run("job-no-ping-pong", {"job_id": "job-no-ping-pong"})

  assert result.status == "success"
  assert result.output["global_replan_count"] == 1
  assert result.output["status"] == "COMPLETED_WITH_GAPS"
  assert counts["VALUE_DELIVERY"] == 2


def test_evaluator_retry_skill_reruns_only_affected_skill(monkeypatch: pytest.MonkeyPatch) -> None:
  counts: dict[str, int] = {}

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    counts[dimension] = counts.get(dimension, 0) + 1
    confidence = 0.4 if dimension == "HOOK" and counts[dimension] == 1 else 0.8
    return {
      "dimension": dimension,
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target opening can be sharper.",
      "suggested_action": "Move value text earlier.",
      "target_frame_refs": ["00:00:00-00:00:03"],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "counter_evidence": "Narrative style may be slower.",
      "confidence": confidence,
    }

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)

  result = _harness(_tools(_rich_evidence())).run("job-9", {"job_id": "job-9"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED"
  assert counts["HOOK"] == 2
  assert counts["STRUCTURE_RHYTHM"] == 1
  assert counts["VALUE_DELIVERY"] == 1
  assert any(item["decision"] == "RETRY_AGENT" for item in result.output["evaluation_results"])


def test_evaluator_retry_reuses_prior_knowledge_observations_under_turn_budget(monkeypatch: pytest.MonkeyPatch) -> None:
  counts: dict[str, int] = {}
  knowledge_calls: list[dict[str, Any]] = []
  saved: list[dict[str, Any]] = []

  def fake_diagnose(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    counts[dimension] = counts.get(dimension, 0) + 1
    target = evidence_pack.get("targetEvidence") or {}
    return {
      "outcome": "FINDING",
      "dimension": dimension,
      "finding_type": "retry_knowledge_reuse",
      "observation": f"{dimension} observation",
      "difference_text": "Target differs from reference.",
      "hypothesis_text": "Target can be sharper.",
      "suggested_action": "Clarify the opening and value.",
      "target_frame_refs": target.get("keyframes") or [],
      "reference_frame_refs": ["ref:00:00:00-00:00:03"],
      "confidence": 0.4 if counts[dimension] == 1 else 0.82,
    }

  def retrieve_knowledge(**kwargs: Any) -> dict[str, Any]:
    knowledge_calls.append(dict(kwargs))
    payload = _knowledge_payload(f"KNOWLEDGE:{kwargs['skill_code']}-rule-v1")
    payload["trace"]["skill_code"] = kwargs["skill_code"]
    payload["items"][0]["skillCode"] = kwargs["skill_code"]
    return payload

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake_diagnose)
  tools = {
    "get_job_context": lambda job_id: {"jobId": job_id, "targetVideoId": "target-1", "needKnowledge": True},
    "get_video_evidence": lambda job_id: _rich_evidence(),
    "retrieve_knowledge": retrieve_knowledge,
    "save_diagnosis_hypothesis": lambda job_id, hypothesis: saved.append(hypothesis)
    or {"findingId": f"finding-{len(saved)}"},
    "save_agent_draft_result": lambda job_id, draft_observations: {"ok": True},
    "report_agent_progress": lambda **kwargs: {"ok": True},
  }
  harness = HarnessRunner(
    compiled_graph=build_diagnosis_graph(),
    tools=tools,
    limits=HarnessLimits(max_turns=20, max_tokens=32000, max_graph_steps=120, timeout_seconds=30),
  )

  result = harness.run("job-retry-knowledge-budget", {"job_id": "job-retry-knowledge-budget"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED"
  assert result.turns < 20
  # 三个 Specialist 并行执行，检索调用的先后顺序取决于线程调度，只比较集合
  assert sorted(call["skill_code"] for call in knowledge_calls) == [
    "hook_analysis",
    "structure_rhythm_analysis",
    "value_delivery_analysis",
  ]
  assert counts == {
    "HOOK": 2,
    "STRUCTURE_RHYTHM": 2,
    "VALUE_DELIVERY": 2,
  }
  assert len(result.output["knowledge_observations"]) == 3
  assert any(item["decision"] == "RETRY_AGENT" for item in result.output["evaluation_results"])


def test_baseline_regression(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  harness = HarnessRunner(
    compiled_graph=build_parallel_skills_graph(),
    tools=_tools(_rich_evidence()),
    limits=HarnessLimits(max_turns=80, max_tokens=32000, max_graph_steps=120, timeout_seconds=30),
  )

  result = harness.run("job-baseline", {"job_id": "job-baseline"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED"
  assert result.output["global_replan_count"] == 0
  assert not any(step.get("step_type") == "SUPERVISOR_ROUTE" for step in result.output["step_traces"])
  assert set(result.output["react_iterations_by_skill"]) == {
    "hook_analysis",
    "structure_rhythm_analysis",
    "value_delivery_analysis",
  }


def test_final_java_callback_payload_remains_compatible(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)

  result = _harness(_tools(_rich_evidence())).run("job-10", {"job_id": "job-10"})

  observations = result.output["draft_observations"]
  assert isinstance(observations, list)
  assert observations[-1] == "agent_run_status:COMPLETED"
  assert all(isinstance(item, str) for item in observations)
