from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from agent_service.knowledge import default_video_diagnosis_corpus, load_benchmark_corpus
from agent_service.retrieval.embeddings import (
  EmbeddingProvider,
  EmbeddingProviderError,
  OpenAIEmbeddingProvider,
  cosine_similarity,
)
from agent_service.retrieval.hybrid import InMemoryHybridKnowledgeRetriever
from agent_service.retrieval.models import KnowledgeEvidence, KnowledgeQuery

RetrievalStrategy = Literal[
  "BM25_ONLY",
  "EMBEDDING_ONLY",
  "HYBRID_BM25_EMBEDDING_RRF",
  "HYBRID_BM25_EMBEDDING_RRF_RERANK",
  "HYBRID_BM25_EMBEDDING_RRF_05_05",
  "FINAL_WEIGHTED_HYBRID",
  "VECTOR_ONLY",
  "HYBRID_RRF",
  "HYBRID_RRF_RERANK",
]
BenchmarkMode = Literal["RUNTIME", "SKILL_FILTERED", "GLOBAL"]
AgentVariant = Literal["VIDEO_EVIDENCE_ONLY", "RAG", "LOCAL_REACT", "EVALUATOR"]
MatchType = Literal["EXACT", "SEMANTIC", "MIXED"]
Difficulty = Literal["EXACT", "SEMANTIC", "MIXED", "EASY", "MEDIUM", "HARD", "ADVERSARIAL"]
AnnotationStatus = Literal["PENDING_REVIEW", "VERIFIED", "REJECTED"]
HardNegativeScope = Literal["INTRA_SKILL", "CROSS_SKILL", "MIXED", ""]

SMOKE_DATASET_VERSION = "video-diagnosis-rag-smoke-v0.1"
DEFAULT_DATASET_VERSION = "video-diagnosis-rag-formal-candidates-v0.2"
DEFAULT_RETRIEVER_PARAMS = {
  "bm25_limit": 30,
  "embedding_limit": 30,
  "rrf_k": 60,
  "final_top_k": 10,
  "rerank": "keyword_overlap_phrase_type_position_v1",
}
DEFAULT_STRATEGIES: list[RetrievalStrategy] = [
  "BM25_ONLY",
  "EMBEDDING_ONLY",
  "HYBRID_BM25_EMBEDDING_RRF",
  "HYBRID_BM25_EMBEDDING_RRF_RERANK",
]
V05_WEIGHTED_RRF_CONFIGS = {
  "bm25_0.7_embedding_0.3": {"bm25Weight": 0.7, "embeddingWeight": 0.3, "rrfK": 60},
  "bm25_0.5_embedding_0.5": {"bm25Weight": 0.5, "embeddingWeight": 0.5, "rrfK": 60},
  "bm25_0.3_embedding_0.7": {"bm25Weight": 0.3, "embeddingWeight": 0.7, "rrfK": 60},
}


@dataclass(frozen=True)
class GoldenRetrievalCase:
  query: str
  expected_refs: list[str] = field(default_factory=list)
  skill_code: str = ""
  knowledge_type: str = "DOMAIN_KNOWLEDGE"
  category: str = ""

  @property
  def expected_knowledge_ids(self) -> list[str]:
    return [ref.replace("KNOWLEDGE:", "") for ref in self.expected_refs]


@dataclass(frozen=True)
class GoldenQueryCase:
  query_id: str
  query: str
  skill_code: str
  knowledge_type: str
  expected_knowledge_ids: list[str]
  difficulty: Difficulty = "SEMANTIC"
  annotation_status: AnnotationStatus = "PENDING_REVIEW"
  category: str = ""
  notes: str = ""
  acceptable_knowledge_ids: list[str] = field(default_factory=list)
  hard_negative_knowledge_ids: list[str] = field(default_factory=list)
  match_type: MatchType = "SEMANTIC"
  hard_negative_scope: HardNegativeScope = ""

  @property
  def id(self) -> str:
    return self.query_id

  @property
  def needs_human_label(self) -> bool:
    return self.annotation_status != "VERIFIED"

  def to_retrieval_case(self) -> GoldenRetrievalCase:
    return GoldenRetrievalCase(
      query=self.query,
      expected_refs=[f"KNOWLEDGE:{item}" for item in self.expected_knowledge_ids],
      skill_code=self.skill_code,
      knowledge_type=self.knowledge_type,
      category=self.category,
    )


@dataclass(frozen=True)
class RetrievalRunConfig:
  dataset_version: str = DEFAULT_DATASET_VERSION
  corpus_version: str = "runtime"
  benchmark_mode: BenchmarkMode = "RUNTIME"
  model: str = "in_memory_bm25_embedding_benchmark"
  embedding_provider: str = "none"
  embedding_model: str = ""
  use_retrieval_text: bool = False
  bm25_weight: float = 0.5
  embedding_weight: float = 0.5
  rrf_k: int = 60
  top_k: int = 10
  repeat_count: int = 5
  verified_only: bool = True
  retriever_params: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_RETRIEVER_PARAMS))


@dataclass(frozen=True)
class RetrievalCaseResult:
  query_id: str
  strategy: RetrievalStrategy
  benchmark_mode: BenchmarkMode
  query: str
  skill_code: str
  difficulty: Difficulty
  match_type: MatchType
  knowledge_type: str
  expected_knowledge_ids: list[str]
  acceptable_knowledge_ids: list[str]
  hard_negative_knowledge_ids: list[str]
  actual_top_5: list[dict[str, Any]]
  ranked_knowledge_ids: list[str]
  candidate_pool_size: int
  recall_at_1: float
  recall_at_3: float
  recall_at_5: float
  recall_at_10: float
  mrr: float
  acceptable_hit_at_5: float
  hard_negative_above_expected: bool
  latency_runs_ms: list[float]
  embedding_generation_latency_ms: float
  retrieval_ranking_latency_ms: float
  end_to_end_latency_ms: float
  embedding_cache_hit: bool
  embedding_latency_included_in_end_to_end: bool
  avg_latency_ms: float
  p50_latency_ms: float
  p95_latency_ms: float


@dataclass(frozen=True)
class RetrievalExperimentReport:
  dataset_version: str
  corpus_version: str
  verified_sample_count: int
  corpus_size: int
  benchmark_mode: BenchmarkMode
  candidate_pool: dict[str, float]
  configuration: dict[str, Any]
  model: str
  embedding_provider: str
  embedding_model: str
  embedding_dimension: int
  retriever_params: dict[str, Any]
  run_started_at: str
  run_finished_at: str
  strategies: dict[str, dict[str, float]]
  by_skill_code: dict[str, dict[str, dict[str, float]]]
  by_difficulty: dict[str, dict[str, dict[str, float]]]
  by_match_type: dict[str, dict[str, dict[str, float]]]
  recall_at_5_misses: list[dict[str, Any]]
  cases: list[dict[str, Any]]

  @property
  def sample_count(self) -> int:
    return self.verified_sample_count

  @property
  def config(self) -> dict[str, Any]:
    return self.configuration


@dataclass(frozen=True)
class GoldenFinding:
  id: str
  skill_code: str
  label: str
  evidence_refs: list[str] = field(default_factory=list)
  finding_type: str = ""


@dataclass(frozen=True)
class PredictedFinding:
  id: str
  skill_code: str
  label: str
  evidence_refs: list[str] = field(default_factory=list)
  supported: bool = True
  finding_type: str = ""


@dataclass(frozen=True)
class AgentGoldenCase:
  id: str
  video_case_id: str
  golden_findings: list[GoldenFinding] = field(default_factory=list)
  notes: str = ""
  needs_human_label: bool = True


@dataclass(frozen=True)
class AgentVariantPrediction:
  case_id: str
  variant: AgentVariant
  findings: list[PredictedFinding] = field(default_factory=list)


@dataclass(frozen=True)
class AgentBenchmarkReport:
  dataset_version: str
  sample_count: int
  config: dict[str, Any]
  model: str
  run_started_at: str
  run_finished_at: str
  variants: dict[str, dict[str, float]]
  cases: list[dict[str, Any]]


@dataclass(frozen=True)
class WeightedRrfConfig:
  bm25_weight: float = 0.5
  embedding_weight: float = 0.5
  rrf_k: int = 60


def weighted_reciprocal_rank_fusion(
  bm25_ranked: list[KnowledgeEvidence],
  embedding_ranked: list[KnowledgeEvidence],
  config: WeightedRrfConfig,
  *,
  final_top_k: int,
) -> list[tuple[KnowledgeEvidence, float]]:
  item_map: dict[str, KnowledgeEvidence] = {}
  score_map: dict[str, float] = {}
  for weight, ranked in [
    (config.bm25_weight, bm25_ranked),
    (config.embedding_weight, embedding_ranked),
  ]:
    for rank, item in enumerate(ranked, start=1):
      item_map.setdefault(item.id, item)
      score_map[item.id] = score_map.get(item.id, 0.0) + weight / (config.rrf_k + rank)
  return [
    (item_map[item_id], score)
    for item_id, score in sorted(score_map.items(), key=lambda entry: entry[1], reverse=True)[
      :final_top_k
    ]
  ]


_DISTINGUISH_FROM: dict[str, list[str]] = {
  "hook-pattern-curiosity-gap-v1": [
    "empty_suspense: effective curiosity must promise concrete unresolved information; empty suspense only asks viewers to wait.",
    "first_three_seconds: this focuses on the curiosity mechanism, not only the opening time window.",
  ],
  "hook-bad-case-empty-suspense-v1": [
    "curiosity_gap: the positive pattern has a concrete object, conflict, or outcome; this case lacks a specific information promise.",
  ],
  "hook-pattern-self-intro-delay-v1": [
    "authority_fast: delayed self-introduction postpones user payoff; fast authority immediately connects credibility to user benefit.",
  ],
  "hook-good-case-authority-fast-v1": [
    "self_intro_delay: authority is acceptable only when it quickly serves the viewer's expected outcome.",
  ],
  "hook-good-case-visual-proof-v1": [
    "value_proof_before_claim: hook visual proof earns first-screen attention; value proof supports a claim across the whole content.",
  ],
  "value-good-case-proof-before-claim-v1": [
    "visual_hook_proof: value proof establishes credibility for a claim, not merely first-screen stopping power.",
    "example_driven_structure: proof supports credibility; examples in structure mainly help explanation and flow.",
  ],
  "structure-pattern-contrast-before-after-v1": [
    "before_after_value_outcome: this item concerns content order and progression; the value rule concerns proving benefit through outcome change.",
  ],
  "value-rule-before-after-outcome-v1": [
    "before_after_structure: this item concerns value evidence and outcome credibility, not narrative sequence alone.",
  ],
  "structure-rule-density-scene-change-v1": [
    "static_talking_bad_case: this is a compensation rule; static talking is the failure state when no compensation exists.",
  ],
  "structure-bad-case-static-talking-v1": [
    "density_scene_change_rule: the bad case is not static footage alone, but static footage without pacing compensation.",
  ],
  "structure-rule-midpoint-retention-v1": [
    "value_specificity: midpoint retention asks whether the content keeps advancing; specificity asks whether benefits are concrete.",
  ],
  "value-rule-specificity-v1": [
    "midpoint_retention: specificity is about measurable or perceivable value, not whether the middle section keeps progressing.",
  ],
  "value-pattern-actionable-advice-v1": [
    "cta_fit: actionable advice asks whether the viewer can do something; CTA fit asks whether the requested action matches prior value.",
  ],
  "value-rule-call-to-action-fit-v1": [
    "actionable_advice: CTA alignment is about the final requested action matching the promise, not merely providing next steps.",
  ],
}


def benchmark_retrieval_text(item: KnowledgeEvidence) -> str:
  """Benchmark-only retrieval text with semantic boundaries, never persisted to runtime corpus."""
  fields = {
    "title": item.title,
    "definition": item.content,
    "applicableConditions": _applicable_conditions(item),
    "nonApplicableConditions": _non_applicable_conditions(item),
    "distinguishFrom": _DISTINGUISH_FROM.get(item.id, []),
    "typicalSignals": item.tags,
  }
  lines: list[str] = []
  for key, value in fields.items():
    if isinstance(value, list):
      if value:
        lines.append(f"{key}: " + "; ".join(value))
    elif value:
      lines.append(f"{key}: {value}")
  return "\n".join(lines)


