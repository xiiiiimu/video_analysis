"""编排闭环测试：交接回调、评估反馈重试、证据引用校验、冲突检测、部分完成、合成与保存、服务层。"""

from __future__ import annotations

import dataclasses
import threading
import time
from typing import Any

import pytest
from test_agent_workflow import FakeGraphHarness, _harness, _rich_evidence, _skill, _tools

from agent_service.graph.builder import build_diagnosis_graph
from agent_service.graph.diagnosis_skill import known_evidence_refs, run_diagnosis_skill
from agent_service.graph.nodes.evaluator import _detect_conflicts, evaluator_node
from agent_service.graph.nodes.supervisor import supervisor_node
from agent_service.graph.synthesis import build_rule_synthesis, merge_llm_synthesis
from agent_service.harness import HarnessLimits
from agent_service.services.harness_setup import create_diagnosis_harness
from agent_service.services.job_queue import JobDispatcher, QueueFullError
from agent_service.tools.adapters.errors import JavaBackendError

LIMITS = HarnessLimits(max_turns=80, max_tokens=32000, max_graph_steps=120, timeout_seconds=30)
CONFIG = {"configurable": {"harness": FakeGraphHarness(), "harness_ctx": None}}


def _finding(dimension: str, evidence: dict[str, Any], **overrides: Any) -> dict[str, Any]:
  target = evidence.get("targetEvidence") or {}
  base = {
    "outcome": "FINDING",
    "dimension": dimension,
    "finding_type": "unknown",
    "observation": f"{dimension} observation",
    "difference_text": "Target differs from reference.",
    "hypothesis_text": "Target can be sharper.",
    "suggested_action": "Clarify.",
    "target_frame_refs": target.get("keyframes") or [],
    "reference_frame_refs": ["ref:00:00:00-00:00:03"],
    "confidence": 0.82,
  }
  base.update(overrides)
  return base


def _base_state(**overrides: Any) -> dict[str, Any]:
  state: dict[str, Any] = {
    "run_id": "run-1",
    "job_id": "job-1",
    "skill_snapshots": {},
    "agent_states": {},
    "handoff_requests": [],
    "routing_history": [],
    "handoff_answers": [],
    "dropped_handoffs": [],
    "global_replan_count": 0,
    "max_global_replans": 1,
    "max_agent_handoffs": 2,
    "plan": [_skill("hook_analysis"), _skill("value_delivery_analysis")],
    "evidence_refs": [],
    "knowledge_evidence_refs": [],
    "findings": [],
    "evidence_gaps": [],
    "tool_results": [],
    "evaluation_results": [],
    "iteration_count": 0,
    "react_iterations_by_skill": {},
    "tool_observations": [],
    "knowledge_observations": [],
    "retrieval_traces": [],
    "skill_execution_status": {"hook_analysis": "COMPLETED", "value_delivery_analysis": "COMPLETED"},
    "status": "EVALUATING",
    "step_traces": [],
    "draft_messages": [],
    "draft_observations": [],
    "draft_hypotheses": [],
    "next_action": "evaluate",
    "done": False,
  }
  state.update(overrides)
  return state


# ---------------------------------------------------------------------- 交接回调闭环


