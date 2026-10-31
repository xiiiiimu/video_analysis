"""Harness 机制测试：事件 / hook / 插件 / 限额 / 取消 / interventions / 模型重试 / HTTP 重试熔断。"""

from __future__ import annotations

import time
from typing import Any

import httpx
import pytest
from langgraph.graph import END, StateGraph
from test_agent_workflow import _patch_diagnosis, _rich_evidence, _tools
from typing_extensions import TypedDict

from agent_service.graph.builder import build_diagnosis_graph
from agent_service.graph.policies import JobIdPinning, SpecialistToolPolicy
from agent_service.harness import (
  AuditPlugin,
  Deny,
  Guide,
  HarnessContext,
  HarnessLimits,
  HarnessRunner,
  HookOrder,
  HookRegistry,
  InterventionHandler,
  InterventionPlugin,
  LimitsPlugin,
  ModelRetryPlugin,
  OutputFormatGuard,
  Plugin,
  Proceed,
  ToolCallCancelled,
  Transform,
  build_harness,
  call_model,
  harness_node,
  harness_scope,
  hook,
)
from agent_service.harness.events import (
  AfterToolCallEvent,
  BeforeModelCallEvent,
  BeforeToolCallEvent,
)
from agent_service.services.harness_setup import create_diagnosis_harness
from agent_service.tools.adapters.http_client import (
  CircuitBreaker,
  JavaBackendError,
  JavaBackendHttpClient,
)

LIMITS = HarnessLimits(max_turns=80, max_tokens=32000, max_graph_steps=120, timeout_seconds=30)


# ---------------------------------------------------------------------- 小工具


class _State(TypedDict, total=False):
  count: int
  log: list[str]


def _loop_graph(steps: int, tool_name: str = "ping", sleep: float = 0.0) -> Any:
  """一个最小图：每个节点调一次工具，跑 steps 次。"""

  def work(state: _State, config: Any) -> dict[str, Any]:
    harness = config["configurable"]["harness"]
    ctx = config["configurable"]["harness_ctx"]
    if sleep:
      time.sleep(sleep)
    harness.call_tool(ctx, tool_name, value=state.get("count", 0))
    return {"count": state.get("count", 0) + 1, "log": [*state.get("log", []), "work"]}

  graph = StateGraph(_State)
  graph.add_node("work", harness_node("work", work))
  graph.set_entry_point("work")
  graph.add_conditional_edges("work", lambda s: "end" if s["count"] >= steps else "work", {"work": "work", "end": END})
  return graph.compile()


class _Resp:
  def __init__(self, content: str, input_tokens: int = 10, output_tokens: int = 5) -> None:
    self.content = content
    self.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}


def _ctx() -> HarnessContext:
  return HarnessContext(task_id="t-1", trace_id="trace-1", job_id="job-1")


# ---------------------------------------------------------------------- 事件与 hook


def test_event_fields_are_read_only_except_writable() -> None:
  event = BeforeToolCallEvent(ctx=_ctx(), tool_name="x", tool_args={})
  event.cancel_tool = "no"
  with pytest.raises(AttributeError):
    event.tool_name = "y"


def test_hook_order_and_after_events_reverse() -> None:
  calls: list[str] = []
  registry = HookRegistry()
  registry.add_callback(BeforeToolCallEvent, lambda e: calls.append("default"))
  registry.add_callback(BeforeToolCallEvent, lambda e: calls.append("first"), order=HookOrder.FIRST)
  registry.add_callback(AfterToolCallEvent, lambda e: calls.append("after-first"), order=HookOrder.FIRST)
  registry.add_callback(AfterToolCallEvent, lambda e: calls.append("after-default"))
  ctx = _ctx()
  registry.emit(BeforeToolCallEvent(ctx=ctx, tool_name="x", tool_args={}))
  registry.emit(AfterToolCallEvent(ctx=ctx, tool_name="x", tool_args={}))
  assert calls == ["first", "default", "after-default", "after-first"]


def test_plugin_discovers_union_hooks_and_rejects_duplicate_names() -> None:
  seen: list[str] = []

  class Probe(Plugin):
    name = "probe"

    @hook
    def on_tool(self, event: BeforeToolCallEvent | AfterToolCallEvent) -> None:
      seen.append(type(event).__name__)

  runner = HarnessRunner(compiled_graph=_loop_graph(1), tools={"ping": lambda value: value}, limits=LIMITS, plugins=[Probe()])
  runner.run("t", {"job_id": "j"})
  assert seen == ["BeforeToolCallEvent", "AfterToolCallEvent"]

  with pytest.raises(ValueError, match="already registered"):
    HarnessRunner(compiled_graph=_loop_graph(1), tools={}, limits=LIMITS, plugins=[Probe(), Probe()])