def _applicable_conditions(item: KnowledgeEvidence) -> list[str]:
  focus = item.metadata.get("diagnosticFocus", "")
  if focus == "OPENING_RETENTION":
    return ["use when judging first-screen stopping power", "prioritize viewer payoff timing"]
  if focus == "STRUCTURE_FLOW":
    return ["use when judging content order, transitions, or section progression"]
  if focus == "MIDPOINT_RETENTION":
    return ["use when judging whether the middle section keeps attention and adds new information"]
  if focus == "VALUE_CLARITY":
    return ["use when judging whether viewer outcome, scenario, or benefit is clear"]
  if focus == "VALUE_CREDIBILITY":
    return ["use when judging whether evidence supports the value claim"]
  if focus == "ACTION_ALIGNMENT":
    return ["use when judging whether the viewer can act and whether the action matches the promise"]
  return ["use when the item's definition matches the diagnosis target"]


def _non_applicable_conditions(item: KnowledgeEvidence) -> list[str]:
  focus = item.metadata.get("diagnosticFocus", "")
  if focus == "OPENING_RETENTION":
    return ["do not use as the main answer for full-video value delivery unless opening retention is central"]
  if focus == "STRUCTURE_FLOW":
    return ["do not use when the issue is only benefit credibility or value specificity"]
  if focus == "MIDPOINT_RETENTION":
    return ["do not use when the issue is only first-screen hook timing"]
  if focus == "VALUE_CLARITY":
    return ["do not use when the issue is only section order or visual pacing"]
  if focus == "VALUE_CREDIBILITY":
    return ["do not use when evidence is only a first-screen attention device"]
  if focus == "ACTION_ALIGNMENT":
    return ["do not use when the issue is only opening curiosity or paragraph transition"]
  return []


class BenchmarkKnowledgeRetriever:
  """Benchmark-only retriever with explicit candidate pool controls."""

  def __init__(
    self,
    corpus: list[KnowledgeEvidence],
    mode: BenchmarkMode,
    embedding_provider: EmbeddingProvider | None = None,
    *,
    use_retrieval_text: bool = False,
    weighted_rrf_config: WeightedRrfConfig | None = None,
  ) -> None:
    self._corpus = list(corpus)
    self._mode = mode
    self._embedding_provider = embedding_provider
    self._use_retrieval_text = use_retrieval_text
    self._weighted_rrf_config = weighted_rrf_config or WeightedRrfConfig()
    self._corpus_embedding_by_id: dict[str, list[float]] = {}
    self._query_embedding_by_text: dict[str, list[float]] = {}
    self.last_embedding_generation_latency_ms = 0.0
    self.last_embedding_cache_hit = False
    self._scorer = InMemoryHybridKnowledgeRetriever(corpus)
    if self._embedding_provider is not None:
      texts = [self._embedding_text(item) for item in self._corpus]
      vectors = self._embedding_provider.embed_batch(texts)
      if len(vectors) != len(self._corpus):
        raise EmbeddingProviderError(
          f"Embedding provider returned {len(vectors)} vectors for {len(self._corpus)} corpus items."
        )
      self._corpus_embedding_by_id = {
        item.id: list(vector)
        for item, vector in zip(self._corpus, vectors)
      }

  def candidate_pool(self, query: KnowledgeQuery) -> list[KnowledgeEvidence]:
    if self._mode == "GLOBAL":
      return list(self._corpus)
    if self._mode == "SKILL_FILTERED":
      return [item for item in self._corpus if item.skill_code == query.skill_code]
    return self._scorer.filter_candidates(query)

  def candidate_pool_size(self, query: KnowledgeQuery) -> int:
    return len(self.candidate_pool(query))

  def search_bm25(self, query: KnowledgeQuery, limit: int) -> list[KnowledgeEvidence]:
    return self._scorer._bm25(query.query_text, self._retrieval_candidates(query), limit=limit)

  def search_vector(self, query: KnowledgeQuery, limit: int) -> list[KnowledgeEvidence]:
    return self._scorer._vector_like(query.query_text, self.candidate_pool(query), limit=limit)

  def search_embedding(self, query: KnowledgeQuery, limit: int) -> list[KnowledgeEvidence]:
    if self._embedding_provider is None:
      raise EmbeddingProviderError(
        "Embedding retrieval requires an EmbeddingProvider. Configure --embedding-provider openai "
        "or pass a provider in tests."
      )
    query_vector = self._query_embedding_by_text.get(query.query_text)
    if query_vector is None:
      started_embedding = time.perf_counter()
      query_vector = self._embedding_provider.embed(query.query_text)
      self.last_embedding_generation_latency_ms = (time.perf_counter() - started_embedding) * 1000
      self._query_embedding_by_text[query.query_text] = query_vector
      self.last_embedding_cache_hit = False
    else:
      self.last_embedding_generation_latency_ms = 0.0
      self.last_embedding_cache_hit = True
    scored: list[KnowledgeEvidence] = []
    from dataclasses import replace

    for item in self.candidate_pool(query):
      corpus_vector = self._corpus_embedding_by_id.get(item.id)
      if corpus_vector is None:
        raise EmbeddingProviderError(f"Missing corpus embedding for knowledge ID: {item.id}")
      scored.append(replace(item, score=cosine_similarity(query_vector, corpus_vector)))
    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]

  def search_hybrid_rrf(self, query: KnowledgeQuery, final_top_k: int) -> list[KnowledgeEvidence]:
    bm25 = self.search_bm25(query, limit=30)
    embedding = self.search_embedding(query, limit=30)
    fused = weighted_reciprocal_rank_fusion(
      bm25,
      embedding,
      self._weighted_rrf_config,
      final_top_k=final_top_k,
    )
    from dataclasses import replace

    return [replace(item, score=score) for item, score in fused]

  def retrieve(self, query: KnowledgeQuery) -> list[KnowledgeEvidence]:
    return self._scorer.rerank(query.query_text, self.search_hybrid_rrf(query, final_top_k=30))[: max(1, query.top_k)]

  @staticmethod
  def _base_embedding_text(item: KnowledgeEvidence) -> str:
    return " ".join([item.title, item.content, " ".join(item.tags)])

  def _embedding_text(self, item: KnowledgeEvidence) -> str:
    return benchmark_retrieval_text(item) if self._use_retrieval_text else self._base_embedding_text(item)

  def _retrieval_candidates(self, query: KnowledgeQuery) -> list[KnowledgeEvidence]:
    if not self._use_retrieval_text:
      return self.candidate_pool(query)
    from dataclasses import replace

    return [
      replace(item, content=benchmark_retrieval_text(item), tags=[])
      for item in self.candidate_pool(query)
    ]


def smoke_golden_query_dataset() -> list[GoldenQueryCase]:
  """Six-case smoke dataset for pipeline checks only; not a formal benchmark."""
  return [
    _case("smoke-hook-domain-opening-pain-v1", "hook_analysis", "前三秒如何用痛点和收益建立钩子", "DOMAIN_KNOWLEDGE", "hook-pattern-opening-pain-v1", "EXACT", "VERIFIED", "Smoke only."),
    _case("smoke-hook-similar-good-benefit-v1", "hook_analysis", "开头直接给出利益点的优秀案例", "SIMILAR_CASE", "hook-good-case-direct-benefit-v1", "EXACT", "VERIFIED", "Smoke only."),
    _case("smoke-structure-domain-three-act-v1", "structure_rhythm_analysis", "短视频结构如何按问题展开收束组织", "DOMAIN_KNOWLEDGE", "structure-pattern-three-act-v1", "EXACT", "VERIFIED", "Smoke only."),
    _case("smoke-structure-rule-density-v1", "structure_rhythm_analysis", "镜头长期不变时如何诊断信息密度和节奏", "ANALYSIS_RULE", "structure-rule-density-v1", "EXACT", "VERIFIED", "Smoke only."),
    _case("smoke-value-domain-clear-outcome-v1", "value_delivery_analysis", "如何判断视频是否讲清楚观众收益和行动建议", "DOMAIN_KNOWLEDGE", "value-delivery-pattern-clear-outcome-v1", "EXACT", "VERIFIED", "Smoke only."),
    _case("smoke-value-similar-bad-vague-benefit-v1", "value_delivery_analysis", "只讲功能不讲收益的反例", "SIMILAR_CASE", "value-bad-case-vague-benefit-v1", "EXACT", "VERIFIED", "Smoke only."),
  ]


def default_golden_query_dataset() -> list[GoldenQueryCase]:
  """Backward-compatible alias for smoke tests, not the formal benchmark dataset."""
  return smoke_golden_query_dataset()


def formal_candidate_query_dataset() -> list[GoldenQueryCase]:
  """At least 60 candidate queries. All are pending human review by design."""
  cases: list[GoldenQueryCase] = []
  cases.extend(_candidate_cases("hook_analysis", "DOMAIN_KNOWLEDGE", "hook-pattern-opening-pain-v1", "hook-pattern", [
    ("用户刷到视频第一眼没停留，应该检索哪类开场钩子规则", "SEMANTIC"),
    ("评估开头有没有先给痛点再给收益，需要参考什么标准", "EXACT"),
    ("视频前几秒一直铺垫背景，想判断是否拖慢兴趣建立", "MIXED"),
    ("首屏没有反常识也没有价值预期，应该找哪条钩子知识", "SEMANTIC"),
    ("诊断开场是否快速制造情绪张力和继续看的理由", "MIXED"),
    ("开头先自我介绍而不是讲用户问题，该用什么规则评估", "SEMANTIC"),
    ("前三秒文案平淡，需要判断是否缺少利益承诺", "MIXED"),
    ("想检查短视频开场有没有把观众痛点前置", "EXACT"),
    ("用户不知道为什么要继续看，应该参考哪类 hook pattern", "SEMANTIC"),
    ("视频开头没有明确结果感，如何找钩子诊断依据", "MIXED"),
  ]))
  cases.extend(_candidate_cases("hook_analysis", "SIMILAR_CASE", "hook-good-case-direct-benefit-v1", "hook-good-case", [
    ("想找开头直接说明省钱省时收益的参考案例", "EXACT"),
    ("对比优秀视频首屏如何让用户马上看到好处", "SEMANTIC"),
    ("需要一个利益点先行的 hook 正向样例", "MIXED"),
    ("首句就承诺结果的短视频案例应该检索哪条知识", "SEMANTIC"),
    ("想看优秀口播怎样在开头给出可感知收益", "EXACT"),
    ("用什么案例说明开场先给价值比先铺垫更有效", "MIXED"),
    ("找一个开头就告诉观众能获得什么的好案例", "SEMANTIC"),
    ("诊断首屏收益表达时需要正向对照样本", "MIXED"),
    ("参考视频开头先讲避坑收益，这属于哪类案例", "SEMANTIC"),
    ("需要首屏给利益点的 good case 做判断基准", "EXACT"),
  ]))
  cases.extend(_candidate_cases("structure_rhythm_analysis", "DOMAIN_KNOWLEDGE", "structure-pattern-three-act-v1", "structure-pattern", [
    ("视频内容散乱时应该检索哪种问题展开收束结构", "SEMANTIC"),
    ("判断短视频有没有按问题引入再行动收尾组织", "EXACT"),
    ("段落之间没有承接，想找结构节奏的组织规则", "MIXED"),
    ("视频说了很多点但没有主线，应该参考什么结构模式", "SEMANTIC"),
    ("分析脚本是否有开头问题中段解释结尾建议", "EXACT"),
    ("内容从痛点跳到卖点再跳回背景，如何找结构诊断依据", "MIXED"),
    ("评估短视频是否有清楚的段落转场和收束", "SEMANTIC"),
    ("视频节奏混乱，想找三段式信息组织知识", "MIXED"),
    ("判断内容有没有先提问再展开关键点", "EXACT"),
    ("需要结构模式来检查观众能不能跟上叙事", "SEMANTIC"),
  ]))
  cases.extend(_candidate_cases("structure_rhythm_analysis", "ANALYSIS_RULE", "structure-rule-density-v1", "structure-rule", [
    ("画面长时间不变时怎么判断信息密度是否不足", "EXACT"),
    ("镜头变化少但口播很多，应该检索什么节奏规则", "MIXED"),
    ("想分析转场信号少会不会影响注意力维持", "SEMANTIC"),
    ("视频一直同一场景，需要找节奏和镜头变化的诊断规则", "EXACT"),
    ("检查信息密度和段落切换是否支撑完播", "MIXED"),
    ("没有明显转场时如何评估短视频节奏风险", "SEMANTIC"),
    ("画面不动但文案在讲卖点，应该参考哪条 analysis rule", "MIXED"),
    ("判断镜头切换频率是否太低需要什么依据", "EXACT"),
    ("观众注意力可能掉线，想找节奏诊断规则", "SEMANTIC"),
    ("视频中段信息堆叠但视觉变化弱，如何找规则", "MIXED"),
  ]))
  cases.extend(_candidate_cases("value_delivery_analysis", "DOMAIN_KNOWLEDGE", "value-delivery-pattern-clear-outcome-v1", "value-pattern", [
    ("判断视频有没有说清楚观众最终能得到什么", "EXACT"),
    ("内容讲了很多功能但收益不明确，需要什么价值表达标准", "MIXED"),
    ("想检查文案是否包含对象场景结果和行动建议", "EXACT"),
    ("视频价值点模糊，应该检索哪类收益表达知识", "SEMANTIC"),
    ("用户看完不知道下一步做什么，如何找价值传递依据", "MIXED"),
    ("诊断是否把结果感和使用场景讲清楚", "SEMANTIC"),
    ("评估观众收益有没有被具体化", "EXACT"),
    ("视频只说产品很好，想判断有没有明确 outcome", "MIXED"),
    ("需要检查行动建议是否和用户收益连接起来", "SEMANTIC"),
    ("找价值传递标准来判断内容是不是只讲过程", "MIXED"),
  ]))
  cases.extend(_candidate_cases("value_delivery_analysis", "SIMILAR_CASE", "value-bad-case-vague-benefit-v1", "value-bad-case", [
    ("找一个只罗列功能却没有说用户收益的反例", "EXACT"),
    ("视频一直讲成分和流程，但没有解释为什么要看完", "MIXED"),
    ("需要模糊收益表达的 bad case 做对照", "SEMANTIC"),
    ("判断内容是不是只讲功能不讲结果，可以参考什么反例", "EXACT"),
    ("卖点很多但用户动机不强，想找负面案例", "MIXED"),
    ("视频没有说明现在行动的理由，属于哪种价值传递问题", "SEMANTIC"),
    ("想对照一个只讲过程没有收益落点的案例", "EXACT"),
    ("内容围绕产品特点展开但缺少用户视角，找什么案例", "MIXED"),
    ("观众不知道为什么需要这个方案，应该检索哪条反例", "SEMANTIC"),
    ("评估价值表达空泛时需要 bad case 参考", "MIXED"),
  ]))
  _assert_expected_ids_exist(cases)
  return cases