def test_handoff_answer_returns_to_source_and_keeps_target_finding(monkeypatch: pytest.MonkeyPatch) -> None:
  calls: list[tuple[str, str | None]] = []
  saved: list[dict[str, Any]] = []

  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    mode = job_context.get("execution_mode")
    calls.append((dimension, mode))
    if dimension == "HOOK" and mode is None:
      return _finding(
        dimension,
        evidence_pack,
        outcome="NEEDS_CAPABILITY",
        target_capability="value_delivery",
        reason="cross_skill_boundary",
        question="前3-5秒展示的是产品功能，还是已经表达明确用户收益？",
        evidence_refs=["OCR:target-1"],
      )
    if dimension == "VALUE_DELIVERY" and mode == "TARGETED_REINVESTIGATION":
      return _finding(dimension, evidence_pack, observation="开头只展示功能，没有说明用户收益", evidence_refs=["OCR:target-1"])
    if dimension == "HOOK" and mode == "HANDOFF_INTEGRATION":
      assert job_context["handoff_answer"]["status"] == "ANSWERED"
      assert "没有说明用户收益" in job_context["handoff_answer"]["answer"]["observation"]
      return _finding(dimension, evidence_pack, observation="开场钩子缺少收益承诺")
    return _finding(dimension, evidence_pack, observation=f"{dimension} full diagnosis")

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = _harness(_tools(_rich_evidence(), saved)).run("job-handoff", {"job_id": "job-handoff"})

  assert result.status == "success"
  assert ("HOOK", "HANDOFF_INTEGRATION") in calls, "提问方必须拿着答复被回调"
  findings = {item["skill_key"]: item for item in result.output["findings"]}
  assert findings["hook_analysis"]["outcome"] == "FINDING"
  assert findings["hook_analysis"]["observation"] == "开场钩子缺少收益承诺"
  assert findings["hook_analysis"]["handoff_answer"]["status"] == "ANSWERED"
  assert "OCR:target-1" in findings["hook_analysis"]["evidence_refs"]
  # 被询问方原本的完整诊断没有被定向答复覆盖
  assert findings["value_delivery_analysis"]["observation"] == "VALUE_DELIVERY full diagnosis"
  assert result.output["handoff_answers"][0]["status"] == "ANSWERED"
  assert all(item["outcome"] != "NEEDS_CAPABILITY" for item in saved)
  assert result.output["status"] == "COMPLETED"


def test_unresolved_handoff_becomes_abstain_before_synthesis() -> None:
  evidence = _rich_evidence()
  state = _base_state(
    max_global_replans=0,
    handoff_requests=[
      {
        "from_agent": "hook_agent",
        "target_capability": "value_delivery",
        "reason": "x",
        "question": "前三秒是功能还是收益？",
        "evidence_refs": ["OCR:target-1"],
      }
    ],
    findings=[
      {**_finding("HOOK", evidence), "skill_key": "hook_analysis", "outcome": "NEEDS_CAPABILITY", "question": "前三秒是功能还是收益？", "evidence_refs": ["OCR:target-1"]},
      {**_finding("VALUE_DELIVERY", evidence), "skill_key": "value_delivery_analysis", "evidence_refs": ["OCR:target-1"]},
    ],
  )
  result = evaluator_node(state, CONFIG)
  assert result["next_action"] == "synthesize"
  assert result["diagnosis_completion_status"] == "COMPLETED_WITH_GAPS"
  hook = next(item for item in result["findings"] if item["skill_key"] == "hook_analysis")
  assert hook["outcome"] == "ABSTAIN"
  assert hook["handoff_rejected"]["reason"] == "handoff_not_resolved"
  assert result["dropped_handoffs"][0]["drop_reason"] == "global_replan_limit_exceeded"


def test_supervisor_routes_one_request_and_keeps_the_rest() -> None:
  requests = [
    {"from_agent": "hook_agent", "target_capability": "value_delivery", "question": "问题一：收益是否明确？", "evidence_refs": ["OCR:target-1"]},
    {"from_agent": "value_agent", "target_capability": "hook_analysis", "question": "问题二：开场是否抓人？", "evidence_refs": ["OCR:target-1"]},
  ]
  update = supervisor_node(_base_state(handoff_requests=requests), CONFIG)
  assert update["active_handoff"]["request_id"] == "handoff-1"
  assert update["handoff_requests"] == requests[1:]

  exhausted = supervisor_node(
    _base_state(handoff_requests=requests, routing_history=[{}, {}], max_agent_handoffs=2), CONFIG
  )
  assert exhausted["next_action"] == "evaluate"
  assert len(exhausted["dropped_handoffs"]) == 2
  assert exhausted.get("status") != "FAILED", "交接预算用完不再让整个 run 失败"


# ---------------------------------------------------------------------- 评估：反馈重试 / 引用校验 / 冲突


