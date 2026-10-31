"""Harness 默认值集中在这里（参考 strands_harness/defaults.py）。"""

from __future__ import annotations

from agent_service.config import get_settings
from agent_service.harness.interventions import InterventionHandler, InterventionPlugin
from agent_service.harness.output_guard import OutputFormatGuard
from agent_service.harness.plugins.audit import AuditPlugin
from agent_service.harness.plugins.base import Plugin
from agent_service.harness.plugins.limits import LimitsPlugin
from agent_service.harness.plugins.model_retry import ModelRetryPlugin
from agent_service.harness.types import HarnessLimits

BUILTIN_PLUGIN_NAMES = ("audit", "limits", "model-retry", "interventions")


def default_limits() -> HarnessLimits:
  settings = get_settings()
  return HarnessLimits(
    max_turns=settings.harness_max_turns,
    max_tokens=settings.harness_max_tokens,
    max_graph_steps=settings.harness_max_graph_steps,
    timeout_seconds=settings.harness_timeout_seconds,
  )


def default_intervention_handlers() -> list[InterventionHandler]:
  return [OutputFormatGuard()]


def default_plugins(
  limits: HarnessLimits,
  extra_handlers: list[InterventionHandler] | None = None,
) -> list[Plugin]:
  return [
    AuditPlugin(),
    LimitsPlugin(limits),
    ModelRetryPlugin(),
    InterventionPlugin([*default_intervention_handlers(), *(extra_handlers or [])]),
  ]