def benchmark_v03_candidate_query_dataset() -> list[GoldenQueryCase]:
  """Sixty v0.3 retrieval-discrimination candidates. All labels require human review."""
  rows = [
    # hook_analysis: 20
    ("v03-hook-001", "hook_analysis", "开头一直讲自己做账号三年，第四秒才说粉丝能少踩什么坑", "HOOK_PATTERN", ["hook-pattern-self-intro-delay-v1"], ["hook-good-case-authority-fast-v1"], [], "MIXED", "MEDIUM", "INTRA_SKILL"),
    ("v03-hook-002", "hook_analysis", "第一句说自己是营养师，下一句马上告诉宝妈怎么避开配料表陷阱", "GOOD_CASE", ["hook-good-case-authority-fast-v1"], ["hook-pattern-self-intro-delay-v1"], [], "SEMANTIC", "HARD", "INTRA_SKILL"),
    ("v03-hook-003", "hook_analysis", "前三秒同时点出上班族的痛点和马上能看到的改善结果", "HOOK_PATTERN", ["hook-pattern-pain-benefit-v2"], ["value-pattern-audience-outcome-v1"], ["hook-rule-first-three-seconds-v1"], "EXACT", "EASY", "MIXED"),
    ("v03-hook-004", "hook_analysis", "开头说“别急着买这个”，但立刻给出一个具体踩坑场景", "HOOK_PATTERN", ["hook-pattern-curiosity-gap-v1"], ["hook-bad-case-empty-suspense-v1"], [], "SEMANTIC", "HARD", "INTRA_SKILL"),
    ("v03-hook-005", "hook_analysis", "文案只说看到最后你就明白，没有说对象、问题或结果", "BAD_CASE", ["hook-bad-case-empty-suspense-v1"], ["hook-pattern-curiosity-gap-v1"], ["value-bad-case-vague-claim-v1"], "MIXED", "MEDIUM", "MIXED"),
    ("v03-hook-006", "hook_analysis", "首屏没有明确谁该看、为什么看，也没有冲突点", "ANALYSIS_RULE", ["hook-rule-first-three-seconds-v1"], ["hook-bad-case-generic-opening-v1"], ["structure-rule-opening-transition-v1"], "SEMANTIC", "HARD", "MIXED"),
    ("v03-hook-007", "hook_analysis", "封面和第一帧直接露出改造前后效果，先让人停住再解释过程", "GOOD_CASE", ["hook-good-case-visual-proof-v1"], ["value-good-case-proof-before-claim-v1"], ["structure-pattern-contrast-before-after-v1"], "MIXED", "MEDIUM", "MIXED"),
    ("v03-hook-008", "hook_analysis", "开场第一句话点名新手妈妈，但后面还要马上接具体困扰", "HOOK_PATTERN", ["hook-pattern-target-audience-v1"], ["value-pattern-use-scenario-v1"], [], "EXACT", "EASY", "CROSS_SKILL"),
    ("v03-hook-009", "hook_analysis", "视频从“大家好今天来聊聊”开始，用户完全不知道和自己有什么关系", "BAD_CASE", ["hook-bad-case-generic-opening-v1"], ["structure-pattern-topic-list-v1"], [], "SEMANTIC", "MEDIUM", "MIXED"),
    ("v03-hook-010", "hook_analysis", "第六秒才出现省钱结果，前面也没有情绪张力或悬念支撑", "ANALYSIS_RULE", ["hook-rule-avoid-late-payoff-v1"], ["structure-rule-slow-burn-exception-v1"], [], "MIXED", "HARD", "MIXED"),
    ("v03-hook-011", "hook_analysis", "信息流里用户只看到第一屏时，需要先判断开场是否给出停留理由", "PLATFORM_GUIDELINE", ["hook-platform-short-feed-v1"], ["hook-rule-first-three-seconds-v1"], [], "EXACT", "EASY", "INTRA_SKILL"),
    ("v03-hook-012", "hook_analysis", "一上来念参数和成分，但没说这些跟用户痛点有什么关系", "BAD_CASE", ["hook-bad-case-feature-first-v1"], ["value-bad-case-feature-without-benefit-v1"], [], "MIXED", "HARD", "CROSS_SKILL"),
    ("v03-hook-013", "hook_analysis", "开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误", "HOOK_PATTERN", ["hook-pattern-curiosity-gap-v1"], ["hook-rule-first-three-seconds-v1"], ["hook-bad-case-empty-suspense-v1"], "SEMANTIC", "MEDIUM", "INTRA_SKILL"),
    ("v03-hook-014", "hook_analysis", "老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓", "GOOD_CASE", ["hook-good-case-authority-fast-v1"], ["hook-pattern-self-intro-delay-v1"], [], "MIXED", "MEDIUM", "INTRA_SKILL"),
    ("v03-hook-015", "hook_analysis", "第一屏给了价格对比截图，真正要判断的是能不能抓住滑走用户", "GOOD_CASE", ["hook-good-case-visual-proof-v1"], ["value-good-case-proof-before-claim-v1"], [], "SEMANTIC", "ADVERSARIAL", "CROSS_SKILL"),
    ("v03-hook-016", "hook_analysis", "开头先讲产品有五种模式，但没告诉观众能解决什么麻烦", "BAD_CASE", ["hook-bad-case-feature-first-v1", "hook-pattern-pain-benefit-v2"], ["value-bad-case-feature-without-benefit-v1"], [], "MIXED", "ADVERSARIAL", "MIXED"),
    ("v03-hook-017", "hook_analysis", "前三秒已经点名租房党和霉味问题，但没有展开解决步骤", "HOOK_PATTERN", ["hook-pattern-target-audience-v1", "hook-rule-first-three-seconds-v1"], ["value-pattern-use-scenario-v1"], [], "MIXED", "ADVERSARIAL", "MIXED"),
    ("v03-hook-018", "hook_analysis", "“今天给大家分享一下我的经验”之后还在寒暄，没有任何结果承诺", "BAD_CASE", ["hook-bad-case-generic-opening-v1", "hook-pattern-self-intro-delay-v1"], [], ["hook-good-case-authority-fast-v1"], "SEMANTIC", "HARD", "INTRA_SKILL"),
    ("v03-hook-019", "hook_analysis", "短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面", "ANALYSIS_RULE", ["hook-rule-avoid-late-payoff-v1"], ["value-pattern-audience-outcome-v1"], ["structure-rule-slow-burn-exception-v1"], "SEMANTIC", "MEDIUM", "MIXED"),
    ("v03-hook-020", "hook_analysis", "开场用一句身份建立信任，但如果后续没有马上接用户结果就会变成铺垫", "GOOD_CASE", ["hook-good-case-authority-fast-v1", "hook-pattern-self-intro-delay-v1"], [], [], "MIXED", "ADVERSARIAL", "INTRA_SKILL"),
    # structure_rhythm_analysis: 20
    ("v03-structure-001", "structure_rhythm_analysis", "脚本先抛问题，再解释原因，最后给一个收尾动作", "STRUCTURE_PATTERN", ["structure-pattern-problem-expand-close-v1"], ["value-pattern-actionable-advice-v1"], [], "EXACT", "EASY", "CROSS_SKILL"),
    ("v03-structure-002", "structure_rhythm_analysis", "三个要点并列讲，但每一点之间没有递进关系，像清单又不像清单", "STRUCTURE_PATTERN", ["structure-pattern-topic-list-v1"], ["hook-bad-case-generic-opening-v1"], [], "SEMANTIC", "MEDIUM", "MIXED"),
    ("v03-structure-003", "structure_rhythm_analysis", "钩子承诺避坑，正文却突然开始介绍品牌历史，连接断了", "ANALYSIS_RULE", ["structure-rule-opening-transition-v1"], ["hook-rule-first-three-seconds-v1"], [], "MIXED", "HARD", "MIXED"),
    ("v03-structure-004", "structure_rhythm_analysis", "全程一个机位也可以，但要靠字幕分段和例子把注意力托住", "ANALYSIS_RULE", ["structure-rule-density-scene-change-v1"], ["structure-bad-case-static-talking-v1"], [], "SEMANTIC", "HARD", "INTRA_SKILL"),
    ("v03-structure-005", "structure_rhythm_analysis", "同一个画面同一个语速讲到底，也没有字幕或例子推进", "BAD_CASE", ["structure-bad-case-static-talking-v1"], ["structure-rule-density-scene-change-v1"], [], "MIXED", "MEDIUM", "INTRA_SKILL"),
    ("v03-structure-006", "structure_rhythm_analysis", "用第一点第二点第三点和屏幕小标题让观众知道讲到哪了", "GOOD_CASE", ["structure-good-case-rhythm-marker-v1"], ["value-good-case-step-by-step-v1"], [], "EXACT", "EASY", "CROSS_SKILL"),
    ("v03-structure-007", "structure_rhythm_analysis", "故事开头收益不明显，但人物冲突一直在升级，所以不一定要立刻收束", "ANALYSIS_RULE", ["structure-rule-slow-burn-exception-v1"], ["hook-rule-avoid-late-payoff-v1"], [], "SEMANTIC", "HARD", "CROSS_SKILL"),
    ("v03-structure-008", "structure_rhythm_analysis", "先展示改变前，再讲怎么变，最后回到改变后的状态", "STRUCTURE_PATTERN", ["structure-pattern-contrast-before-after-v1"], ["value-rule-before-after-outcome-v1"], [], "MIXED", "HARD", "CROSS_SKILL"),
    ("v03-structure-009", "structure_rhythm_analysis", "上一句还在讲痛点，下一句突然跳到购买链接，中间没有过渡", "BAD_CASE", ["structure-bad-case-topic-jump-v1"], ["value-bad-case-scattered-benefits-v1"], [], "SEMANTIC", "MEDIUM", "CROSS_SKILL"),
    ("v03-structure-010", "structure_rhythm_analysis", "中段反复解释同一句话，没有新例子、反转或步骤往前推", "ANALYSIS_RULE", ["structure-rule-midpoint-retention-v1"], ["value-rule-specificity-v1"], [], "MIXED", "HARD", "CROSS_SKILL"),
    ("v03-structure-011", "structure_rhythm_analysis", "用一个客户案例带着解释概念，让抽象说法更容易跟上", "GOOD_CASE", ["structure-good-case-example-driven-v1"], ["value-good-case-proof-before-claim-v1"], [], "SEMANTIC", "MEDIUM", "CROSS_SKILL"),
    ("v03-structure-012", "structure_rhythm_analysis", "开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进", "STRUCTURE_PATTERN", ["structure-pattern-problem-expand-close-v1"], ["value-pattern-actionable-advice-v1"], [], "SEMANTIC", "MEDIUM", "CROSS_SKILL"),
    ("v03-structure-013", "structure_rhythm_analysis", "视频有五个技巧，但没有编号和转场词，观众不知道进度", "GOOD_CASE", ["structure-good-case-rhythm-marker-v1", "structure-pattern-topic-list-v1"], [], ["value-good-case-step-by-step-v1"], "MIXED", "ADVERSARIAL", "INTRA_SKILL"),
    ("v03-structure-014", "structure_rhythm_analysis", "画面变化很多，但信息只是重复口号，没有真正向下一段推进", "ANALYSIS_RULE", ["structure-rule-midpoint-retention-v1"], ["structure-rule-density-scene-change-v1"], [], "SEMANTIC", "ADVERSARIAL", "INTRA_SKILL"),
    ("v03-structure-015", "structure_rhythm_analysis", "前后对比是为了安排讲述顺序，不是为了证明产品一定有效", "STRUCTURE_PATTERN", ["structure-pattern-contrast-before-after-v1"], ["value-rule-before-after-outcome-v1"], [], "SEMANTIC", "EASY", "CROSS_SKILL"),
    ("v03-structure-016", "structure_rhythm_analysis", "静态口播问题不是不能用同一镜头，而是没有任何补偿性的段落变化", "BAD_CASE", ["structure-bad-case-static-talking-v1", "structure-rule-density-scene-change-v1"], [], [], "MIXED", "EASY", "INTRA_SKILL"),
    ("v03-structure-017", "structure_rhythm_analysis", "第一段钩子很好，但第二段没有接上承诺，像换了一个话题", "ANALYSIS_RULE", ["structure-rule-opening-transition-v1", "structure-bad-case-topic-jump-v1"], ["hook-rule-first-three-seconds-v1"], [], "MIXED", "ADVERSARIAL", "MIXED"),
    ("v03-structure-018", "structure_rhythm_analysis", "这个视频不是缺收益，而是从背景到卖点的段落顺序让人跟不上", "BAD_CASE", ["structure-bad-case-topic-jump-v1"], ["value-bad-case-scattered-benefits-v1"], [], "SEMANTIC", "HARD", "CROSS_SKILL"),
    ("v03-structure-019", "structure_rhythm_analysis", "慢热故事可以成立的关键，是前半段一直有关系张力在推着走", "ANALYSIS_RULE", ["structure-rule-slow-burn-exception-v1"], ["hook-pattern-curiosity-gap-v1"], ["hook-rule-avoid-late-payoff-v1"], "SEMANTIC", "MEDIUM", "MIXED"),
    ("v03-structure-020", "structure_rhythm_analysis", "讲理论时穿插一个真实场景，是为了把段落解释清楚，不是拿它当成交证明", "GOOD_CASE", ["structure-good-case-example-driven-v1"], ["value-good-case-proof-before-claim-v1"], [], "MIXED", "ADVERSARIAL", "CROSS_SKILL"),
    # value_delivery_analysis: 20
    ("v03-value-001", "value_delivery_analysis", "观众看完能得到什么结果、适合谁、在哪个场景用，都需要说清楚", "VALUE_DELIVERY_PATTERN", ["value-pattern-audience-outcome-v1"], ["hook-pattern-pain-benefit-v2"], [], "EXACT", "EASY", "CROSS_SKILL"),
    ("v03-value-002", "value_delivery_analysis", "不是只说方法好，而是说明通勤、带娃、租房这种场景里怎么解决问题", "VALUE_DELIVERY_PATTERN", ["value-pattern-use-scenario-v1"], ["hook-pattern-target-audience-v1"], [], "SEMANTIC", "MEDIUM", "CROSS_SKILL"),
    ("v03-value-003", "value_delivery_analysis", "讲完问题后要让用户知道下一步怎么检查或尝试", "VALUE_DELIVERY_PATTERN", ["value-pattern-actionable-advice-v1"], ["value-rule-call-to-action-fit-v1"], ["structure-pattern-problem-expand-close-v1"], "MIXED", "HARD", "MIXED"),
    ("v03-value-004", "value_delivery_analysis", "“更省事”太空，需要换成具体省几步、少花多少时间或体验变化", "ANALYSIS_RULE", ["value-rule-specificity-v1"], ["structure-rule-midpoint-retention-v1"], [], "EXACT", "EASY", "CROSS_SKILL"),
    ("v03-value-005", "value_delivery_analysis", "整条都在讲配置参数，没有把参数翻译成用户能感受到的好处", "BAD_CASE", ["value-bad-case-feature-without-benefit-v1"], ["hook-bad-case-feature-first-v1"], [], "MIXED", "HARD", "CROSS_SKILL"),
    ("v03-value-006", "value_delivery_analysis", "文案反复说很好用很值得，但没有对象、场景、结果或证据", "BAD_CASE", ["value-bad-case-vague-claim-v1"], ["hook-bad-case-empty-suspense-v1"], [], "SEMANTIC", "MEDIUM", "CROSS_SKILL"),
    ("v03-value-007", "value_delivery_analysis", "先放用户反馈和对比数据，再说这个方案更可信", "GOOD_CASE", ["value-good-case-proof-before-claim-v1"], ["hook-good-case-visual-proof-v1"], ["structure-good-case-example-driven-v1"], "MIXED", "HARD", "MIXED"),
    ("v03-value-008", "value_delivery_analysis", "把清洁步骤拆成先喷、等三分钟、再擦，用户能直接照做", "GOOD_CASE", ["value-good-case-step-by-step-v1"], ["structure-good-case-rhythm-marker-v1"], [], "EXACT", "EASY", "CROSS_SKILL"),
    ("v03-value-009", "value_delivery_analysis", "前面是避坑科普，结尾却突然让人直接下单，动作和价值承诺不匹配", "ANALYSIS_RULE", ["value-rule-call-to-action-fit-v1"], ["value-pattern-actionable-advice-v1"], [], "SEMANTIC", "HARD", "INTRA_SKILL"),
    ("v03-value-010", "value_delivery_analysis", "省钱、省心、变好看都提了，但没有一个主结果贯穿全片", "BAD_CASE", ["value-bad-case-scattered-benefits-v1"], ["structure-bad-case-topic-jump-v1"], [], "MIXED", "MEDIUM", "CROSS_SKILL"),
    ("v03-value-011", "value_delivery_analysis", "用使用前后的状态变化说明观众收益，而不是只按时间顺序讲过程", "ANALYSIS_RULE", ["value-rule-before-after-outcome-v1"], ["structure-pattern-contrast-before-after-v1"], [], "SEMANTIC", "HARD", "CROSS_SKILL"),
    ("v03-value-012", "value_delivery_analysis", "开头有痛点，但整条视频没有回答这个人最后能获得什么改变", "VALUE_DELIVERY_PATTERN", ["value-pattern-audience-outcome-v1"], ["hook-pattern-pain-benefit-v2"], [], "MIXED", "HARD", "CROSS_SKILL"),
    ("v03-value-013", "value_delivery_analysis", "场景是厨房油污，不是泛泛说产品适合所有家庭", "VALUE_DELIVERY_PATTERN", ["value-pattern-use-scenario-v1"], ["value-rule-specificity-v1"], [], "SEMANTIC", "MEDIUM", "INTRA_SKILL"),
    ("v03-value-014", "value_delivery_analysis", "最后让用户收藏检查清单，比突然引导购买更符合这条内容", "ANALYSIS_RULE", ["value-rule-call-to-action-fit-v1"], ["value-pattern-actionable-advice-v1"], [], "MIXED", "EASY", "INTRA_SKILL"),
    ("v03-value-015", "value_delivery_analysis", "案例不是为了让结构更顺，而是为了先证明结论可信", "GOOD_CASE", ["value-good-case-proof-before-claim-v1"], ["structure-good-case-example-driven-v1"], [], "SEMANTIC", "ADVERSARIAL", "CROSS_SKILL"),
    ("v03-value-016", "value_delivery_analysis", "讲了三个步骤但每步只是标题，没有让用户知道怎么执行", "VALUE_DELIVERY_PATTERN", ["value-pattern-actionable-advice-v1", "value-good-case-step-by-step-v1"], ["structure-good-case-rhythm-marker-v1"], [], "MIXED", "ADVERSARIAL", "MIXED"),
    ("v03-value-017", "value_delivery_analysis", "参数出现在开头不一定错，问题是整条都没把功能转成收益", "BAD_CASE", ["value-bad-case-feature-without-benefit-v1"], ["hook-bad-case-feature-first-v1"], [], "SEMANTIC", "EASY", "CROSS_SKILL"),
    ("v03-value-018", "value_delivery_analysis", "中段不是没推进，而是每个收益都停留在好用、划算这种空话", "ANALYSIS_RULE", ["value-rule-specificity-v1", "value-bad-case-vague-claim-v1"], [], ["structure-rule-midpoint-retention-v1"], "MIXED", "ADVERSARIAL", "MIXED"),
    ("v03-value-019", "value_delivery_analysis", "前后对比图如果服务于证明省时效果，应归到价值可信而非段落顺序", "ANALYSIS_RULE", ["value-rule-before-after-outcome-v1", "value-good-case-proof-before-claim-v1"], ["structure-pattern-contrast-before-after-v1"], [], "MIXED", "ADVERSARIAL", "CROSS_SKILL"),
    ("v03-value-020", "value_delivery_analysis", "卖点到处都是，用户最后记不住主线，也不知道主要改善什么", "BAD_CASE", ["value-bad-case-scattered-benefits-v1"], ["structure-bad-case-topic-jump-v1"], ["value-pattern-audience-outcome-v1"], "SEMANTIC", "MEDIUM", "MIXED"),
  ]
  cases = [
    GoldenQueryCase(
      query_id=query_id,
      skill_code=skill_code,
      query=query,
      knowledge_type=knowledge_type,
      expected_knowledge_ids=expected_ids,
      acceptable_knowledge_ids=acceptable_ids,
      hard_negative_knowledge_ids=hard_negative_ids,
      match_type=match_type,  # type: ignore[arg-type]
      difficulty=difficulty,  # type: ignore[arg-type]
      hard_negative_scope=hard_negative_scope,  # type: ignore[arg-type]
      annotation_status="PENDING_REVIEW",
      notes="v0.3 generated candidate. Human review required before formal benchmark use.",
    )
    for (
      query_id,
      skill_code,
      query,
      knowledge_type,
      expected_ids,
      hard_negative_ids,
      acceptable_ids,
      match_type,
      difficulty,
      hard_negative_scope,
    ) in rows
  ]
  _assert_expected_ids_exist(cases, corpus=load_benchmark_corpus("v0.3"))
  _assert_expected_ids_exist(cases, corpus=load_benchmark_corpus("v0.3"), id_field="acceptable_knowledge_ids")
  _assert_expected_ids_exist(cases, corpus=load_benchmark_corpus("v0.3"), id_field="hard_negative_knowledge_ids")
  return cases