def test_retry_carries_evaluator_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
  seen_feedback: dict[str, list[list[str]]] = {}

  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    feedback = list(job_context.get("evaluator_feedback") or [])
    seen_feedback.setdefault(dimension, []).append(feedback)
    confidence = 0.4 if dimension == "HOOK" and not feedback else 0.85
    return _finding(dimension, evidence_pack, confidence=confidence)

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = _harness(_tools(_rich_evidence())).run("job-feedback", {"job_id": "job-feedback"})

  assert result.status == "success"
  assert len(seen_feedback["HOOK"]) == 2
  assert any("置信度" in item for item in seen_feedback["HOOK"][1])
  assert len(seen_feedback["VALUE_DELIVERY"]) == 1, "只重跑受影响的维度"
  assert any(step.get("step_type") == "RETRY_WITH_FEEDBACK" for step in result.output["step_traces"])


def test_invented_evidence_refs_are_removed_and_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
  evidence = _rich_evidence()

  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    return _finding(dimension, evidence_pack, target_frame_refs=["00:00:00-00:00:03", "99:99:99-made-up"], evidence_refs=["OCR:target-1", "KNOWLEDGE:not-retrieved"])

  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  finding = run_diagnosis_skill(_skill("hook_analysis"), {"jobId": "job-1"}, evidence)
  assert set(finding["invalid_evidence_refs"]) == {"99:99:99-made-up", "KNOWLEDGE:not-retrieved"}
  assert "99:99:99-made-up" not in finding["evidence_refs"]
  assert "OCR:target-1" in finding["evidence_refs"]
  assert {"OCR:target-1", "OCR:ref-1", "00:00:00-00:00:03", "METADATA:target-1"} <= known_evidence_refs(evidence)

  state = _base_state(
    plan=[_skill("hook_analysis")],
    skill_execution_status={"hook_analysis": "COMPLETED"},
    findings=[{**finding, "skill_key": "hook_analysis"}],
  )
  result = evaluator_node(state, CONFIG)
  assert result["next_action"] == "diagnose"
  assert any("不存在" in item for item in result["retry_feedback"]["hook_analysis"])


def test_chinese_conflicting_suggestions_are_detected() -> None:
  findings = [
    {"skill_key": "hook_analysis", "outcome": "FINDING", "suggested_action": "把产品卖点提前到第 1 秒"},
    {"skill_key": "structure_rhythm_analysis", "outcome": "FINDING", "suggested_action": "卖点延后到第二段再展开"},
    {"skill_key": "value_delivery_analysis", "outcome": "FINDING", "suggested_action": "补充使用场景"},
  ]
  conflicts = _detect_conflicts(findings)
  assert conflicts == [("hook_analysis", "structure_rhythm_analysis", "提前/延后")]


# ---------------------------------------------------------------------- 部分完成


