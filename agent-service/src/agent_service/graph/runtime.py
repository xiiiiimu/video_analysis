from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agent_service.graph.state import AgentGraphState, StepTrace


@dataclass
class AgentStep:
  node: str
  skill: str = ""
  step_type: str = ""
  status: str = "PENDING"
  iteration: int = 0
  tool_calls: list[dict[str, Any]] = field(default_factory=list)
  error: str = ""
  input_summary: str = ""
  output_summary: str = ""
  requested_evidence: str = ""
  tool_name: str = ""
  start: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
  end: str = ""


@dataclass
class AgentRun:
  run_id: str
  job_id: str
  status: str = "RUNNING"
  steps: list[AgentStep] = field(default_factory=list)


def utc_now() -> str:
  return datetime.now(UTC).isoformat()


def report_stage(
  state: AgentGraphState,
  config: dict[str, Any],
  stage: str,
  percent: int,
  short_summary: str = "",
) -> None:
  """
  Best-effort Java Redis progress update. MySQL remains the source of truth.

  进度上报是流程副作用，不是模型选择的工具：走 ``call_infra``，不计入轮次/步数预算，
  只留一条 infra_call 审计。（改造前走 call_tool，每次上报都会消耗一次轮次和图步数。）
  """
  harness = config["configurable"]["harness"]
  harness_ctx = config["configurable"]["harness_ctx"]
  call_infra = getattr(harness, "call_infra", None)
  if call_infra is None:
    return
  try:
    call_infra(
      harness_ctx,
      "report_agent_progress",
      job_id=state["job_id"],
      agent_run_id=state["run_id"],
      stage=stage,
      percent=percent,
      status="RUNNING" if stage != "COMPLETED" else "COMPLETED",
      short_summary=short_summary,
    )
  except Exception:  # noqa: BLE001 - progress is best-effort
    # Progress is cache-only; never fail the AgentRun because Redis/Java progress is unavailable.
    return


def build_lightweight_trace(state: AgentGraphState) -> list[dict[str, Any]]:
  run_id = state.get("run_id", "")
  rows: list[dict[str, Any]] = []
  for step in state.get("step_traces") or []:
    rows.append(
      {
        "runId": run_id,
        "agentId": step.get("agent_id") or "",
        "stepType": step.get("step_type") or step.get("node") or "",
        "skillCode": step.get("skill") or step.get("skill_code") or "",
        "toolName": step.get("tool_name") or _first_tool_name(step),
        "evidenceRefs": list(step.get("selected_evidence_refs") or []),
        "latencyMs": _latency_ms(step),
        "status": step.get("status") or "",
        "shortSummary": step.get("output_summary") or step.get("input_summary") or "",
      }
    )
  return rows


@contextmanager
def trace_step(
  state: AgentGraphState,
  node: str,
  *,
  skill: str = "",
  step_type: str = "",
  iteration: int | None = None,
  input_summary: str = "",
  requested_evidence: str = "",
  tool_name: str = "",
) -> Iterator[StepTrace]:
  step: StepTrace = {
    "node": node,
    "skill": skill,
    "step_type": step_type,
    "start": utc_now(),
    "status": "RUNNING",
    "iteration": state.get("iteration_count", 0) if iteration is None else iteration,
    "tool_calls": [],
    "input_summary": input_summary,
    "requested_evidence": requested_evidence,
    "tool_name": tool_name,
  }
  traces = list(state.get("step_traces") or [])
  traces.append(step)
  state["step_traces"] = traces
  try:
    yield step
    step["status"] = "SUCCESS"
  except Exception as exc:
    step["status"] = "FAILED"
    step["error"] = str(exc)
    raise
  finally:
    step["end"] = utc_now()


def _first_tool_name(step: StepTrace) -> str:
  calls = step.get("tool_calls") or []
  if not calls:
    return ""
  return str(calls[0].get("tool_name") or "")


def _latency_ms(step: StepTrace) -> int:
  if step.get("latency"):
    return int(step.get("latency") or 0)
  try:
    start = datetime.fromisoformat(str(step.get("start")))
    end = datetime.fromisoformat(str(step.get("end")))
  except ValueError:
    return 0
  return max(0, int((end - start).total_seconds() * 1000))


def summarize_payload(payload: Any, limit: int = 240) -> str:
  text = str(payload)
  return text if len(text) <= limit else text[:limit] + "..."