def unlabeled_golden_query_template() -> list[GoldenQueryCase]:
  return [
    _case("manual-hook-category-template-v1", "hook_analysis", "请填写真实业务类目下的钩子问题", "DOMAIN_KNOWLEDGE", "", "SEMANTIC", "PENDING_REVIEW", "Human label required."),
    _case("manual-structure-category-template-v1", "structure_rhythm_analysis", "请填写真实业务类目下的结构节奏问题", "DOMAIN_KNOWLEDGE", "", "SEMANTIC", "PENDING_REVIEW", "Human label required."),
    _case("manual-value-category-template-v1", "value_delivery_analysis", "请填写真实业务类目下的价值传递问题", "DOMAIN_KNOWLEDGE", "", "SEMANTIC", "PENDING_REVIEW", "Human label required."),
  ]


def load_query_dataset(path: str | Path) -> list[GoldenQueryCase]:
  source = Path(path)
  if source.suffix.lower() == ".jsonl":
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
  else:
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("cases", payload if isinstance(payload, list) else [])
  return [_case_from_mapping(row) for row in rows]


def split_golden_dataset_v05(
  cases: list[GoldenQueryCase],
  *,
  seed: int = 20260911,
  dev_size: int = 40,
) -> tuple[list[GoldenQueryCase], list[GoldenQueryCase]]:
  groups: dict[tuple[str, str, str], list[GoldenQueryCase]] = {}
  for case in cases:
    groups.setdefault((case.skill_code, str(case.difficulty), case.match_type), []).append(case)

  rng = random.Random(seed)
  shuffled_groups: dict[tuple[str, str, str], list[GoldenQueryCase]] = {}
  allocations: dict[tuple[str, str, str], int] = {}
  remainders: list[tuple[float, tuple[str, str, str]]] = []
  total = len(cases)
  for key, group_cases in groups.items():
    ordered = list(group_cases)
    rng.shuffle(ordered)
    shuffled_groups[key] = ordered
    exact = len(group_cases) * dev_size / total
    allocations[key] = int(exact)
    remainders.append((exact - allocations[key], key))

  remaining = dev_size - sum(allocations.values())
  for _, key in sorted(remainders, reverse=True)[:remaining]:
    allocations[key] += 1

  dev: list[GoldenQueryCase] = []
  test: list[GoldenQueryCase] = []
  for key in sorted(shuffled_groups):
    cutoff = allocations[key]
    dev.extend(shuffled_groups[key][:cutoff])
    test.extend(shuffled_groups[key][cutoff:])
  dev = sorted(dev, key=lambda case: case.query_id)
  test = sorted(test, key=lambda case: case.query_id)
  return dev, test