# ---------------------------------------------------------------------- 限额 / 取消


def test_turn_limit_stops_gracefully_and_keeps_state() -> None:
  runner = HarnessRunner(
    compiled_graph=_loop_graph(10),
    tools={"ping": lambda value: value},
    limits=HarnessLimits(max_turns=3, max_tokens=1000, max_graph_steps=50, timeout_seconds=30),
  )
  result = runner.run("t", {"job_id": "j"})
  assert result.stop_reason == "limit_turns"
  assert result.status == "guardrail_blocked"
  assert result.turns == 3
  assert result.output["count"] == 3  # 已完成节点的 state 被保留，不再是空 dict


def test_graph_step_limit() -> None:
  runner = HarnessRunner(
    compiled_graph=_loop_graph(10),
    tools={"ping": lambda value: value},
    limits=HarnessLimits(max_turns=100, max_tokens=1000, max_graph_steps=4, timeout_seconds=30),
  )
  result = runner.run("t", {"job_id": "j"})
  assert result.stop_reason == "limit_steps"
  assert result.output["count"] == 4


def test_timeout_cancels_at_next_checkpoint() -> None:
  runner = HarnessRunner(
    compiled_graph=_loop_graph(100, sleep=0.3),
    tools={"ping": lambda value: value},
    limits=HarnessLimits(max_turns=1000, max_tokens=1000, max_graph_steps=1000, timeout_seconds=1),
  )
  started = time.perf_counter()
  result = runner.run("t", {"job_id": "j"})
  assert time.perf_counter() - started < 3
  assert result.stop_reason == "cancelled"
  assert result.status == "timeout"
  assert 1 <= result.output["count"] < 100


def test_token_usage_counted_and_limited() -> None:
  ctx = _ctx()
  runner = HarnessRunner(
    compiled_graph=_loop_graph(1),
    tools={},
    limits=HarnessLimits(max_turns=10, max_tokens=40, max_graph_steps=10, timeout_seconds=30),
  )
  with harness_scope(runner, ctx, agent_id="hook_agent"):
    for _ in range(3):
      call_model(lambda messages: _Resp('{"ok": 1}', 10, 5), [{"role": "user", "content": "hi"}])
    assert ctx.token_usage == 45 and ctx.model_calls == 3
    from agent_service.harness import StopRun

    with pytest.raises(StopRun) as stop:
      call_model(lambda messages: _Resp("{}"), [])
  assert stop.value.stop_reason == "limit_tokens"


def test_stop_run_not_swallowed_by_except_exception() -> None:
  """StopRun 继承 BaseException：业务代码里的 except Exception 拦不住它。"""

  def swallowing_tool(value: int) -> int:
    return value

  def work(state: _State, config: Any) -> dict[str, Any]:
    harness = config["configurable"]["harness"]
    ctx = config["configurable"]["harness_ctx"]
    for _ in range(5):
      try:
        harness.call_tool(ctx, "ping", value=1)
      except Exception:  # noqa: BLE001, S110 - 模拟业务代码的宽泛捕获
        pass
    return {"count": 1}

  graph = StateGraph(_State)
  graph.add_node("work", harness_node("work", work))
  graph.set_entry_point("work")
  graph.add_edge("work", END)
  runner = HarnessRunner(
    compiled_graph=graph.compile(),
    tools={"ping": swallowing_tool},
    limits=HarnessLimits(max_turns=2, max_tokens=1000, max_graph_steps=10, timeout_seconds=30),
  )
  result = runner.run("t", {"job_id": "j"})
  assert result.stop_reason == "limit_turns"
  assert result.turns == 2


