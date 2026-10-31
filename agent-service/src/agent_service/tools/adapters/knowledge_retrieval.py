from __future__ import annotations

from typing import Any

from agent_service.config import get_settings
from agent_service.knowledge import diagnosis_rubric_corpus
from agent_service.retrieval import (
  InMemoryHybridKnowledgeRetriever,
  KnowledgeQuery,
  KnowledgeRetriever,
)


class KnowledgeRetrievalToolAdapter:
  """Agent tool facade for knowledge evidence retrieval."""

  def __init__(self, retriever: KnowledgeRetriever | None = None) -> None:
    self._retriever = retriever or InMemoryHybridKnowledgeRetriever(diagnosis_rubric_corpus())

  def retrieve_knowledge(
    self,
    query_text: str,
    skill_code: str,
    knowledge_type: str,
    category: str = "",
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
    settings = get_settings()
    effective_top_k = top_k or settings.retrieval_top_k
    query = KnowledgeQuery(
      query_text=query_text,
      skill_code=skill_code,
      knowledge_type=knowledge_type,
      category=category,
      top_k=effective_top_k,
      filters=filters or {},
    )
    if settings.rerank_enabled or not isinstance(self._retriever, InMemoryHybridKnowledgeRetriever):
      result = self._retriever.retrieve(query)
    else:
      items = self._retriever.search_hybrid_rrf(query, final_top_k=max(1, effective_top_k))[: max(1, effective_top_k)]
      result = _hybrid_result_without_rerank(query, items)
    return {
      "items": [
        {
          "id": item.id,
          "evidenceRef": item.evidence_ref,
          "knowledgeType": item.knowledge_type,
          "skillCode": item.skill_code,
          "category": item.category,
          "title": item.title,
          "content": item.content,
          "source": item.source,
          "tags": item.tags,
          "version": item.version,
          "createdAt": item.created_at,
          "score": item.score,
          "metadata": {
            **item.metadata,
            "skill_code": item.skill_code,
            "knowledge_type": item.knowledge_type,
            "category": item.category,
            "source_id": item.source,
          },
        }
        for item in result.items
      ],
      "trace": {
        "skill_code": result.trace.skill_code,
        "query": result.trace.query,
        "knowledge_type": result.trace.knowledge_type,
        "retrieval_method": result.trace.retrieval_method,
        "bm25_count": result.trace.bm25_count,
        "vector_count": result.trace.vector_count,
        "rrf_count": result.trace.rrf_count,
        "rerank_count": result.trace.rerank_count,
        "top_k": result.trace.top_k,
        "latency_ms": result.trace.latency_ms,
        "selected_evidence_refs": result.trace.selected_evidence_refs,
      },
    }


def _hybrid_result_without_rerank(query: KnowledgeQuery, items: list[Any]) -> Any:
  from agent_service.retrieval.models import KnowledgeRetrievalResult, RetrievalTrace

  return KnowledgeRetrievalResult(
    query=query,
    items=items,
    trace=RetrievalTrace(
      skill_code=query.skill_code,
      query=query.query_text,
      knowledge_type=query.knowledge_type,
      retrieval_method="HYBRID_RRF",
      bm25_count=0,
      vector_count=0,
      rrf_count=len(items),
      rerank_count=0,
      top_k=query.top_k,
      latency_ms=0,
      selected_evidence_refs=[item.evidence_ref for item in items],
    ),
  )