def save_v05_dev_test_split(
  input_path: str | Path,
  output_dir: str | Path,
  *,
  seed: int = 20260911,
) -> tuple[Path, Path]:
  cases = load_query_dataset(input_path)
  dev, test = split_golden_dataset_v05(cases, seed=seed)
  output = Path(output_dir)
  output.mkdir(parents=True, exist_ok=True)
  dev_path = output / "retrieval_golden_dev.v0.5.json"
  test_path = output / "retrieval_golden_test.v0.5.json"
  _write_dataset_payload(dev_path, "video-diagnosis-rag-dev-v0.5", dev, seed=seed)
  _write_dataset_payload(test_path, "video-diagnosis-rag-test-v0.5", test, seed=seed)
  return dev_path, test_path


def evaluate_ranked_refs(expected_refs: list[str], ranked_refs: list[str]) -> dict[str, float]:
  expected = set(expected_refs)
  if not expected:
    return {"recallAt1": 0.0, "recallAt3": 0.0, "recallAt5": 0.0, "recallAt10": 0.0, "mrr": 0.0}
  return {
    "recallAt1": _recall_at(expected, ranked_refs, 1),
    "recallAt3": _recall_at(expected, ranked_refs, 3),
    "recallAt5": _recall_at(expected, ranked_refs, 5),
    "recallAt10": _recall_at(expected, ranked_refs, 10),
    "mrr": _mrr(expected, ranked_refs),
  }


def aggregate_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
  if not rows:
    return _empty_retrieval_metrics()
  latencies = [row.get("latencyMs", 0.0) for row in rows]
  embedding_latencies = [row.get("embeddingGenerationLatencyMs", 0.0) for row in rows]
  ranking_latencies = [row.get("retrievalRankingLatencyMs", 0.0) for row in rows]
  end_to_end_latencies = [row.get("endToEndLatencyMs", row.get("latencyMs", 0.0)) for row in rows]
  return {
    "queryCount": float(len(rows)),
    "recallAt1": sum(row.get("recallAt1", 0.0) for row in rows) / len(rows),
    "recallAt3": sum(row.get("recallAt3", 0.0) for row in rows) / len(rows),
    "recallAt5": sum(row.get("recallAt5", 0.0) for row in rows) / len(rows),
    "recallAt10": sum(row.get("recallAt10", 0.0) for row in rows) / len(rows),
    "mrr": sum(row.get("mrr", 0.0) for row in rows) / len(rows),
    "acceptableHitAt5": sum(row.get("acceptableHitAt5", 0.0) for row in rows) / len(rows),
    "hardNegativeAboveExpectedRate": (
      sum(row.get("hardNegativeAboveExpected", 0.0) for row in rows)
      / max(1, sum(row.get("hardNegativeEvaluated", 0.0) for row in rows))
    ),
    "hardNegativeFailureCount": sum(row.get("hardNegativeAboveExpected", 0.0) for row in rows),
    "hardNegativeEvaluatedQueryCount": sum(row.get("hardNegativeEvaluated", 0.0) for row in rows),
    "avgLatencyMs": sum(latencies) / len(latencies),
    "embeddingGenerationLatencyMs": sum(embedding_latencies) / len(embedding_latencies),
    "retrievalRankingLatencyMs": sum(ranking_latencies) / len(ranking_latencies),
    "endToEndLatencyMs": sum(end_to_end_latencies) / len(end_to_end_latencies),
    "p50LatencyMs": _percentile(latencies, 50),
    "p95LatencyMs": _percentile(latencies, 95),
  }


def candidate_pool_stats(results: list[RetrievalCaseResult]) -> dict[str, float]:
  if not results:
    return {"candidatePoolMin": 0.0, "candidatePoolMedian": 0.0, "candidatePoolMax": 0.0}
  sizes_by_query = {
    result.query_id: result.candidate_pool_size
    for result in results
  }
  sizes = list(sizes_by_query.values())
  return {
    "candidatePoolMin": float(min(sizes)),
    "candidatePoolMedian": _percentile([float(size) for size in sizes], 50),
    "candidatePoolMax": float(max(sizes)),
  }


def hard_negative_above_expected(
  *,
  expected_knowledge_ids: list[str],
  hard_negative_knowledge_ids: list[str],
  ranked_knowledge_ids: list[str],
) -> bool:
  if not hard_negative_knowledge_ids:
    return False
  rank_by_id = {knowledge_id: index + 1 for index, knowledge_id in enumerate(ranked_knowledge_ids)}
  expected_ranks = [
    rank_by_id[knowledge_id]
    for knowledge_id in expected_knowledge_ids
    if knowledge_id in rank_by_id
  ]
  hard_negative_ranks = [
    rank_by_id[knowledge_id]
    for knowledge_id in hard_negative_knowledge_ids
    if knowledge_id in rank_by_id
  ]
  if not hard_negative_ranks:
    return False
  best_expected_rank = min(expected_ranks) if expected_ranks else float("inf")
  return min(hard_negative_ranks) < best_expected_rank


def build_miss_analysis(report: RetrievalExperimentReport, cases: list[GoldenQueryCase]) -> dict[str, Any]:
  by_query: dict[str, dict[str, Any]] = {}
  case_by_id = {case.query_id: case for case in cases}
  for row in report.cases:
    by_query.setdefault(row["query_id"], {})[row["strategy"]] = row

  analysis_rows = []
  for query_id, strategy_rows in sorted(by_query.items()):
    case = case_by_id[query_id]
    strategy_summary = {
      "BM25": _strategy_miss_summary(strategy_rows.get("BM25_ONLY"), case),
      "Embedding": _strategy_miss_summary(strategy_rows.get("EMBEDDING_ONLY"), case),
      "Hybrid": _strategy_miss_summary(strategy_rows.get("HYBRID_BM25_EMBEDDING_RRF"), case),
      "Rerank": _strategy_miss_summary(strategy_rows.get("HYBRID_BM25_EMBEDDING_RRF_RERANK"), case),
    }
    highest_hard_negative_rank = _highest_hard_negative_rank(strategy_rows, case)
    hard_negative_failure = any(
      bool(row.get("hard_negative_above_expected"))
      for row in strategy_rows.values()
    )
    analysis_rows.append({
      "queryId": case.query_id,
      "skillCode": case.skill_code,
      "difficulty": case.difficulty,
      "matchType": case.match_type,
      "query": case.query,
      "expectedKnowledgeIds": case.expected_knowledge_ids,
      "acceptableKnowledgeIds": case.acceptable_knowledge_ids,
      "hardNegativeKnowledgeIds": case.hard_negative_knowledge_ids,
      "BM25": strategy_summary["BM25"],
      "Embedding": strategy_summary["Embedding"],
      "Hybrid": strategy_summary["Hybrid"],
      "Rerank": strategy_summary["Rerank"],
      "highestHardNegativeRank": highest_hard_negative_rank,
      "hardNegativeAboveExpected": hard_negative_failure,
      "candidatePoolSize": _candidate_pool_size(strategy_rows),
      "errorType": classify_error_type(case, strategy_rows, hard_negative_failure),
    })
  return {
    "datasetVersion": report.dataset_version,
    "corpusVersion": report.corpus_version,
    "benchmarkMode": report.benchmark_mode,
    "rows": analysis_rows,
    "summary": miss_analysis_summary(analysis_rows),
  }


def classify_error_type(
  case: GoldenQueryCase,
  strategy_rows: dict[str, dict[str, Any]],
  hard_negative_failure: bool,
) -> str:
  hybrid = strategy_rows.get("HYBRID_BM25_EMBEDDING_RRF")
  rerank = strategy_rows.get("HYBRID_BM25_EMBEDDING_RRF_RERANK")
  if rerank and hybrid and _rank_worse(
    _best_rank(rerank["ranked_knowledge_ids"], case.expected_knowledge_ids),
    _best_rank(hybrid["ranked_knowledge_ids"], case.expected_knowledge_ids),
  ):
    return "RERANK_INVERSION"
  if hard_negative_failure:
    return "HARD_NEGATIVE_CONFUSION"
  if len(case.expected_knowledge_ids) > 1:
    return "MULTI_LABEL_AMBIGUITY"
  if case.hard_negative_scope == "CROSS_SKILL":
    return "CROSS_SKILL_CONTAMINATION"
  if case.match_type == "SEMANTIC":
    return "SEMANTIC_BOUNDARY_CONFUSION"
  if case.match_type == "EXACT":
    return "LEXICAL_MISMATCH"
  return "UNKNOWN"


def miss_analysis_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
  from collections import Counter

  confused_pairs: Counter[str] = Counter()
  skill_misses: Counter[str] = Counter()
  error_types: Counter[str] = Counter()
  hard_negative_counts: Counter[str] = Counter()
  suppressed_expected: Counter[str] = Counter()
  for row in rows:
    is_miss = any(
      row[strategy]["expectedBestRank"] is None or row[strategy]["expectedBestRank"] > 5
      for strategy in ["BM25", "Embedding", "Hybrid", "Rerank"]
      if row[strategy]
    )
    if is_miss:
      skill_misses[row["skillCode"]] += 1
    error_types[row["errorType"]] += 1
    if row["hardNegativeAboveExpected"]:
      for hard_id in row["hardNegativeKnowledgeIds"]:
        hard_negative_counts[hard_id] += 1
      for expected_id in row["expectedKnowledgeIds"]:
        for hard_id in row["hardNegativeKnowledgeIds"]:
          confused_pairs[f"{expected_id} -> {hard_id}"] += 1
    for expected_id in row["expectedKnowledgeIds"]:
      if any(
        row[strategy]["expectedBestRank"] is None or row[strategy]["expectedBestRank"] > 1
        for strategy in ["BM25", "Embedding", "Hybrid", "Rerank"]
        if row[strategy]
      ):
        suppressed_expected[expected_id] += 1
  return {
    "topRecurringConfusedKnowledgePairs": confused_pairs.most_common(10),
    "missCountBySkillCode": dict(skill_misses),
    "missCountByErrorType": dict(error_types),
    "hardNegativeFailureKnowledgeIds": hard_negative_counts.most_common(10),
    "suppressedExpectedKnowledgeIds": suppressed_expected.most_common(10),
  }


def _strategy_miss_summary(row: dict[str, Any] | None, case: GoldenQueryCase) -> dict[str, Any] | None:
  if not row:
    return None
  ranked = list(row.get("ranked_knowledge_ids") or [])
  return {
    "expectedBestRank": _best_rank(ranked, case.expected_knowledge_ids),
    "top5KnowledgeIds": ranked[:5],
  }


def _best_rank(ranked_knowledge_ids: list[str], expected_ids: list[str]) -> int | None:
  ranks = [
    ranked_knowledge_ids.index(expected_id) + 1
    for expected_id in expected_ids
    if expected_id in ranked_knowledge_ids
  ]
  return min(ranks) if ranks else None


def _rank_worse(candidate_rank: int | None, baseline_rank: int | None) -> bool:
  if candidate_rank is None and baseline_rank is None:
    return False
  if candidate_rank is None:
    return True
  if baseline_rank is None:
    return False
  return candidate_rank > baseline_rank


def _highest_hard_negative_rank(
  strategy_rows: dict[str, dict[str, Any]],
  case: GoldenQueryCase,
) -> int | None:
  ranks = []
  for row in strategy_rows.values():
    ranked = list(row.get("ranked_knowledge_ids") or [])
    ranks.extend(
      ranked.index(hard_id) + 1
      for hard_id in case.hard_negative_knowledge_ids
      if hard_id in ranked
    )
  return min(ranks) if ranks else None


def _candidate_pool_size(strategy_rows: dict[str, dict[str, Any]]) -> int:
  for row in strategy_rows.values():
    if row.get("candidate_pool_size") is not None:
      return int(row["candidate_pool_size"])
  return 0


