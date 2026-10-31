from __future__ import annotations


class Guardrails:
  """全局护栏：在 Harness 层统一校验，node 内不写护栏逻辑。"""

  def check_turn_limit(self, turns: int, max_turns: int) -> None:
    if turns >= max_turns:
      raise GuardrailExceeded(f"Max turns exceeded: {turns}/{max_turns}")

  def check_token_limit(self, token_usage: int, max_tokens: int) -> None:
    if token_usage >= max_tokens:
      raise GuardrailExceeded(f"Max tokens exceeded: {token_usage}/{max_tokens}")

  def check_graph_step_limit(self, graph_steps: int, max_graph_steps: int) -> None:
    if graph_steps >= max_graph_steps:
      raise GuardrailExceeded(f"Max graph steps exceeded: {graph_steps}/{max_graph_steps}")


class GuardrailExceeded(Exception):
  pass