def test_parallel_specialists_stop_on_turn_limit(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  runner = create_diagnosis_harness(
    _tools(_rich_evidence()),
    graph=build_diagnosis_graph(),
    limits=HarnessLimits(max_turns=2, max_tokens=32000, max_graph_steps=120, timeout_seconds=30),
  )
  result = runner.run("job-limit", {"job_id": "job-limit"})
  assert result.stop_reason == "limit_turns"
  assert result.status == "guardrail_blocked"
  assert result.output["plan"], "plan 节点的结果应被保留"


# ---------------------------------------------------------------------- 审计 / 进度


def test_progress_reports_do_not_consume_turns_and_audit_is_not_duplicated(monkeypatch: pytest.MonkeyPatch) -> None:
  _patch_diagnosis(monkeypatch)
  progress: list[dict[str, Any]] = []
  tools = _tools(_rich_evidence())
  tools["report_agent_progress"] = lambda **kwargs: progress.append(kwargs) or {"ok": True}
  tool_calls = {"n": 0}
  for name in ("get_job_context", "get_video_evidence", "save_diagnosis_hypothesis"):
    original = tools[name]

    def counted(*args: Any, _fn: Any = original, **kwargs: Any) -> Any:
      tool_calls["n"] += 1
      return _fn(*args, **kwargs)

    tools[name] = counted

  result = HarnessRunner(compiled_graph=build_diagnosis_graph(), tools=tools, limits=LIMITS).run(
    "job-progress", {"job_id": "job-progress"}
  )
  assert result.status == "success"
  assert progress, "进度仍然会上报"
  assert result.turns == tool_calls["n"], "进度上报不再计入轮次"
  events = [item["event"] for item in result.audit_events]
  assert events.count("tool_call_started") == tool_calls["n"]
  assert events.count("infra_call") == len(progress)
  assert events[0] == "harness_started" and events[-1] == "harness_finished"
  assert "graph_step" in events


# ---------------------------------------------------------------------- interventions


class _DenyAll(InterventionHandler):
  name = "deny-all"

  def before_tool_call(self, event: BeforeToolCallEvent) -> Any:
    return Deny("no tools today")


class _NeverReached(InterventionHandler):
  name = "never"
  called = False

  def before_tool_call(self, event: BeforeToolCallEvent) -> Any:
    type(self).called = True
    return Proceed()


class _Guide(InterventionHandler):
  def __init__(self, name: str, text: str) -> None:
    self.name = name
    self.text = text

  def before_model_call(self, event: BeforeModelCallEvent) -> Any:
    return Guide(self.text)


def _runner_with(handlers: list[InterventionHandler], tools: dict[str, Any] | None = None) -> HarnessRunner:
  return HarnessRunner(
    compiled_graph=_loop_graph(1),
    tools=tools or {"ping": lambda value: value},
    limits=LIMITS,
    plugins=[LimitsPlugin(LIMITS), InterventionPlugin(handlers)],
  )


def test_deny_short_circuits_and_cancels_tool() -> None:
  runner = _runner_with([_DenyAll(), _NeverReached()])
  with pytest.raises(ToolCallCancelled, match="DENIED: no tools today"):
    runner.call_tool(_ctx(), "ping", value=1)
  assert _NeverReached.called is False


def test_guides_are_merged_into_one_message() -> None:
  runner = _runner_with([_Guide("a", "be brief"), _Guide("b", "cite refs")])
  seen: list[list[dict[str, Any]]] = []
  runner.call_model(_ctx(), lambda messages: seen.append(list(messages)) or _Resp("{}"), [{"role": "user", "content": "q"}])
  assert seen[0][-1] == {"role": "user", "content": "[a] be brief\n[b] cite refs"}


def test_transform_and_on_error_deny() -> None:
  class Boom(InterventionHandler):
    name = "boom"
    on_error = "deny"

    def before_tool_call(self, event: BeforeToolCallEvent) -> Any:
      raise RuntimeError("policy store down")

  received: list[int] = []
  runner = _runner_with([JobIdPinning()], tools={"fetch": lambda job_id: received.append(job_id) or job_id})
  ctx = _ctx()
  assert runner.call_tool(ctx, "fetch", job_id="other-job") == "job-1"

  failing = _runner_with([Boom()])
  with pytest.raises(ToolCallCancelled, match="policy store down"):
    failing.call_tool(_ctx(), "ping", value=1)

  def noop(event: Any) -> None:
    return None

  assert isinstance(Transform(apply=noop), Transform)


def test_specialist_tool_policy_denies_outside_allowed_tools() -> None:
  runner = _runner_with([SpecialistToolPolicy()], tools={"save_diagnosis_hypothesis": lambda **kw: "ok", "get_video_evidence": lambda **kw: "ev"})
  ctx = _ctx()
  assert runner.call_tool(ctx, "save_diagnosis_hypothesis", job_id="job-1") == "ok"  # 外层流程不受限
  with harness_scope(runner, ctx, agent_id="hook_agent"):
    assert runner.call_tool(ctx, "get_video_evidence", job_id="job-1") == "ev"
    with pytest.raises(ToolCallCancelled, match="DENIED"):
      runner.call_tool(ctx, "save_diagnosis_hypothesis", job_id="job-1")


def test_output_format_guard_retries_with_feedback_then_gives_up() -> None:
  import json

  runner = _runner_with([OutputFormatGuard(max_retries=2)])
  sent: list[list[dict[str, Any]]] = []
  replies = iter(["not json", '{"outcome": "FINDING"}'])

  def invoke(messages: list[dict[str, Any]]) -> _Resp:
    sent.append(list(messages))
    return _Resp(next(replies))

  _, parsed = runner.call_model(_ctx(), invoke, [{"role": "user", "content": "q"}], parse=lambda r: json.loads(r.content))
  assert parsed == {"outcome": "FINDING"}
  assert len(sent) == 2 and "无法解析" in sent[1][-1]["content"]

  always_bad = _runner_with([OutputFormatGuard(max_retries=2)])
  calls = {"n": 0}

  def bad(messages: list[dict[str, Any]]) -> _Resp:
    calls["n"] += 1
    return _Resp("still not json")

  with pytest.raises(json.JSONDecodeError):
    always_bad.call_model(_ctx(), bad, [], parse=lambda r: json.loads(r.content))
  assert calls["n"] == 3  # 1 次原始 + 2 次重试后收敛


def test_model_retry_plugin_retries_transient_errors_only() -> None:
  class RateLimitError(Exception):
    status_code = 429

  runner = HarnessRunner(
    compiled_graph=_loop_graph(1),
    tools={},
    limits=LIMITS,
    plugins=[ModelRetryPlugin(max_attempts=3, initial_delay=0)],
  )
  outcomes = iter([RateLimitError("slow down"), _Resp("{}")])

  def flaky(messages: list[dict[str, Any]]) -> Any:
    item = next(outcomes)
    if isinstance(item, Exception):
      raise item
    return item

  response, _ = runner.call_model(_ctx(), flaky, [])
  assert response.content == "{}"

  def broken(messages: list[dict[str, Any]]) -> Any:
    raise ValueError("bad request")

  with pytest.raises(ValueError):
    runner.call_model(_ctx(), broken, [])


@pytest.mark.parametrize(
  ("status", "message"),
  [
    (429, "Error code: 429 - You have no credits remaining. Add credits to continue using the API"),
    (429, "Error code: 429 - {'error': {'code': 'insufficient_quota'}}"),
    (402, "Insufficient Balance"),
    (401, "Incorrect API key provided"),
  ],
)
def test_model_retry_plugin_stops_run_on_account_errors(status: int, message: str) -> None:
  """余额不足 / key 无效：不重试，直接停止整个 run（否则每个专家失败后弃权，run 却显示成功）。"""
  from agent_service.harness import StopRun

  class APIStatusError(Exception):
    status_code = status

  calls = 0

  def broke(messages: list[dict[str, Any]]) -> Any:
    nonlocal calls
    calls += 1
    raise APIStatusError(message)

  runner = HarnessRunner(compiled_graph=_loop_graph(1), tools={}, limits=LIMITS, plugins=[ModelRetryPlugin(max_attempts=3, initial_delay=0)])
  ctx = _ctx()
  with pytest.raises(StopRun) as stop:
    runner.call_model(ctx, broke, [])
  assert calls == 1
  assert stop.value.stop_reason == "model_fatal"
  assert ctx.stop_reason == "model_fatal" and ctx.cancelled


def test_plain_rate_limit_is_still_retried() -> None:
  class RateLimitError(Exception):
    status_code = 429

  assert not ModelRetryPlugin().is_fatal(RateLimitError("Rate limit reached for requests"))


# ---------------------------------------------------------------------- 组装层


def test_build_harness_can_disable_builtin_plugins() -> None:
  harness = build_harness(_loop_graph(1), {"ping": lambda value: value}, limits=LIMITS, builtin_plugins=["limits"])
  assert [plugin.name for plugin in harness.plugins.plugins] == ["limits"]
  with pytest.raises(ValueError, match="Unknown builtin plugins"):
    build_harness(_loop_graph(1), {}, limits=LIMITS, builtin_plugins=["nope"])


def test_default_harness_has_audit_and_limits() -> None:
  names = [plugin.name for plugin in create_diagnosis_harness({}, graph=_loop_graph(1), limits=LIMITS).plugins.plugins]
  assert names == ["audit", "limits", "model-retry", "interventions", "fatal-tool-errors"]
  assert isinstance(AuditPlugin(), Plugin)


# ---------------------------------------------------------------------- HTTP 重试与熔断


def _client(handler: Any, breaker: CircuitBreaker | None = None) -> JavaBackendHttpClient:
  return JavaBackendHttpClient(
    base_url="http://java.test",
    api_key="k",
    max_retries=3,
    retry_backoff_seconds=0,
    transport=httpx.MockTransport(handler),
    circuit_breaker=breaker or CircuitBreaker(),
  )


def test_get_is_retried_on_5xx() -> None:
  calls = {"n": 0}

  def handler(request: httpx.Request) -> httpx.Response:
    calls["n"] += 1
    if calls["n"] < 3:
      return httpx.Response(503)
    return httpx.Response(200, json={"success": True, "data": {"ok": 1}})

  assert _client(handler).get("/x") == {"ok": 1}
  assert calls["n"] == 3


def test_post_is_not_retried_on_5xx_to_avoid_duplicate_writes() -> None:
  calls = {"n": 0}

  def handler(request: httpx.Request) -> httpx.Response:
    calls["n"] += 1
    return httpx.Response(502)

  with pytest.raises(JavaBackendError):
    _client(handler).post("/hypotheses", {"a": 1})
  assert calls["n"] == 1


def test_client_errors_do_not_open_breaker_but_server_errors_do() -> None:
  breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60)
  not_found = _client(lambda request: httpx.Response(404, text="nope"), breaker)
  for _ in range(3):
    with pytest.raises(JavaBackendError):
      not_found.get("/x")
  assert breaker.is_open is False

  down = _client(lambda request: httpx.Response(500), breaker)
  for _ in range(2):
    with pytest.raises(JavaBackendError):
      down.get("/x")
  assert breaker.is_open is True
  with pytest.raises(JavaBackendError, match="circuit breaker is open"):
    down.get("/x")