class RetrievalBenchmarkRunner:
  def __init__(
    self,
    corpus: list[KnowledgeEvidence] | None = None,
    config: RetrievalRunConfig | None = None,
    embedding_provider: EmbeddingProvider | None = None,
  ) -> None:
    self.corpus = corpus or default_video_diagnosis_corpus()
    self.config = config or RetrievalRunConfig()
    self.embedding_provider = embedding_provider
    self.retriever = BenchmarkKnowledgeRetriever(
      self.corpus,
      self.config.benchmark_mode,
      embedding_provider=embedding_provider,
      use_retrieval_text=self.config.use_retrieval_text,
      weighted_rrf_config=WeightedRrfConfig(
        bm25_weight=self.config.bm25_weight,
        embedding_weight=self.config.embedding_weight,
        rrf_k=self.config.rrf_k,
      ),
    )

  def run(
    self,
    dataset: list[GoldenQueryCase] | None = None,
    strategies: list[RetrievalStrategy] | None = None,
    *,
    verified_only: bool | None = None,
  ) -> RetrievalExperimentReport:
    started_at = _utc_timestamp()
    dataset = dataset or formal_candidate_query_dataset()
    strategies = strategies or DEFAULT_STRATEGIES
    use_verified_only = self.config.verified_only if verified_only is None else verified_only
    cases = [
      case
      for case in dataset
      if case.expected_knowledge_ids and (case.annotation_status == "VERIFIED" or not use_verified_only)
    ]
    case_results = [
      self._run_case(case, strategy)
      for strategy in strategies
      for case in cases
    ]
    candidate_pool = candidate_pool_stats(case_results)
    if case_results and self.config.benchmark_mode != "RUNTIME" and candidate_pool["candidatePoolMedian"] <= 1:
      raise ValueError(
        f"Invalid benchmark candidate pool for {self.config.benchmark_mode}: "
        f"median={candidate_pool['candidatePoolMedian']}"
      )

    report = RetrievalExperimentReport(
      dataset_version=self.config.dataset_version,
      corpus_version=self.config.corpus_version,
      verified_sample_count=sum(1 for case in cases if case.annotation_status == "VERIFIED"),
      corpus_size=len(self.corpus),
      benchmark_mode=self.config.benchmark_mode,
      candidate_pool=candidate_pool,
      configuration={
        "strategies": strategies,
        "top_k": self.config.top_k,
        "repeat_count": self.config.repeat_count,
        "verified_only": use_verified_only,
        "benchmarkMode": self.config.benchmark_mode,
        "corpusVersion": self.config.corpus_version,
        "useRetrievalText": self.config.use_retrieval_text,
        "weightedRrf": {
          "bm25Weight": self.config.bm25_weight,
          "embeddingWeight": self.config.embedding_weight,
          "rrfK": self.config.rrf_k,
        },
        "corpusEmbeddingMode": "precomputed_at_runner_init" if self.embedding_provider else "not_used",
        "queryEmbeddingCache": "enabled_per_runner",
        "embeddingLatencyIncludedInEndToEnd": True,
        "rerankEnabled": any(strategy.endswith("RERANK") for strategy in strategies),
        "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default.",
        **self.config.retriever_params.get("reportMetadata", {}),
      },
      model=self.config.model,
      embedding_provider=self._embedding_provider_name(),
      embedding_model=self._embedding_model_name(),
      embedding_dimension=self._embedding_dimension(),
      retriever_params=self.config.retriever_params,
      run_started_at=started_at,
      run_finished_at=_utc_timestamp(),
      strategies=self._aggregate_by_strategy(case_results, strategies),
      by_skill_code=self._aggregate_grouped(case_results, strategies, "skill_code"),
      by_difficulty=self._aggregate_grouped(case_results, strategies, "difficulty"),
      by_match_type=self._aggregate_grouped(case_results, strategies, "match_type"),
      recall_at_5_misses=self._misses(case_results),
      cases=[asdict(item) for item in case_results],
    )
    return report

  def run_smoke(self) -> RetrievalExperimentReport:
    config = RetrievalRunConfig(
      dataset_version=SMOKE_DATASET_VERSION,
      corpus_version=self.config.corpus_version,
      benchmark_mode=self.config.benchmark_mode,
      model=self.config.model,
      top_k=self.config.top_k,
      repeat_count=self.config.repeat_count,
      verified_only=False,
      retriever_params=self.config.retriever_params,
    )
    strategies: list[RetrievalStrategy] | None = None
    if self.embedding_provider is None:
      strategies = ["BM25_ONLY", "VECTOR_ONLY", "HYBRID_RRF", "HYBRID_RRF_RERANK"]
    return RetrievalBenchmarkRunner(self.corpus, config, self.embedding_provider).run(
      smoke_golden_query_dataset(),
      strategies=strategies,
      verified_only=False,
    )

  def write_report(self, report: RetrievalExperimentReport, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "retrieval_benchmark_report.json"
    md_path = output / "retrieval_benchmark_report.md"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_retrieval_markdown(report), encoding="utf-8")
    return json_path, md_path

  def write_miss_analysis(
    self,
    report: RetrievalExperimentReport,
    dataset: list[GoldenQueryCase],
    output_dir: str | Path,
  ) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = build_miss_analysis(report, dataset)
    json_path = output / "miss-analysis.json"
    md_path = output / "miss-analysis.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_miss_analysis_markdown(payload), encoding="utf-8")
    return json_path, md_path

  def _run_case(self, case: GoldenQueryCase, strategy: RetrievalStrategy) -> RetrievalCaseResult:
    query = KnowledgeQuery(
      query_text=case.query,
      skill_code=case.skill_code,
      knowledge_type=case.knowledge_type,
      category=case.category,
      top_k=self.config.top_k,
    )
    final_items: list[KnowledgeEvidence] = []
    latency_runs: list[float] = []
    embedding_latency_runs: list[float] = []
    cache_hit_runs: list[bool] = []
    candidate_pool_size = self.retriever.candidate_pool_size(query)
    for _ in range(max(1, self.config.repeat_count)):
      started = time.perf_counter()
      final_items = self._search(query, strategy)
      elapsed_ms = (time.perf_counter() - started) * 1000
      latency_runs.append(elapsed_ms)
      embedding_latency_runs.append(self.retriever.last_embedding_generation_latency_ms)
      cache_hit_runs.append(self.retriever.last_embedding_cache_hit)
    ranked_ids = [item.id for item in final_items[: self.config.top_k]]
    metrics = evaluate_ranked_refs(
      [f"KNOWLEDGE:{item}" for item in case.expected_knowledge_ids],
      [f"KNOWLEDGE:{item}" for item in ranked_ids],
    )
    hard_negative_failure = hard_negative_above_expected(
      expected_knowledge_ids=case.expected_knowledge_ids,
      hard_negative_knowledge_ids=case.hard_negative_knowledge_ids,
      ranked_knowledge_ids=ranked_ids,
    )
    return RetrievalCaseResult(
      query_id=case.query_id,
      strategy=strategy,
      benchmark_mode=self.config.benchmark_mode,
      query=case.query,
      skill_code=case.skill_code,
      difficulty=case.difficulty,
      match_type=case.match_type,
      knowledge_type=case.knowledge_type,
      expected_knowledge_ids=case.expected_knowledge_ids,
      acceptable_knowledge_ids=case.acceptable_knowledge_ids,
      hard_negative_knowledge_ids=case.hard_negative_knowledge_ids,
      actual_top_5=[{"knowledgeId": item.id, "score": item.score} for item in final_items[:5]],
      ranked_knowledge_ids=ranked_ids,
      candidate_pool_size=candidate_pool_size,
      recall_at_1=metrics["recallAt1"],
      recall_at_3=metrics["recallAt3"],
      recall_at_5=metrics["recallAt5"],
      recall_at_10=metrics["recallAt10"],
      mrr=metrics["mrr"],
      acceptable_hit_at_5=1.0 if set(case.acceptable_knowledge_ids) & set(ranked_ids[:5]) else 0.0,
      hard_negative_above_expected=hard_negative_failure,
      latency_runs_ms=latency_runs,
      embedding_generation_latency_ms=sum(embedding_latency_runs) / len(embedding_latency_runs),
      retrieval_ranking_latency_ms=(
        sum(max(0.0, total - embedding) for total, embedding in zip(latency_runs, embedding_latency_runs))
        / len(latency_runs)
      ),
      end_to_end_latency_ms=sum(latency_runs) / len(latency_runs),
      embedding_cache_hit=all(cache_hit_runs) if cache_hit_runs else False,
      embedding_latency_included_in_end_to_end=strategy != "BM25_ONLY",
      avg_latency_ms=sum(latency_runs) / len(latency_runs),
      p50_latency_ms=_percentile(latency_runs, 50),
      p95_latency_ms=_percentile(latency_runs, 95),
    )

  def _search(self, query: KnowledgeQuery, strategy: RetrievalStrategy) -> list[KnowledgeEvidence]:
    if strategy == "BM25_ONLY":
      self.retriever.last_embedding_generation_latency_ms = 0.0
      self.retriever.last_embedding_cache_hit = False
      return self.retriever.search_bm25(query, limit=self.config.top_k)
    if strategy == "EMBEDDING_ONLY":
      return self.retriever.search_embedding(query, limit=self.config.top_k)
    if strategy == "HYBRID_BM25_EMBEDDING_RRF":
      return self.retriever.search_hybrid_rrf(query, final_top_k=self.config.top_k)
    if strategy == "HYBRID_BM25_EMBEDDING_RRF_05_05":
      return self._search_with_weighted_rrf(query, bm25_weight=0.5, embedding_weight=0.5)
    if strategy == "FINAL_WEIGHTED_HYBRID":
      return self._search_with_weighted_rrf(query, bm25_weight=0.7, embedding_weight=0.3)
    if strategy == "HYBRID_BM25_EMBEDDING_RRF_RERANK":
      return self.retriever.retrieve(query)
    if strategy == "VECTOR_ONLY":
      self.retriever.last_embedding_generation_latency_ms = 0.0
      self.retriever.last_embedding_cache_hit = False
      return self.retriever.search_vector(query, limit=self.config.top_k)
    if strategy == "HYBRID_RRF":
      return self._legacy_hybrid_rrf(query, final_top_k=self.config.top_k)
    if strategy == "HYBRID_RRF_RERANK":
      return self.retriever._scorer.rerank(query.query_text, self._legacy_hybrid_rrf(query, final_top_k=30))[: max(1, query.top_k)]
    raise ValueError(f"Unsupported retrieval strategy: {strategy}")

  def _search_with_weighted_rrf(
    self,
    query: KnowledgeQuery,
    *,
    bm25_weight: float,
    embedding_weight: float,
  ) -> list[KnowledgeEvidence]:
    previous = self.retriever._weighted_rrf_config
    self.retriever._weighted_rrf_config = WeightedRrfConfig(
      bm25_weight=bm25_weight,
      embedding_weight=embedding_weight,
      rrf_k=60,
    )
    try:
      return self.retriever.search_hybrid_rrf(query, final_top_k=self.config.top_k)
    finally:
      self.retriever._weighted_rrf_config = previous

  def _legacy_hybrid_rrf(self, query: KnowledgeQuery, *, final_top_k: int) -> list[KnowledgeEvidence]:
    from dataclasses import replace

    from agent_service.retrieval.rrf import reciprocal_rank_fusion

    bm25 = self.retriever.search_bm25(query, limit=30)
    vector = self.retriever.search_vector(query, limit=30)
    fused = reciprocal_rank_fusion([vector, bm25], lambda item: item.id, final_top_k=final_top_k)
    return [replace(item, score=score) for item, score in fused]

  def _embedding_provider_name(self) -> str:
    return self.embedding_provider.provider_name if self.embedding_provider else self.config.embedding_provider

  def _embedding_model_name(self) -> str:
    return self.embedding_provider.model_name if self.embedding_provider else self.config.embedding_model

  def _embedding_dimension(self) -> int:
    return self.embedding_provider.dimension if self.embedding_provider else 0

  def _aggregate_by_strategy(
    self,
    results: list[RetrievalCaseResult],
    strategies: list[RetrievalStrategy],
  ) -> dict[str, dict[str, float]]:
    return {
      strategy: aggregate_metrics([
        _metrics_row(result)
        for result in results
        if result.strategy == strategy
      ])
      for strategy in strategies
    }

  def _aggregate_grouped(
    self,
    results: list[RetrievalCaseResult],
    strategies: list[RetrievalStrategy],
    field_name: Literal["skill_code", "difficulty", "match_type"],
  ) -> dict[str, dict[str, dict[str, float]]]:
    groups = sorted({str(getattr(result, field_name)) for result in results})
    return {
      group: {
        strategy: aggregate_metrics([
          _metrics_row(result)
          for result in results
          if result.strategy == strategy and str(getattr(result, field_name)) == group
        ])
        for strategy in strategies
      }
      for group in groups
    }

  def _misses(self, results: list[RetrievalCaseResult]) -> list[dict[str, Any]]:
    return [
      {
        "queryId": result.query_id,
        "strategy": result.strategy,
        "query": result.query,
        "skillCode": result.skill_code,
        "difficulty": result.difficulty,
        "expectedKnowledgeIds": result.expected_knowledge_ids,
        "hardNegativeKnowledgeIds": result.hard_negative_knowledge_ids,
        "actualTop5": result.actual_top_5,
      }
      for result in results
      if result.recall_at_5 < 1.0
    ]


