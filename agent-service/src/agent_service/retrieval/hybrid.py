from __future__ import annotations

import math
import re
import time
from collections.abc import Iterable
from dataclasses import replace

from agent_service.retrieval.models import (
  KnowledgeEvidence,
  KnowledgeQuery,
  KnowledgeRetrievalResult,
  RetrievalTrace,
)
from agent_service.retrieval.rrf import reciprocal_rank_fusion

TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


class InMemoryHybridKnowledgeRetriever:
  """
  Lightweight local retriever for the agent runtime.

  It intentionally mirrors the old knowledge_system project's useful shape
  (BM25 channel + vector-like channel + RRF + rerank fallback) without bringing
  Elasticsearch, PGVector, Redis, or Java cache concerns into Python.
  """

  def __init__(self, corpus: Iterable[KnowledgeEvidence]) -> None:
    self._corpus = list(corpus)

  def retrieve(self, query: KnowledgeQuery) -> KnowledgeRetrievalResult:
    started = time.perf_counter()
    bm25 = self.search_bm25(query, limit=30)
    vector = self.search_vector(query, limit=30)
    fused = self.search_hybrid_rrf(query, final_top_k=30)
    reranked = self.rerank(query.query_text, fused)
    selected = reranked[: max(1, query.top_k)]
    if query.knowledge_type == "RUBRIC" and query.category:
      # 品类专属评分点（私有规范）全部带上，通用评分点按相关度取 top-k：私有规范是用户明确要求要检查的，不能被排序挤掉
      pinned = [item for item in self.filter_candidates(query) if item.category == query.category]
      selected = [*pinned, *[item for item in selected if item.id not in {row.id for row in pinned}]][
        : max(1, query.top_k) + len(pinned)
      ]
    latency_ms = int((time.perf_counter() - started) * 1000)
    trace = RetrievalTrace(
      skill_code=query.skill_code,
      query=query.query_text,
      knowledge_type=query.knowledge_type,
      retrieval_method="HYBRID_RRF_RERANK",
      bm25_count=len(bm25),
      vector_count=len(vector),
      rrf_count=len(fused),
      rerank_count=len(reranked),
      top_k=query.top_k,
      latency_ms=latency_ms,
      selected_evidence_refs=[item.evidence_ref for item in selected],
    )
    return KnowledgeRetrievalResult(query=query, items=selected, trace=trace)

  def filter_candidates(self, query: KnowledgeQuery) -> list[KnowledgeEvidence]:
    allowed_types = {query.knowledge_type}
    if query.knowledge_type == "DOMAIN_KNOWLEDGE":
      allowed_types = {
        "HOOK_PATTERN",
        "STRUCTURE_PATTERN",
        "VALUE_DELIVERY_PATTERN",
        "CATEGORY_BEST_PRACTICE",
        "PLATFORM_GUIDELINE",
      }
    if query.knowledge_type == "SIMILAR_CASE":
      allowed_types = {"GOOD_CASE", "BAD_CASE"}
    rubric = query.knowledge_type == "RUBRIC"  # 评分点：该维度下全部类型

    filtered: list[KnowledgeEvidence] = []
    for item in self._corpus:
      if not rubric and item.knowledge_type not in allowed_types:
        continue
      if item.skill_code and item.skill_code != query.skill_code:
        continue
      # 带品类的评分点只对同品类的查询生效；不带品类的通用评分点对所有查询生效
      if item.category and item.category != query.category:
        continue
      filtered.append(item)
    return filtered

  def search_bm25(self, query: KnowledgeQuery, limit: int) -> list[KnowledgeEvidence]:
    return self._bm25(query.query_text, self.filter_candidates(query), limit=limit)

  def search_vector(self, query: KnowledgeQuery, limit: int) -> list[KnowledgeEvidence]:
    return self._vector_like(query.query_text, self.filter_candidates(query), limit=limit)

  def search_hybrid_rrf(self, query: KnowledgeQuery, final_top_k: int) -> list[KnowledgeEvidence]:
    bm25 = self.search_bm25(query, limit=30)
    vector = self.search_vector(query, limit=30)
    fused = reciprocal_rank_fusion([vector, bm25], lambda item: item.id, final_top_k=final_top_k)
    return [replace(item, score=score) for item, score in fused]

  def rerank(self, query_text: str, candidates: list[KnowledgeEvidence]) -> list[KnowledgeEvidence]:
    return self._rerank(query_text, candidates)

  def _bm25(self, query_text: str, candidates: list[KnowledgeEvidence], limit: int) -> list[KnowledgeEvidence]:
    q_tokens = set(_tokenize(query_text))
    if not q_tokens:
      return []
    scored: list[KnowledgeEvidence] = []
    for item in candidates:
      tokens = _tokenize(" ".join([item.title, item.content, " ".join(item.tags)]))
      if not tokens:
        continue
      overlap = sum(1 for token in q_tokens if token in tokens)
      score = overlap / math.sqrt(len(tokens))
      if score > 0:
        scored.append(replace(item, score=score))
    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

  def _vector_like(
    self,
    query_text: str,
    candidates: list[KnowledgeEvidence],
    limit: int,
  ) -> list[KnowledgeEvidence]:
    q_tokens = set(_tokenize(query_text))
    if not q_tokens:
      return []
    scored: list[KnowledgeEvidence] = []
    for item in candidates:
      doc_tokens = set(_tokenize(" ".join([item.title, item.content, " ".join(item.tags)])))
      union = q_tokens | doc_tokens
      if not union:
        continue
      score = len(q_tokens & doc_tokens) / len(union)
      if score > 0:
        scored.append(replace(item, score=score))
    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

  def _rerank(self, query_text: str, candidates: list[KnowledgeEvidence]) -> list[KnowledgeEvidence]:
    q_tokens = set(_tokenize(query_text))
    reranked: list[KnowledgeEvidence] = []
    for index, item in enumerate(candidates):
      content = " ".join([item.title, item.content, " ".join(item.tags)])
      content_tokens = set(_tokenize(content))
      overlap = len(q_tokens & content_tokens)
      phrase_boost = 0.05 if query_text and query_text in content else 0.0
      type_boost = 0.03 if item.knowledge_type in {"ANALYSIS_RULE", "CATEGORY_BEST_PRACTICE"} else 0.0
      position_prior = 1.0 / (60 + index + 1)
      score = item.score + 0.15 * overlap + phrase_boost + type_boost + position_prior
      reranked.append(replace(item, score=score))
    return sorted(reranked, key=lambda item: item.score, reverse=True)


def _tokenize(text: str) -> list[str]:
  tokens: list[str] = []
  for token in TOKEN_RE.findall(text or ""):
    lowered = token.lower()
    if _contains_cjk(lowered):
      chars = [char for char in lowered if "\u4e00" <= char <= "\u9fff"]
      tokens.extend(chars)
      tokens.extend(chars[index] + chars[index + 1] for index in range(len(chars) - 1))
      ascii_part = "".join(char for char in lowered if not ("\u4e00" <= char <= "\u9fff"))
      if ascii_part:
        tokens.append(ascii_part)
    else:
      tokens.append(lowered)
  return tokens


def _contains_cjk(text: str) -> bool:
  return any("\u4e00" <= char <= "\u9fff" for char in text)