def test_one_specialist_crash_does_not_fail_the_whole_run(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    if dimension == "VALUE_DELIVERY":
      raise RuntimeError("model returned garbage")
    return _finding(dimension, evidence_pack)

  saved: list[dict[str, Any]] = []
  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = _harness(_tools(_rich_evidence(), saved)).run("job-partial", {"job_id": "job-partial"})

  assert result.status == "success"
  assert result.output["status"] == "COMPLETED_WITH_GAPS"
  findings = {item["skill_key"]: item for item in result.output["findings"]}
  assert findings["hook_analysis"]["outcome"] == "FINDING"
  assert findings["value_delivery_analysis"]["outcome"] == "ABSTAIN"
  assert findings["value_delivery_analysis"]["system_failure"] is True
  assert result.output["synthesis"]["evidenceGaps"][0]["systemFailure"] is True


# ---------------------------------------------------------------------- 合成与保存


def test_synthesis_ranks_findings_and_batch_save_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    confidence = {"HOOK": 0.7, "STRUCTURE_RHYTHM": 0.95, "VALUE_DELIVERY": 0.9}[dimension]
    return _finding(dimension, evidence_pack, confidence=confidence, suggested_action=f"{dimension} action")

  batches: list[dict[str, Any]] = []
  tools = _tools(_rich_evidence())
  tools["save_diagnosis_result"] = lambda **kwargs: batches.append(kwargs) or {"findingIds": ["f1", "f2", "f3"]}
  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = _harness(tools).run("job-synth", {"job_id": "job-synth", "agent_run_id": "run-42"})

  assert result.status == "success"
  assert len(batches) == 1
  assert batches[0]["idempotency_key"] == "run-42:v1"
  synthesis = result.output["synthesis"]
  assert [row["dimension"] for row in synthesis["priorities"]] == ["VALUE_DELIVERY", "STRUCTURE_RHYTHM", "HOOK"]
  assert batches[0]["synthesis"]["summary"] == synthesis["summary"]
  assert any(item.startswith("synthesis:") for item in result.output["draft_observations"])
  assert result.output["draft_observations"][-1] == "agent_run_status:COMPLETED"


@pytest.mark.parametrize("status", [404, 500])
def test_batch_save_falls_back_to_per_finding_when_endpoint_missing(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    return _finding(dimension, evidence_pack)

  saved: list[dict[str, Any]] = []
  tools = _tools(_rich_evidence(), saved)

  def missing(**kwargs: Any) -> Any:
    raise JavaBackendError("not found", status_code=status)

  tools["save_diagnosis_result"] = missing
  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = _harness(tools).run("job-fallback", {"job_id": "job-fallback", "agent_run_id": "run-7"})

  assert result.status == "success"
  assert len(saved) == 3
  assert {item["idempotency_key"] for item in saved} == {
    "run-7:v1:hook_analysis",
    "run-7:v1:structure_rhythm_analysis",
    "run-7:v1:value_delivery_analysis",
  }


def test_llm_synthesis_cannot_invent_dimensions() -> None:
  base = build_rule_synthesis(
    [
      {"skill_key": "hook_analysis", "dimension": "HOOK", "outcome": "FINDING", "confidence": 0.9, "suggested_action": "a"},
      {"skill_key": "value_delivery_analysis", "dimension": "VALUE_DELIVERY", "outcome": "FINDING", "confidence": 0.8, "suggested_action": "b"},
    ],
    completion_status="COMPLETED",
  )
  merged = merge_llm_synthesis(
    base,
    {
      "summary": "价值表达是最大问题",
      "priorities": [
        {"skillKey": "value_delivery_analysis", "rationale": "收益不清"},
        {"skillKey": "made_up_skill", "rationale": "x"},
      ],
      "mergedActions": ["先讲收益"],
    },
  )
  assert merged["source"] == "llm"
  assert [row["skillKey"] for row in merged["priorities"]] == ["value_delivery_analysis", "hook_analysis"]
  assert [row["rank"] for row in merged["priorities"]] == [1, 2]
  assert merge_llm_synthesis(base, {"summary": ""}) is base


# ---------------------------------------------------------------------- 工具错误分类


def test_auth_failure_from_java_stops_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
  def fake(dimension: str, job_context: dict[str, Any], evidence_pack: dict[str, Any]) -> dict[str, Any]:
    return _finding(dimension, evidence_pack)

  tools = _tools(_rich_evidence())

  def unauthorized(job_id: str) -> Any:
    raise JavaBackendError("unauthorized", status_code=401)

  tools["get_video_evidence"] = unauthorized
  monkeypatch.setattr("agent_service.graph.diagnosis_skill.diagnose_dimension", fake)
  result = create_diagnosis_harness(tools, graph=build_diagnosis_graph(), limits=LIMITS).run("job-401", {"job_id": "job-401"})
  assert result.stop_reason == "error"
  assert result.status == "failed"
  assert "Fatal tool error" in (result.error or "")


# ---------------------------------------------------------------------- LLM 配置


def test_missing_llm_key_fails_instead_of_returning_mock(monkeypatch: pytest.MonkeyPatch) -> None:
  from agent_service.llm import diagnosis_llm

  real = diagnosis_llm.get_settings()
  monkeypatch.setattr(diagnosis_llm, "get_settings", lambda: dataclasses.replace(real, chat_api_key="", llm_mock=False))
  with pytest.raises(diagnosis_llm.LLMNotConfiguredError):
    diagnosis_llm.diagnose_dimension("HOOK", {}, _rich_evidence())

  monkeypatch.setattr(diagnosis_llm, "get_settings", lambda: dataclasses.replace(real, chat_api_key="", llm_mock=True))
  assert diagnosis_llm.diagnose_dimension("HOOK", {}, _rich_evidence())["finding_type"] == "hook_no_value_promise"


def test_payload_marks_truncated_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
  from agent_service.llm import diagnosis_llm

  real = diagnosis_llm.get_settings()
  monkeypatch.setattr(diagnosis_llm, "get_settings", lambda: dataclasses.replace(real, evidence_text_limit=10))
  evidence = _rich_evidence()
  evidence["targetEvidence"]["transcriptText"] = "很长的转写" * 20
  evidence["targetEvidence"]["keyframes"] = [f"00:00:{i:02d}" for i in range(12)]
  payload = diagnosis_llm._build_user_payload("HOOK", {}, evidence)
  assert payload["truncation"]["target.transcript"]["originalChars"] == 100
  assert payload["truncation"]["target.keyframes"] == {"originalCount": 12, "keptCount": 8}
  assert payload["references"][0]["ocrJson"], "参考视频的 OCR 现在也会提供给模型"


def test_skills_dir_env_is_respected(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
  from agent_service import config
  from agent_service.skills.loader import default_skills_dir

  real = config.get_settings()
  monkeypatch.setattr(config, "get_settings", lambda: dataclasses.replace(real, skills_dir=str(tmp_path)))
  assert default_skills_dir() == tmp_path


# ---------------------------------------------------------------------- 服务层：任务调度与鉴权


def test_dispatcher_dedupes_and_bounds_concurrency() -> None:
  running = {"now": 0, "max": 0}
  lock = threading.Lock()
  release = threading.Event()

  def runner(job_id: str, run_id: str | None) -> None:
    with lock:
      running["now"] += 1
      running["max"] = max(running["max"], running["now"])
    release.wait(2)
    with lock:
      running["now"] -= 1

  dispatcher = JobDispatcher(runner, max_workers=2, max_pending=4)
  first = dispatcher.submit("job-a", "run-a")
  duplicate = dispatcher.submit("job-a", "run-b")
  assert not first.duplicate and duplicate.duplicate and duplicate.agent_run_id == "run-a"
  for job in ("job-b", "job-c", "job-d"):
    dispatcher.submit(job)
  with pytest.raises(QueueFullError):
    dispatcher.submit("job-e")
  time.sleep(0.2)
  release.set()
  dispatcher.shutdown(wait=True)
  assert running["max"] == 2
  assert dispatcher.in_flight == 0


def test_submit_endpoint_requires_api_key_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
  from fastapi import FastAPI
  from fastapi.testclient import TestClient

  from agent_service.api import routes

  submitted: list[str] = []

  class FakeDispatcher:
    def submit(self, job_id: str, run_id: str | None = None) -> Any:
      submitted.append(job_id)
      return type("R", (), {"agent_run_id": run_id, "duplicate": False})()

  real = routes.get_settings()
  monkeypatch.setattr(routes, "get_settings", lambda: dataclasses.replace(real, agent_service_api_key="secret"))
  monkeypatch.setattr(routes, "get_dispatcher", lambda: FakeDispatcher())
  app = FastAPI()
  app.include_router(routes.router)
  client = TestClient(app)

  assert client.post("/api/v1/agent/jobs/submit", json={"job_id": "j1"}).status_code == 401
  assert client.post("/api/v1/agent/jobs/submit", json={"job_id": "j1"}, headers={"X-Internal-Api-Key": "wrong"}).status_code == 401
  ok = client.post("/api/v1/agent/jobs/submit", json={"job_id": "j1"}, headers={"X-Internal-Api-Key": "secret"})
  assert ok.status_code == 202 and submitted == ["j1"]
  assert client.get("/api/v1/agent/health").status_code == 200