def render_retrieval_markdown(report: RetrievalExperimentReport) -> str:
  lines = [
    "# Video Diagnosis RAG Retrieval Benchmark",
    "",
    f"- Dataset version: `{report.dataset_version}`",
    f"- Corpus version: `{report.corpus_version}`",
    f"- Verified sample count: `{report.verified_sample_count}`",
    f"- Corpus size: `{report.corpus_size}`",
    f"- Benchmark mode: `{report.benchmark_mode}`",
    f"- Candidate pool: `{json.dumps(report.candidate_pool, ensure_ascii=False)}`",
    f"- Model: `{report.model}`",
    f"- Embedding provider: `{report.embedding_provider}`",
    f"- Embedding model: `{report.embedding_model}`",
    f"- Embedding dimension: `{report.embedding_dimension}`",
    f"- Run started at: `{report.run_started_at}`",
    f"- Run finished at: `{report.run_finished_at}`",
    f"- Configuration: `{json.dumps(report.configuration, ensure_ascii=False)}`",
    f"- Retriever params: `{json.dumps(report.retriever_params, ensure_ascii=False)}`",
    "",
    "## Overall Metrics",
    "",
    "| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
  ]
  for strategy, metrics in report.strategies.items():
    lines.append(_metrics_table_row(strategy, metrics))
  lines.extend(["", "## Metrics By Skill", ""])
  lines.extend(_group_markdown(report.by_skill_code))
  lines.extend(["", "## Metrics By Difficulty", ""])
  lines.extend(_group_markdown(report.by_difficulty))
  lines.extend(["", "## Metrics By Match Type", ""])
  lines.extend(_group_markdown(report.by_match_type))
  lines.extend(["", "## Recall@5 Miss Analysis", ""])
  if not report.recall_at_5_misses:
    lines.append("- No Recall@5 misses in the evaluated VERIFIED dataset.")
  for miss in report.recall_at_5_misses:
    lines.append(
      f"- `{miss['queryId']}` `{miss['strategy']}` query={miss['query']} "
      f"expected={miss['expectedKnowledgeIds']} hardNegative={miss['hardNegativeKnowledgeIds']} "
      f"actualTop5={miss['actualTop5']}"
    )
  lines.append("")
  return "\n".join(lines)


def render_miss_analysis_markdown(payload: dict[str, Any]) -> str:
  summary = payload["summary"]
  lines = [
    "# Retrieval Miss Analysis",
    "",
    f"- Dataset version: `{payload['datasetVersion']}`",
    f"- Corpus version: `{payload['corpusVersion']}`",
    f"- Benchmark mode: `{payload['benchmarkMode']}`",
    "",
    "## Top 10 Recurring Confused Knowledge Pairs",
  ]
  lines.extend(_count_rows(summary["topRecurringConfusedKnowledgePairs"]))
  lines.extend(["", "## Miss Count By SkillCode"])
  lines.extend(_dict_rows(summary["missCountBySkillCode"]))
  lines.extend(["", "## Miss Count By ErrorType"])
  lines.extend(_dict_rows(summary["missCountByErrorType"]))
  lines.extend(["", "## Hard Negative Failure Knowledge IDs"])
  lines.extend(_count_rows(summary["hardNegativeFailureKnowledgeIds"]))
  lines.extend(["", "## Suppressed Expected Knowledge IDs"])
  lines.extend(_count_rows(summary["suppressedExpectedKnowledgeIds"]))
  lines.extend(["", "## Query Rows", ""])
  for row in payload["rows"]:
    lines.append(
      f"- `{row['queryId']}` `{row['skillCode']}` `{row['errorType']}` "
      f"expected={row['expectedKnowledgeIds']} hardNegative={row['hardNegativeKnowledgeIds']} "
      f"hybridRank={row['Hybrid']['expectedBestRank'] if row['Hybrid'] else None}"
    )
  lines.append("")
  return "\n".join(lines)


def _count_rows(rows: list[list[Any]] | list[tuple[Any, int]]) -> list[str]:
  if not rows:
    return ["- None"]
  return [f"- `{key}`: {count}" for key, count in rows]


def _dict_rows(values: dict[str, Any]) -> list[str]:
  if not values:
    return ["- None"]
  return [f"- `{key}`: {value}" for key, value in sorted(values.items())]


def save_default_datasets(output_dir: str | Path) -> tuple[Path, Path, Path]:
  output = Path(output_dir)
  output.mkdir(parents=True, exist_ok=True)
  json_path = output / "retrieval_golden_candidates.v0.2.json"
  jsonl_path = output / "retrieval_golden_candidates.v0.2.jsonl"
  agent_path = output / "agent_ablation_golden_template.json"
  cases = formal_candidate_query_dataset()
  retrieval_payload = {
    "datasetVersion": DEFAULT_DATASET_VERSION,
    "annotationPolicy": "All generated candidates are PENDING_REVIEW. Change annotationStatus to VERIFIED only after human review.",
    "cases": [_external_case_dict(item) for item in cases],
    "smokeCases": [_external_case_dict(item) for item in smoke_golden_query_dataset()],
  }
  json_path.write_text(json.dumps(retrieval_payload, ensure_ascii=False, indent=2), encoding="utf-8")
  jsonl_path.write_text(
    "\n".join(json.dumps(_external_case_dict(item), ensure_ascii=False) for item in cases) + "\n",
    encoding="utf-8",
  )
  agent_payload = {
    "datasetVersion": "video-diagnosis-agent-ablation-v0.1",
    "variants": ["VIDEO_EVIDENCE_ONLY", "RAG", "LOCAL_REACT", "EVALUATOR"],
    "cases": [asdict(item) for item in agent_golden_template()],
  }
  agent_path.write_text(json.dumps(agent_payload, ensure_ascii=False, indent=2), encoding="utf-8")
  return json_path, jsonl_path, agent_path


def save_benchmark_v03_candidate_dataset(output_dir: str | Path) -> tuple[Path, Path]:
  output = Path(output_dir)
  output.mkdir(parents=True, exist_ok=True)
  json_path = output / "retrieval_golden_candidates.v0.3.json"
  jsonl_path = output / "retrieval_golden_candidates.v0.3.jsonl"
  cases = benchmark_v03_candidate_query_dataset()
  payload = {
    "datasetVersion": "video-diagnosis-rag-candidates-v0.3",
    "corpusVersion": "v0.3",
    "annotationPolicy": "All generated candidates are PENDING_REVIEW. Change annotationStatus to VERIFIED only after human review.",
    "cases": [_external_case_dict(item) for item in cases],
  }
  json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
  jsonl_path.write_text(
    "\n".join(json.dumps(_external_case_dict(item), ensure_ascii=False) for item in cases) + "\n",
    encoding="utf-8",
  )
  return json_path, jsonl_path


def _write_dataset_payload(path: Path, dataset_version: str, cases: list[GoldenQueryCase], *, seed: int) -> None:
  payload = {
    "datasetVersion": dataset_version,
    "splitSeed": seed,
    "cases": [_external_case_dict(item) for item in cases],
  }
  path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def agent_golden_template() -> list[AgentGoldenCase]:
  return [
    AgentGoldenCase(
      id="manual-agent-case-hook-001",
      video_case_id="fill-real-video-case-id",
      golden_findings=[],
      notes="Human annotator must fill golden_findings before metrics are meaningful.",
      needs_human_label=True,
    )
  ]


def evaluate_agent_variant(
  golden_cases: list[AgentGoldenCase],
  predictions: list[AgentVariantPrediction],
  *,
  dataset_version: str,
  model: str,
  config: dict[str, Any] | None = None,
) -> AgentBenchmarkReport:
  started_at = _utc_timestamp()
  labeled_cases = {case.id: case for case in golden_cases if case.golden_findings and not case.needs_human_label}
  grouped: dict[str, list[AgentVariantPrediction]] = {}
  for prediction in predictions:
    if prediction.case_id in labeled_cases:
      grouped.setdefault(prediction.variant, []).append(prediction)
  metrics_by_variant: dict[str, dict[str, float]] = {}
  case_rows: list[dict[str, Any]] = []
  for variant, rows in grouped.items():
    per_case = []
    for prediction in rows:
      metrics = evaluate_findings(labeled_cases[prediction.case_id].golden_findings, prediction.findings)
      per_case.append(metrics)
      case_rows.append({"case_id": prediction.case_id, "variant": variant, **metrics})
    metrics_by_variant[variant] = _aggregate_agent_metrics(per_case)
  return AgentBenchmarkReport(
    dataset_version=dataset_version,
    sample_count=len(labeled_cases),
    config=config or {},
    model=model,
    run_started_at=started_at,
    run_finished_at=_utc_timestamp(),
    variants=metrics_by_variant,
    cases=case_rows,
  )


def evaluate_findings(expected: list[GoldenFinding], predicted: list[PredictedFinding]) -> dict[str, float]:
  expected_keys = {_finding_key(item.skill_code, item.label) for item in expected}
  predicted_keys = [_finding_key(item.skill_code, item.label) for item in predicted]
  predicted_key_set = set(predicted_keys)
  true_positive = len(expected_keys & predicted_key_set)
  precision = true_positive / len(predicted_keys) if predicted_keys else 0.0
  recall = true_positive / len(expected_keys) if expected_keys else 0.0
  f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
  grounded = [item for item in predicted if item.evidence_refs]
  unsupported = [item for item in predicted if not item.supported or not item.evidence_refs]
  return {
    "findingPrecision": precision,
    "findingRecall": recall,
    "findingF1": f1,
    "evidenceRefPresenceRate": len(grounded) / len(predicted) if predicted else 0.0,
    "evidenceGroundingRate": len(grounded) / len(predicted) if predicted else 0.0,
    "unsupportedFindingRate": len(unsupported) / len(predicted) if predicted else 0.0,
  }


def write_agent_report(report: AgentBenchmarkReport, output_dir: str | Path) -> tuple[Path, Path]:
  output = Path(output_dir)
  output.mkdir(parents=True, exist_ok=True)
  json_path = output / "agent_ablation_benchmark_report.json"
  md_path = output / "agent_ablation_benchmark_report.md"
  json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
  md_path.write_text(render_agent_markdown(report), encoding="utf-8")
  return json_path, md_path


def render_agent_markdown(report: AgentBenchmarkReport) -> str:
  lines = [
    "# Video Diagnosis Agent Ablation Benchmark",
    "",
    f"- Dataset version: `{report.dataset_version}`",
    f"- Sample count: `{report.sample_count}`",
    f"- Model: `{report.model}`",
    f"- Run started at: `{report.run_started_at}`",
    f"- Run finished at: `{report.run_finished_at}`",
    f"- Config: `{json.dumps(report.config, ensure_ascii=False)}`",
    "",
    "## Metrics",
    "",
    "| Variant | Precision | Recall | F1 | Grounding Rate | Unsupported Rate |",
    "|---|---:|---:|---:|---:|---:|",
  ]
  for variant, metrics in report.variants.items():
    lines.append(
      f"| {variant} | {metrics['findingPrecision']:.4f} | {metrics['findingRecall']:.4f} | "
      f"{metrics['findingF1']:.4f} | {metrics['evidenceGroundingRate']:.4f} | "
      f"{metrics['unsupportedFindingRate']:.4f} |"
    )
  lines.append("")
  return "\n".join(lines)


def _candidate_cases(
  skill_code: str,
  knowledge_type: str,
  expected_id: str,
  prefix: str,
  query_specs: list[tuple[str, Difficulty]],
) -> list[GoldenQueryCase]:
  return [
    _case(
      f"{prefix}-{index:02d}",
      skill_code,
      query,
      knowledge_type,
      expected_id,
      difficulty,
      "PENDING_REVIEW",
      "Generated candidate. Human review required before use in formal metrics.",
    )
    for index, (query, difficulty) in enumerate(query_specs, start=1)
  ]


