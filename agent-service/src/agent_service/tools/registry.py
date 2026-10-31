from __future__ import annotations

from typing import Any

from agent_service.tools.adapters.analysis_job import AnalysisJobToolAdapter
from agent_service.tools.adapters.http_client import JavaBackendHttpClient
from agent_service.tools.adapters.hypothesis import HypothesisToolAdapter
from agent_service.tools.adapters.knowledge_retrieval import KnowledgeRetrievalToolAdapter
from agent_service.tools.adapters.video_evidence import VideoEvidenceToolAdapter


def build_tool_registry(client: JavaBackendHttpClient | None = None) -> dict[str, Any]:
  http_client = client or JavaBackendHttpClient()
  job_adapter = AnalysisJobToolAdapter(http_client)
  evidence_adapter = VideoEvidenceToolAdapter(http_client)
  hypothesis_adapter = HypothesisToolAdapter(http_client)
  knowledge_adapter = KnowledgeRetrievalToolAdapter()

  return {
    "get_job_context": job_adapter.get_job_context,
    "get_video_evidence": evidence_adapter.get_video_evidence,
    "retrieve_knowledge": knowledge_adapter.retrieve_knowledge,
    "save_diagnosis_hypothesis": hypothesis_adapter.save_diagnosis_hypothesis,
    "save_diagnosis_result": hypothesis_adapter.save_diagnosis_result,
    "save_agent_draft_result": job_adapter.save_agent_draft_result,
    "report_agent_progress": job_adapter.report_agent_progress,
  }
