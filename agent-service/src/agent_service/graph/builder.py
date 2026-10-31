from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from agent_service.graph.edges.conditions import route_by_action
from agent_service.graph.initial_state import build_initial_state
from agent_service.graph.nodes.diagnose import diagnose_node
from agent_service.graph.nodes.evaluator import evaluator_node
from agent_service.graph.nodes.planner import plan_node
from agent_service.graph.nodes.supervisor import supervisor_node
from agent_service.graph.nodes.synthesizer import synthesizer_node
from agent_service.graph.nodes.tool_executor import tool_executor_node
from agent_service.graph.state import AgentGraphState
from agent_service.harness.graph_adapter import harness_node


class DiagnosisGraph:
  """
  编译后的 LangGraph + 本图的初始 state。

  harness 通过 ``initial_state(payload, run_id)`` 拿到初始 state，从而不需要认识任何业务字段；
  其它属性（invoke / stream / get_graph ...）都委托给编译后的图。
  """

  def __init__(self, compiled: Any) -> None:
    self.compiled = compiled

  def initial_state(self, input_payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    return build_initial_state(input_payload, run_id)

  def __getattr__(self, name: str) -> Any:
    return getattr(self.compiled, name)


def _add_node(graph: StateGraph, name: str, fn: Any) -> None:
  # 每个节点统一包装：自动发 BeforeNode / AfterNode 事件，业务节点里不再手动调用 on_graph_step
  graph.add_node(name, harness_node(name, fn))


def build_diagnosis_graph() -> DiagnosisGraph:
  """
  Deterministic outer workflow + bounded agentic inner loop：

  Planner → Evidence Tools → Parallel Diagnosis Skills → Evaluator
    → PASS → Synthesizer → END
    → RETRY_SKILL → Re-run affected Skill
    → REPLAN → Supervisor → target Specialist → Evaluator
    → FAILED → END

  Local ReAct lives inside each Diagnosis Skill, not in the outer workflow.
  """
  graph = StateGraph(AgentGraphState)

  _add_node(graph, "plan", plan_node)
  _add_node(graph, "tools", tool_executor_node)
  _add_node(graph, "diagnose", diagnose_node)
  _add_node(graph, "evaluate", evaluator_node)
  _add_node(graph, "synthesize", synthesizer_node)
  _add_node(graph, "supervise", supervisor_node)

  graph.set_entry_point("plan")
  graph.add_conditional_edges("plan", route_by_action, {"tools": "tools", "end": END})
  graph.add_conditional_edges("tools", route_by_action, {"tools": "tools", "diagnose": "diagnose", "end": END})
  graph.add_conditional_edges(
    "diagnose", route_by_action, {"diagnose": "diagnose", "evaluate": "evaluate", "end": END}
  )
  graph.add_conditional_edges(
    "evaluate",
    route_by_action,
    {"diagnose": "diagnose", "supervise": "supervise", "synthesize": "synthesize", "end": END},
  )
  graph.add_conditional_edges("supervise", route_by_action, {"diagnose": "diagnose", "end": END})
  graph.add_conditional_edges("synthesize", route_by_action, {"end": END})

  return DiagnosisGraph(graph.compile())


def build_parallel_skills_graph() -> DiagnosisGraph:
  """Compatibility baseline: fixed parallel skills, no Supervisor or global replanning edge."""
  graph = StateGraph(AgentGraphState)

  _add_node(graph, "plan", plan_node)
  _add_node(graph, "tools", tool_executor_node)
  _add_node(graph, "diagnose", diagnose_node)
  _add_node(graph, "evaluate", _parallel_baseline_evaluator_node)
  _add_node(graph, "synthesize", synthesizer_node)

  graph.set_entry_point("plan")
  graph.add_conditional_edges("plan", route_by_action, {"tools": "tools", "end": END})
  graph.add_conditional_edges("tools", route_by_action, {"tools": "tools", "diagnose": "diagnose", "end": END})
  graph.add_conditional_edges(
    "diagnose", route_by_action, {"diagnose": "diagnose", "evaluate": "evaluate", "end": END}
  )
  graph.add_conditional_edges("evaluate", route_by_action, {"diagnose": "diagnose", "synthesize": "synthesize", "end": END})
  graph.add_conditional_edges("synthesize", route_by_action, {"end": END})

  return DiagnosisGraph(graph.compile())


def _parallel_baseline_evaluator_node(state: AgentGraphState, config):
  baseline_state = {
    **state,
    "handoff_requests": [],
    "max_global_replans": 0,
  }
  return evaluator_node(baseline_state, config)