def _case(
  query_id: str,
  skill_code: str,
  query: str,
  knowledge_type: str,
  expected_id: str,
  difficulty: Difficulty,
  annotation_status: AnnotationStatus,
  notes: str,
) -> GoldenQueryCase:
  return GoldenQueryCase(
    query_id=query_id,
    query=query,
    skill_code=skill_code,
    knowledge_type=knowledge_type,
    expected_knowledge_ids=[expected_id] if expected_id else [],
    difficulty=difficulty,
    annotation_status=annotation_status,
    notes=notes,
  )


def _case_from_mapping(row: dict[str, Any]) -> GoldenQueryCase:
  return GoldenQueryCase(
    query_id=str(row.get("queryId") or row.get("query_id") or row.get("id")),
    query=str(row["query"]),
    skill_code=str(row.get("skillCode") or row.get("skill_code")),
    knowledge_type=str(row.get("knowledgeType") or row.get("knowledge_type") or "DOMAIN_KNOWLEDGE"),
    expected_knowledge_ids=list(row.get("expectedKnowledgeIds") or row.get("expected_knowledge_ids") or []),
    difficulty=str(row.get("difficulty") or "SEMANTIC"),  # type: ignore[arg-type]
    annotation_status=str(row.get("annotationStatus") or row.get("annotation_status") or "PENDING_REVIEW"),  # type: ignore[arg-type]
    category=str(row.get("category") or ""),
    notes=str(row.get("notes") or ""),
    acceptable_knowledge_ids=list(row.get("acceptableKnowledgeIds") or row.get("acceptable_knowledge_ids") or []),
    hard_negative_knowledge_ids=list(row.get("hardNegativeKnowledgeIds") or row.get("hard_negative_knowledge_ids") or []),
    match_type=str(row.get("matchType") or row.get("match_type") or "SEMANTIC"),  # type: ignore[arg-type]
    hard_negative_scope=str(row.get("hardNegativeScope") or row.get("hard_negative_scope") or ""),  # type: ignore[arg-type]
  )


def _external_case_dict(case: GoldenQueryCase) -> dict[str, Any]:
  return {
    "queryId": case.query_id,
    "query": case.query,
    "skillCode": case.skill_code,
    "knowledgeType": case.knowledge_type,
    "expectedKnowledgeIds": case.expected_knowledge_ids,
    "acceptableKnowledgeIds": case.acceptable_knowledge_ids,
    "hardNegativeKnowledgeIds": case.hard_negative_knowledge_ids,
    "matchType": case.match_type,
    "difficulty": case.difficulty,
    "hardNegativeScope": case.hard_negative_scope,
    "annotationStatus": case.annotation_status,
    "category": case.category,
    "notes": case.notes,
  }


def _assert_expected_ids_exist(
  cases: list[GoldenQueryCase],
  *,
  corpus: list[KnowledgeEvidence] | None = None,
  id_field: str = "expected_knowledge_ids",
) -> None:
  corpus_ids = {item.id for item in (corpus or default_video_diagnosis_corpus())}
  for case in cases:
    knowledge_ids = getattr(case, id_field)
    missing = [item for item in knowledge_ids if item not in corpus_ids]
    if missing:
      raise ValueError(f"Golden case {case.query_id} field {id_field} references missing corpus IDs: {missing}")


def _metrics_row(result: RetrievalCaseResult) -> dict[str, float]:
  return {
    "recallAt1": result.recall_at_1,
    "recallAt3": result.recall_at_3,
    "recallAt5": result.recall_at_5,
    "recallAt10": result.recall_at_10,
    "mrr": result.mrr,
    "acceptableHitAt5": result.acceptable_hit_at_5,
    "hardNegativeAboveExpected": 1.0 if result.hard_negative_above_expected else 0.0,
    "hardNegativeEvaluated": 1.0 if result.hard_negative_knowledge_ids else 0.0,
    "latencyMs": result.avg_latency_ms,
    "embeddingGenerationLatencyMs": result.embedding_generation_latency_ms,
    "retrievalRankingLatencyMs": result.retrieval_ranking_latency_ms,
    "endToEndLatencyMs": result.end_to_end_latency_ms,
  }


def _empty_retrieval_metrics() -> dict[str, float]:
  return {
    "queryCount": 0.0,
    "recallAt1": 0.0,
    "recallAt3": 0.0,
    "recallAt5": 0.0,
    "recallAt10": 0.0,
    "mrr": 0.0,
    "acceptableHitAt5": 0.0,
    "hardNegativeAboveExpectedRate": 0.0,
    "hardNegativeFailureCount": 0.0,
    "hardNegativeEvaluatedQueryCount": 0.0,
    "avgLatencyMs": 0.0,
    "embeddingGenerationLatencyMs": 0.0,
    "retrievalRankingLatencyMs": 0.0,
    "endToEndLatencyMs": 0.0,
    "p50LatencyMs": 0.0,
    "p95LatencyMs": 0.0,
  }


def _percentile(values: list[float], percentile: int) -> float:
  if not values:
    return 0.0
  ordered = sorted(values)
  if len(ordered) == 1:
    return ordered[0]
  index = (len(ordered) - 1) * percentile / 100
  lower = int(index)
  upper = min(lower + 1, len(ordered) - 1)
  weight = index - lower
  return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _group_markdown(grouped: dict[str, dict[str, dict[str, float]]]) -> list[str]:
  lines: list[str] = []
  if not grouped:
    return ["- No VERIFIED samples available for grouped metrics."]
  for group, strategies in grouped.items():
    lines.extend([
      f"### `{group}`",
      "",
      "| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |",
      "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for strategy, metrics in strategies.items():
      lines.append(_metrics_table_row(strategy, metrics))
    lines.append("")
  return lines


def _metrics_table_row(name: str, metrics: dict[str, float]) -> str:
  return (
    f"| {name} | {metrics['recallAt1']:.4f} | {metrics['recallAt3']:.4f} | "
    f"{metrics['recallAt5']:.4f} | {metrics['mrr']:.4f} | "
    f"{metrics['hardNegativeAboveExpectedRate']:.4f} | {metrics['avgLatencyMs']:.3f} | "
    f"{metrics['p50LatencyMs']:.3f} | {metrics['p95LatencyMs']:.3f} |"
  )


def _aggregate_agent_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
  if not rows:
    return {
      "findingPrecision": 0.0,
      "findingRecall": 0.0,
      "findingF1": 0.0,
      "evidenceGroundingRate": 0.0,
      "unsupportedFindingRate": 0.0,
    }
  keys = rows[0].keys()
  return {key: sum(row.get(key, 0.0) for row in rows) / len(rows) for key in keys}


def _recall_at(expected: set[str], ranked_refs: list[str], k: int) -> float:
  top = set(ranked_refs[:k])
  return 1.0 if expected & top else 0.0


def _mrr(expected: set[str], ranked_refs: list[str]) -> float:
  for index, ref in enumerate(ranked_refs):
    if ref in expected:
      return 1.0 / (index + 1)
  return 0.0


def _finding_key(skill_code: str, label: str) -> str:
  return f"{skill_code}:{' '.join((label or '').lower().split())}"


def _utc_timestamp() -> str:
  return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _dataset_version_from_path(path: str | Path) -> str:
  source = Path(path)
  if not source.exists() or source.suffix.lower() == ".jsonl":
    return DEFAULT_DATASET_VERSION
  payload = json.loads(source.read_text(encoding="utf-8"))
  if isinstance(payload, dict) and payload.get("datasetVersion"):
    return str(payload["datasetVersion"])
  return DEFAULT_DATASET_VERSION


def build_embedding_provider(provider_name: str, model_name: str) -> EmbeddingProvider | None:
  if provider_name in {"", "none"}:
    return None
  if provider_name == "openai":
    return OpenAIEmbeddingProvider(model=model_name or "text-embedding-3-small")
  raise ValueError(f"Unsupported embedding provider: {provider_name}")


def main(argv: list[str] | None = None) -> None:
  parser = argparse.ArgumentParser(description="Run video diagnosis benchmark utilities.")
  parser.add_argument("--output-dir", default="benchmark-reports")
  parser.add_argument("--write-datasets", action="store_true")
  parser.add_argument("--write-v05-split", action="store_true")
  parser.add_argument("--run-retrieval", action="store_true")
  parser.add_argument("--run-v05-final-test", action="store_true")
  parser.add_argument("--run-smoke", action="store_true")
  parser.add_argument("--dataset-path", default="")
  parser.add_argument("--dataset-version", default="")
  parser.add_argument("--corpus-version", default="runtime")
  parser.add_argument("--benchmark-mode", choices=["RUNTIME", "SKILL_FILTERED", "GLOBAL"], default="RUNTIME")
  parser.add_argument("--embedding-provider", choices=["none", "openai"], default="none")
  parser.add_argument("--embedding-model", default="text-embedding-3-small")
  parser.add_argument("--use-retrieval-text", action="store_true")
  parser.add_argument("--bm25-weight", type=float, default=0.5)
  parser.add_argument("--embedding-weight", type=float, default=0.5)
  parser.add_argument("--rrf-k", type=int, default=60)
  parser.add_argument("--include-pending", action="store_true")
  parser.add_argument("--repeat-count", type=int, default=5)
  args = parser.parse_args(argv)

  if args.write_datasets:
    save_default_datasets(args.output_dir)
  if args.write_v05_split:
    if not args.dataset_path:
      raise SystemExit("--write-v05-split requires --dataset-path")
    save_v05_dev_test_split(args.dataset_path, "benchmarks")
  if args.run_retrieval or args.run_v05_final_test:
    dataset = load_query_dataset(args.dataset_path) if args.dataset_path else formal_candidate_query_dataset()
    if args.run_v05_final_test:
      verified = [case for case in dataset if case.annotation_status == "VERIFIED"]
      if len(dataset) != 20 or len(verified) != 20:
        raise SystemExit(
          f"v0.5 final test requires exactly 20 VERIFIED queries, got total={len(dataset)} verified={len(verified)}"
        )
    corpus = load_benchmark_corpus(args.corpus_version) if args.corpus_version != "runtime" else default_video_diagnosis_corpus()
    dataset_version = args.dataset_version or (_dataset_version_from_path(args.dataset_path) if args.dataset_path else DEFAULT_DATASET_VERSION)
    try:
      embedding_provider = build_embedding_provider(args.embedding_provider, args.embedding_model)
    except EmbeddingProviderError as exc:
      raise SystemExit(
        f"Embedding provider setup failed: {exc}\n"
        "请先在当前 PowerShell 会话设置 OPENAI_API_KEY，或在 agent-service/.env 中配置后重试。"
      ) from exc
    runner = RetrievalBenchmarkRunner(
      corpus=corpus,
      config=RetrievalRunConfig(
        dataset_version=dataset_version,
        corpus_version=args.corpus_version,
        benchmark_mode=args.benchmark_mode,  # type: ignore[arg-type]
        embedding_provider=args.embedding_provider,
        embedding_model=args.embedding_model if args.embedding_provider != "none" else "",
        use_retrieval_text=True if args.run_v05_final_test else args.use_retrieval_text,
        bm25_weight=0.7 if args.run_v05_final_test else args.bm25_weight,
        embedding_weight=0.3 if args.run_v05_final_test else args.embedding_weight,
        rrf_k=args.rrf_k,
        repeat_count=args.repeat_count,
        retriever_params={
          **DEFAULT_RETRIEVER_PARAMS,
          **({
            "reportMetadata": {
              "datasetSplit": "TEST",
              "selectionSource": "DEV",
              "devSelectedBm25Weight": 0.7,
              "devSelectedEmbeddingWeight": 0.3,
              "testUsedForTuning": False,
              "heuristicRerankerFinalStrategy": False,
            }
          } if args.run_v05_final_test else {}),
        },
      ),
      embedding_provider=embedding_provider,
    )
    final_strategies: list[RetrievalStrategy] | None = None
    if args.run_v05_final_test:
      final_strategies = [
        "BM25_ONLY",
        "EMBEDDING_ONLY",
        "HYBRID_BM25_EMBEDDING_RRF_05_05",
        "FINAL_WEIGHTED_HYBRID",
      ]
    report = runner.run(dataset, strategies=final_strategies, verified_only=not args.include_pending)
    runner.write_report(report, args.output_dir)
    runner.write_miss_analysis(report, dataset, args.output_dir)
  if args.run_smoke:
    runner = RetrievalBenchmarkRunner(config=RetrievalRunConfig(repeat_count=args.repeat_count, verified_only=False))
    runner.write_report(runner.run_smoke(), args.output_dir)


if __name__ == "__main__":
  main()