# ---------------------------------------------------------------------- 端到端：真实 LLM 路径经过 harness


def test_real_llm_path_goes_through_harness(monkeypatch: pytest.MonkeyPatch) -> None:
  """diagnose_dimension 的真实分支（有 API Key）通过 call_model 计 token，并在 JSON 不合法时带反馈重试。"""
  import dataclasses
  import json
  import threading

  from agent_service.llm import diagnosis_llm, provider

  real_settings = diagnosis_llm.get_settings()
  fake_settings = dataclasses.replace(diagnosis_llm.get_settings(), chat_api_key="test-key", llm_mock=False)
  monkeypatch.setattr(diagnosis_llm, "get_settings", lambda: fake_settings)

  lock = threading.Lock()
  first_call_by_dimension: set[str] = set()
  finding = {"outcome": "FINDING", "observation": "obs", "hypothesis_text": "h", "confidence": 0.9}

  class FakeLLM:
    def invoke(self, messages: list[dict[str, Any]]) -> _Resp:
      dimension = messages[0]["content"]
      with lock:
        first = dimension not in first_call_by_dimension
        first_call_by_dimension.add(dimension)
      # 每个维度第一次故意返回非法 JSON，第二次返回合法结果
      return _Resp("这不是 JSON" if first else json.dumps(finding), 100, 20)

  monkeypatch.setattr(provider, "get_chat_model", lambda: FakeLLM())

  runner = create_diagnosis_harness(_tools(_rich_evidence()), graph=build_diagnosis_graph(), limits=LIMITS)
  result = runner.run("job-llm", {"job_id": "job-llm"})

  assert result.status == "success", result.error
  calls = result.usage["modelCalls"]
  assert calls >= 6  # 每个维度至少 1 次非法 + 1 次重试（Evaluator 可能再触发一轮诊断）
  assert result.usage["totalTokens"] == calls * 120
  events = [item["event"] for item in result.audit_events]
  assert events.count("model_call_error") == 3  # 只有每个维度的第一次回复非法
  assert events.count("intervention_applied") == 3  # 每次非法回复都由 OutputFormatGuard 给出一次 Guide
  assert events.count("model_call_finished") == calls - 3
  assert real_settings is not None
