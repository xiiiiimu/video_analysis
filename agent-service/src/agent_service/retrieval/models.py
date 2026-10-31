from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

KNOWLEDGE_TYPES = {
  "HOOK_PATTERN",
  "STRUCTURE_PATTERN",
  "VALUE_DELIVERY_PATTERN",
  "ANALYSIS_RULE",
  "GOOD_CASE",
  "BAD_CASE",
  "CATEGORY_BEST_PRACTICE",
  "PLATFORM_GUIDELINE",
}


@dataclass(frozen=True)
class KnowledgeEvidence:
  id: str
  knowledge_type: str
  skill_code: str
  category: str
  title: str
  content: str
  source: str
  tags: list[str] = field(default_factory=list)
  version: str = "v1"
  created_at: str = ""
  score: float = 0.0
  metadata: dict[str, Any] = field(default_factory=dict)

  @property
  def evidence_ref(self) -> str:
    return f"KNOWLEDGE:{self.id}"


@dataclass(frozen=True)
class KnowledgeQuery:
  query_text: str
  skill_code: str
  knowledge_type: str
  category: str = ""
  top_k: int = 5
  filters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalTrace:
  skill_code: str
  query: str
  knowledge_type: str
  retrieval_method: str
  bm25_count: int
  vector_count: int
  rrf_count: int
  rerank_count: int
  top_k: int
  latency_ms: int
  selected_evidence_refs: list[str]


@dataclass(frozen=True)
class KnowledgeRetrievalResult:
  query: KnowledgeQuery
  items: list[KnowledgeEvidence]
  trace: RetrievalTrace


class KnowledgeRetriever(Protocol):
  def retrieve(self, query: KnowledgeQuery) -> KnowledgeRetrievalResult:
    """Retrieve domain knowledge for a bounded Diagnosis Skill ReAct step."""
