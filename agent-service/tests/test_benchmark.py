from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace

import pytest

from agent_service.config import get_settings
from agent_service.knowledge import default_video_diagnosis_corpus, load_benchmark_corpus
from agent_service.retrieval.benchmark import (
  DEFAULT_DATASET_VERSION,
  AgentGoldenCase,
  AgentVariantPrediction,
  GoldenFinding,
  PredictedFinding,
  RetrievalBenchmarkRunner,
  RetrievalRunConfig,
  WeightedRrfConfig,
  aggregate_metrics,
  benchmark_retrieval_text,
  benchmark_v03_candidate_query_dataset,
  build_embedding_provider,
  build_miss_analysis,
  evaluate_agent_variant,
  evaluate_findings,
  evaluate_ranked_refs,
  formal_candidate_query_dataset,
  hard_negative_above_expected,
  load_query_dataset,
  save_benchmark_v03_candidate_dataset,
  save_default_datasets,
  save_v05_dev_test_split,
  smoke_golden_query_dataset,
  split_golden_dataset_v05,
  weighted_reciprocal_rank_fusion,
)
from agent_service.retrieval.embeddings import (
  EmbeddingProviderError,
  StaticEmbeddingProvider,
  cosine_similarity,
)
from agent_service.retrieval.hybrid import InMemoryHybridKnowledgeRetriever
from agent_service.retrieval.models import KnowledgeQuery
from agent_service.retrieval.review_golden import (
  build_review_rows,
  load_review_corpus,
  missing_expected_ids,
  review_dataset,
  review_stats,
  write_review_dataset,
)
from agent_service.retrieval.review_golden import (
  main as review_golden_main,
)
from agent_service.retrieval.rrf import reciprocal_rank_fusion


class CountingStaticEmbeddingProvider(StaticEmbeddingProvider):
  def __init__(self, vectors: dict[str, list[float]]) -> None:
    super().__init__(vectors=vectors)
    self.batch_calls = 0
    self.single_calls = 0

  def embed(self, text: str) -> list[float]:
    self.single_calls += 1
    return super().embed(text)

  def embed_batch(self, texts: list[str]) -> list[list[float]]:
    self.batch_calls += 1
    return [StaticEmbeddingProvider.embed(self, text) for text in texts]


def test_smoke_golden_query_ids_exist_in_real_corpus() -> None:
  corpus_ids = {item.id for item in default_video_diagnosis_corpus()}

  for case in smoke_golden_query_dataset():
    assert case.expected_knowledge_ids
    assert set(case.expected_knowledge_ids).issubset(corpus_ids)


def test_benchmark_corpus_v03_loads_independently_without_runtime_changes() -> None:
  runtime_corpus = default_video_diagnosis_corpus()
  benchmark_corpus = load_benchmark_corpus("v0.3")

  assert len(runtime_corpus) == 6
  assert 33 <= len(benchmark_corpus) <= 34
  assert {item.version for item in benchmark_corpus} == {"v0.3"}
  assert {item.source for item in benchmark_corpus} == {"video-diagnosis-benchmark"}
  assert all(item.metadata.get("benchmarkOnly") is True for item in benchmark_corpus)
  assert {item.id for item in runtime_corpus}.isdisjoint({item.id for item in benchmark_corpus})


def test_benchmark_corpus_v03_rejects_unsupported_versions() -> None:
  with pytest.raises(ValueError):
    load_benchmark_corpus("v9.9")


def test_benchmark_corpus_v03_has_unique_ids_and_expected_skill_distribution() -> None:
  benchmark_corpus = load_benchmark_corpus("v0.3")
  ids = [item.id for item in benchmark_corpus]
  skill_counts = Counter(item.skill_code for item in benchmark_corpus)

  assert len(ids) == len(set(ids))
  assert len(benchmark_corpus) == 34
  assert skill_counts == {
    "hook_analysis": 12,
    "structure_rhythm_analysis": 11,
    "value_delivery_analysis": 11,
  }
  assert all(10 <= count <= 12 for count in skill_counts.values())


def test_benchmark_corpus_v03_confusion_groups_cover_major_hard_negative_pairs() -> None:
  group_members: dict[str, set[str]] = defaultdict(set)
  for item in load_benchmark_corpus("v0.3"):
    groups = item.metadata.get("confusionGroup", [])
    if isinstance(groups, str):
      groups = [groups]
    for group in groups:
      group_members[group].add(item.id)

  expected_pairs = {
    "self_intro_authority": {
      "hook-pattern-self-intro-delay-v1",
      "hook-good-case-authority-fast-v1",
    },
    "curiosity_empty_suspense": {
      "hook-pattern-curiosity-gap-v1",
      "hook-bad-case-empty-suspense-v1",
    },
    "hook_value_boundary": {
      "hook-pattern-pain-benefit-v2",
      "value-pattern-audience-outcome-v1",
    },
    "visual_proof_value_proof": {
      "hook-good-case-visual-proof-v1",
      "value-good-case-proof-before-claim-v1",
    },
    "static_density": {
      "structure-rule-density-scene-change-v1",
      "structure-bad-case-static-talking-v1",
    },
    "midpoint_specificity": {
      "structure-rule-midpoint-retention-v1",
      "value-rule-specificity-v1",
    },
    "before_after_structure_value": {
      "structure-pattern-contrast-before-after-v1",
      "value-rule-before-after-outcome-v1",
    },
    "example_proof": {
      "structure-good-case-example-driven-v1",
      "value-good-case-proof-before-claim-v1",
    },
    "action_cta_fit": {
      "value-pattern-actionable-advice-v1",
      "value-rule-call-to-action-fit-v1",
    },
  }
  for group, members in expected_pairs.items():
    assert members.issubset(group_members[group])


def test_benchmark_v03_candidate_dataset_distribution_and_refs() -> None:
  cases = benchmark_v03_candidate_query_dataset()
  corpus_ids = {item.id for item in load_benchmark_corpus("v0.3")}
  skill_counts = Counter(case.skill_code for case in cases)
  difficulty_counts = Counter(case.difficulty for case in cases)
  match_type_counts = Counter(case.match_type for case in cases)
  primary_counts = Counter(case.expected_knowledge_ids[0] for case in cases if case.expected_knowledge_ids)

  assert len(cases) == 60
  assert skill_counts == {
    "hook_analysis": 20,
    "structure_rhythm_analysis": 20,
    "value_delivery_analysis": 20,
  }
  assert difficulty_counts == {
    "EASY": 12,
    "MEDIUM": 18,
    "HARD": 18,
    "ADVERSARIAL": 12,
  }
  assert set(match_type_counts) == {"EXACT", "SEMANTIC", "MIXED"}
  assert {case.annotation_status for case in cases} == {"PENDING_REVIEW"}
  assert all(set(case.expected_knowledge_ids).issubset(corpus_ids) for case in cases)
  assert all(set(case.acceptable_knowledge_ids).issubset(corpus_ids) for case in cases)
  assert all(set(case.hard_negative_knowledge_ids).issubset(corpus_ids) for case in cases)
  assert max(primary_counts.values()) <= 3
  assert sum(1 for case in cases if case.hard_negative_scope == "INTRA_SKILL") >= 10
  assert sum(1 for case in cases if case.hard_negative_scope == "CROSS_SKILL") >= 10
  assert sum(1 for case in cases if case.hard_negative_knowledge_ids) >= 45
  assert sum(1 for case in cases if case.acceptable_knowledge_ids) >= 10
  assert sum(1 for case in cases if len(case.expected_knowledge_ids) > 1) >= 6


def test_benchmark_v03_candidate_files_can_be_written_and_loaded(tmp_path) -> None:
  json_path, jsonl_path = save_benchmark_v03_candidate_dataset(tmp_path)

  assert json_path.name == "retrieval_golden_candidates.v0.3.json"
  assert jsonl_path.name == "retrieval_golden_candidates.v0.3.jsonl"
  assert len(load_query_dataset(json_path)) == 60
  assert len(load_query_dataset(jsonl_path)) == 60
  loaded = load_query_dataset(json_path)
  assert loaded[0].match_type in {"EXACT", "SEMANTIC", "MIXED"}
  assert loaded[0].hard_negative_knowledge_ids


def test_v05_split_is_reproducible_and_preserves_all_query_ids(tmp_path) -> None:
  json_path, _ = save_benchmark_v03_candidate_dataset(tmp_path)
  cases = load_query_dataset(json_path)
  dev, test = split_golden_dataset_v05(cases, seed=123)
  dev_again, test_again = split_golden_dataset_v05(cases, seed=123)

  assert len(dev) == 40
  assert len(test) == 20
  assert {case.query_id for case in dev}.isdisjoint({case.query_id for case in test})
  assert {case.query_id for case in dev + test} == {case.query_id for case in cases}
  assert [case.query_id for case in dev] == [case.query_id for case in dev_again]
  assert [case.query_id for case in test] == [case.query_id for case in test_again]

  dev_path, test_path = save_v05_dev_test_split(json_path, tmp_path, seed=123)
  assert len(load_query_dataset(dev_path)) == 40
  assert len(load_query_dataset(test_path)) == 20


def test_benchmark_retrieval_text_is_benchmark_only_and_safe() -> None:
  item = next(item for item in load_benchmark_corpus("v0.3") if item.id == "hook-pattern-curiosity-gap-v1")
  text = benchmark_retrieval_text(item)

  assert item.id == "hook-pattern-curiosity-gap-v1"
  assert "difficulty" not in text
  assert "confusionGroup" not in text
  assert "queryId" not in text
  assert "v03-" not in text
  assert "别急着买这个" not in text
  assert "empty_suspense" in text


def test_weighted_rrf_formula_and_weight_sensitivity() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  bm25_ranked = [corpus[0], corpus[1]]
  embedding_ranked = [corpus[1], corpus[0]]

  equal = weighted_reciprocal_rank_fusion(
    bm25_ranked,
    embedding_ranked,
    WeightedRrfConfig(0.5, 0.5, 60),
    final_top_k=2,
  )
  bm25_heavy = weighted_reciprocal_rank_fusion(
    bm25_ranked,
    embedding_ranked,
    WeightedRrfConfig(0.7, 0.3, 60),
    final_top_k=2,
  )
  embedding_heavy = weighted_reciprocal_rank_fusion(
    bm25_ranked,
    embedding_ranked,
    WeightedRrfConfig(0.3, 0.7, 60),
    final_top_k=2,
  )

  expected_score = 0.7 / 61 + 0.3 / 62
  assert round(bm25_heavy[0][1], 8) == round(expected_score, 8)
  assert {item.id for item, _ in equal} == {corpus[0].id, corpus[1].id}
  assert bm25_heavy[0][0].id == corpus[0].id
  assert embedding_heavy[0][0].id == corpus[1].id


def test_weighted_rrf_equal_weights_matches_regular_rrf_order() -> None:
  corpus = load_benchmark_corpus("v0.3")[:3]
  bm25_ranked = [corpus[0], corpus[1], corpus[2]]
  embedding_ranked = [corpus[0], corpus[2], corpus[1]]

  regular = reciprocal_rank_fusion(
    [embedding_ranked, bm25_ranked],
    lambda item: item.id,
    final_top_k=3,
    rrf_k=60,
  )
  weighted = weighted_reciprocal_rank_fusion(
    bm25_ranked,
    embedding_ranked,
    WeightedRrfConfig(0.5, 0.5, 60),
    final_top_k=3,
  )

  regular_scores = {item.id: score for item, score in regular}
  weighted_scores = {item.id: score for item, score in weighted}
  assert set(weighted_scores) == set(regular_scores)
  for knowledge_id, score in weighted_scores.items():
    assert round(score, 8) == round(regular_scores[knowledge_id] * 0.5, 8)


def test_embedding_cosine_similarity_ranking_and_query_embedding() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  vectors = {
    _embedding_text(corpus[0]): [1.0, 0.0],
    _embedding_text(corpus[1]): [0.0, 1.0],
    "semantic query": [0.9, 0.1],
  }
  provider = CountingStaticEmbeddingProvider(vectors)
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
    embedding_provider=provider,
  )

  ranked = runner.retriever.search_embedding(
    KnowledgeQuery("semantic query", "hook_analysis", "HOOK_PATTERN", top_k=2),
    limit=2,
  )

  assert ranked[0].id == corpus[0].id
  assert provider.batch_calls == 1
  assert provider.single_calls == 1
  assert cosine_similarity([1.0, 0.0], [0.5, 0.0]) == 1.0


def test_query_embedding_is_cached_across_embedding_strategies_and_repeats() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  vectors = {
    _embedding_text(corpus[0]): [1.0, 0.0],
    _embedding_text(corpus[1]): [0.0, 1.0],
    "same query": [0.9, 0.1],
  }
  provider = CountingStaticEmbeddingProvider(vectors)
  case = replace(
    benchmark_v03_candidate_query_dataset()[0],
    query="same query",
    expected_knowledge_ids=[corpus[0].id],
    annotation_status="VERIFIED",
  )
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=3),
    embedding_provider=provider,
  )

  runner.run(
    [case],
    strategies=[
      "EMBEDDING_ONLY",
      "HYBRID_BM25_EMBEDDING_RRF",
      "HYBRID_BM25_EMBEDDING_RRF_RERANK",
    ],
  )

  assert provider.batch_calls == 1
  assert provider.single_calls == 1


def test_latency_fields_separate_embedding_and_ranking_time() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  vectors = {
    _embedding_text(corpus[0]): [1.0, 0.0],
    _embedding_text(corpus[1]): [0.0, 1.0],
    "latency query": [1.0, 0.0],
  }
  case = replace(
    benchmark_v03_candidate_query_dataset()[0],
    query="latency query",
    expected_knowledge_ids=[corpus[0].id],
    annotation_status="VERIFIED",
  )
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
    embedding_provider=CountingStaticEmbeddingProvider(vectors),
  )

  report = runner.run([case], strategies=["EMBEDDING_ONLY"])
  row = report.cases[0]

  assert row["embedding_generation_latency_ms"] >= 0
  assert row["retrieval_ranking_latency_ms"] >= 0
  assert row["end_to_end_latency_ms"] >= row["embedding_generation_latency_ms"]
  assert row["embedding_latency_included_in_end_to_end"] is True


def test_miss_analysis_expected_rank_hard_negative_and_pairs() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  case = replace(
    benchmark_v03_candidate_query_dataset()[0],
    query="miss query",
    expected_knowledge_ids=[corpus[0].id],
    hard_negative_knowledge_ids=[corpus[1].id],
    annotation_status="VERIFIED",
  )
  vectors = {
    _embedding_text(corpus[0]): [0.0, 1.0],
    _embedding_text(corpus[1]): [1.0, 0.0],
    "miss query": [1.0, 0.0],
  }
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
    embedding_provider=StaticEmbeddingProvider(vectors),
  )
  report = runner.run([case], strategies=["EMBEDDING_ONLY"])

  analysis = build_miss_analysis(report, [case])
  row = analysis["rows"][0]

  assert row["Embedding"]["expectedBestRank"] == 2
  assert row["highestHardNegativeRank"] == 1
  assert row["hardNegativeAboveExpected"] is True
  assert row["errorType"] == "HARD_NEGATIVE_CONFUSION"
  assert analysis["summary"]["topRecurringConfusedKnowledgePairs"]


def test_miss_analysis_handles_missing_expected_ranks_without_crashing() -> None:
  case = replace(
    benchmark_v03_candidate_query_dataset()[0],
    expected_knowledge_ids=["missing-expected"],
    annotation_status="VERIFIED",
  )
  report = type("Report", (), {
    "dataset_version": "test",
    "corpus_version": "v0.3",
    "benchmark_mode": "GLOBAL",
    "cases": [
      {
        "query_id": case.query_id,
        "strategy": "HYBRID_BM25_EMBEDDING_RRF",
        "ranked_knowledge_ids": ["a", "b"],
        "hard_negative_above_expected": False,
        "candidate_pool_size": 2,
      },
      {
        "query_id": case.query_id,
        "strategy": "HYBRID_BM25_EMBEDDING_RRF_RERANK",
        "ranked_knowledge_ids": ["b", "a"],
        "hard_negative_above_expected": False,
        "candidate_pool_size": 2,
      },
    ],
  })()

  analysis = build_miss_analysis(report, [case])

  assert analysis["rows"][0]["Hybrid"]["expectedBestRank"] is None
  assert analysis["rows"][0]["Rerank"]["expectedBestRank"] is None
  assert analysis["rows"][0]["errorType"] != "RERANK_INVERSION"


def test_v05_final_test_requires_exactly_twenty_verified_queries(tmp_path) -> None:
  json_path, _ = save_benchmark_v03_candidate_dataset(tmp_path)

  with pytest.raises(SystemExit) as error:
    from agent_service.retrieval.benchmark import main as benchmark_main

    benchmark_main([
      "--run-v05-final-test",
      "--dataset-path",
      str(json_path),
      "--corpus-version",
      "v0.3",
      "--benchmark-mode",
      "GLOBAL",
      "--embedding-provider",
      "none",
    ])

  assert "exactly 20 VERIFIED" in str(error.value)


def test_bm25_and_embedding_can_rank_differently() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  vectors = {
    _embedding_text(corpus[0]): [0.0, 1.0],
    _embedding_text(corpus[1]): [1.0, 0.0],
    "自我介绍拖慢开场": [1.0, 0.0],
  }
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
    embedding_provider=StaticEmbeddingProvider(vectors),
  )
  query = KnowledgeQuery("自我介绍拖慢开场", "hook_analysis", "HOOK_PATTERN", top_k=2)

  bm25_ranked = runner.retriever.search_bm25(query, limit=2)
  embedding_ranked = runner.retriever.search_embedding(query, limit=2)

  assert bm25_ranked[0].id == corpus[0].id
  assert embedding_ranked[0].id == corpus[1].id


def test_embedding_rrf_fuses_bm25_and_embedding_rankings() -> None:
  corpus = load_benchmark_corpus("v0.3")[:2]
  vectors = {
    _embedding_text(corpus[0]): [0.0, 1.0],
    _embedding_text(corpus[1]): [1.0, 0.0],
    "自我介绍拖慢开场": [1.0, 0.0],
  }
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
    embedding_provider=StaticEmbeddingProvider(vectors),
  )

  fused = runner.retriever.search_hybrid_rrf(
    KnowledgeQuery("自我介绍拖慢开场", "hook_analysis", "HOOK_PATTERN", top_k=2),
    final_top_k=2,
  )

  assert {item.id for item in fused} == {corpus[0].id, corpus[1].id}
  assert all(item.score > 0 for item in fused)


def test_embedding_provider_failure_is_explicit() -> None:
  corpus = load_benchmark_corpus("v0.3")[:1]
  provider = StaticEmbeddingProvider({_embedding_text(corpus[0]): [1.0, 0.0]})
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
    embedding_provider=provider,
  )

  with pytest.raises(EmbeddingProviderError):
    runner.retriever.search_embedding(
      KnowledgeQuery("missing query vector", "hook_analysis", "HOOK_PATTERN"),
      limit=1,
    )


def test_openai_embedding_provider_requires_api_key(monkeypatch) -> None:
  get_settings.cache_clear()
  monkeypatch.delenv("OPENAI_API_KEY", raising=False)
  monkeypatch.delenv("EMBEDDING_OPENAI_API_KEY", raising=False)

  with pytest.raises(EmbeddingProviderError):
    build_embedding_provider("openai", "text-embedding-3-small")
  get_settings.cache_clear()


def test_chat_and_embedding_settings_are_isolated(monkeypatch) -> None:
  get_settings.cache_clear()
  monkeypatch.delenv("CHAT_API_KEY", raising=False)
  monkeypatch.delenv("CHAT_MODEL", raising=False)
  monkeypatch.delenv("CHAT_BASE_URL", raising=False)
  monkeypatch.delenv("EMBEDDING_OPENAI_API_KEY", raising=False)
  monkeypatch.delenv("EMBEDDING_OPENAI_BASE_URL", raising=False)
  monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
  monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
  monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
  monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
  monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
  monkeypatch.setenv("EMBEDDING_OPENAI_MODEL", "text-embedding-3-small")

  settings = get_settings()

  assert settings.chat_api_key == "deepseek-key"
  assert settings.chat_model == "deepseek-chat"
  assert settings.chat_base_url == "https://api.deepseek.com"
  assert settings.embedding_openai_api_key == "openai-key"
  assert settings.embedding_openai_model == "text-embedding-3-small"
  assert settings.embedding_openai_base_url == "https://api.openai.com/v1"
  get_settings.cache_clear()


def test_benchmark_cli_reports_embedding_provider_setup_error(tmp_path, monkeypatch) -> None:
  get_settings.cache_clear()
  monkeypatch.delenv("OPENAI_API_KEY", raising=False)
  monkeypatch.delenv("EMBEDDING_OPENAI_API_KEY", raising=False)
  json_path, _ = save_benchmark_v03_candidate_dataset(tmp_path)

  with pytest.raises(SystemExit) as error:
    from agent_service.retrieval.benchmark import main as benchmark_main

    benchmark_main([
      "--run-retrieval",
      "--dataset-path",
      str(json_path),
      "--corpus-version",
      "v0.3",
      "--benchmark-mode",
      "GLOBAL",
      "--embedding-provider",
      "openai",
    ])

  assert "Embedding provider setup failed" in str(error.value)
  assert "EMBEDDING_OPENAI_API_KEY" in str(error.value)
  get_settings.cache_clear()


def test_formal_benchmark_skill_filtered_candidate_pool_is_not_degenerate() -> None:
  corpus = load_benchmark_corpus("v0.3")
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="SKILL_FILTERED", repeat_count=1),
  )
  case = benchmark_v03_candidate_query_dataset()[0]
  query = KnowledgeQuery(case.query, case.skill_code, case.knowledge_type, top_k=10)

  assert runner.retriever.candidate_pool_size(query) == 12
  report = runner.run([replace(case, annotation_status="VERIFIED")], strategies=["BM25_ONLY"])
  assert report.candidate_pool["candidatePoolMedian"] > 1


def test_formal_benchmark_global_candidate_pool_is_full_v03_corpus() -> None:
  corpus = load_benchmark_corpus("v0.3")
  runner = RetrievalBenchmarkRunner(
    corpus=corpus,
    config=RetrievalRunConfig(corpus_version="v0.3", benchmark_mode="GLOBAL", repeat_count=1),
  )
  case = benchmark_v03_candidate_query_dataset()[0]
  query = KnowledgeQuery(case.query, case.skill_code, case.knowledge_type, top_k=10)

  assert runner.retriever.candidate_pool_size(query) == 34
  report = runner.run([replace(case, annotation_status="VERIFIED")], strategies=["BM25_ONLY"])
  assert report.candidate_pool == {
    "candidatePoolMin": 34.0,
    "candidatePoolMedian": 34.0,
    "candidatePoolMax": 34.0,
  }


def test_core_retrieval_metrics_recall_and_mrr_are_expected_only() -> None:
  metrics = evaluate_ranked_refs(
    ["KNOWLEDGE:expected-a", "KNOWLEDGE:expected-b"],
    ["KNOWLEDGE:acceptable-only", "KNOWLEDGE:expected-b", "KNOWLEDGE:hard-negative"],
  )

  assert metrics["recallAt1"] == 0.0
  assert metrics["recallAt3"] == 1.0
  assert metrics["recallAt5"] == 1.0
  assert metrics["mrr"] == 0.5


def test_acceptable_ids_do_not_affect_core_metrics() -> None:
  metrics = evaluate_ranked_refs(
    ["KNOWLEDGE:expected-only"],
    ["KNOWLEDGE:acceptable-only", "KNOWLEDGE:other"],
  )

  assert metrics["recallAt1"] == 0.0
  assert metrics["recallAt3"] == 0.0
  assert metrics["recallAt5"] == 0.0
  assert metrics["mrr"] == 0.0


def test_hard_negative_above_expected_metric() -> None:
  assert hard_negative_above_expected(
    expected_knowledge_ids=["expected-a", "expected-b"],
    hard_negative_knowledge_ids=["hard-negative"],
    ranked_knowledge_ids=["hard-negative", "expected-b", "expected-a"],
  )
  assert not hard_negative_above_expected(
    expected_knowledge_ids=["expected-a", "expected-b"],
    hard_negative_knowledge_ids=["hard-negative"],
    ranked_knowledge_ids=["expected-b", "hard-negative", "expected-a"],
  )


def test_hard_negative_above_expected_rate_aggregation() -> None:
  metrics = aggregate_metrics([
    {
      "recallAt1": 0.0,
      "recallAt3": 1.0,
      "recallAt5": 1.0,
      "mrr": 0.5,
      "acceptableHitAt5": 0.0,
      "hardNegativeAboveExpected": 1.0,
      "hardNegativeEvaluated": 1.0,
      "latencyMs": 1.0,
    },
    {
      "recallAt1": 1.0,
      "recallAt3": 1.0,
      "recallAt5": 1.0,
      "mrr": 1.0,
      "acceptableHitAt5": 0.0,
      "hardNegativeAboveExpected": 0.0,
      "hardNegativeEvaluated": 1.0,
      "latencyMs": 3.0,
    },
  ])

  assert metrics["hardNegativeAboveExpectedRate"] == 0.5
  assert metrics["hardNegativeFailureCount"] == 1.0
  assert metrics["hardNegativeEvaluatedQueryCount"] == 2.0


def test_runtime_retriever_behavior_is_unchanged() -> None:
  corpus = default_video_diagnosis_corpus()
  retriever = InMemoryHybridKnowledgeRetriever(corpus)
  query = KnowledgeQuery(
    query_text="前三秒痛点收益",
    skill_code="hook_analysis",
    knowledge_type="DOMAIN_KNOWLEDGE",
    top_k=10,
  )
  candidate_ids = {item.id for item in retriever.filter_candidates(query)}

  assert len(corpus) == 6
  assert candidate_ids == {"hook-pattern-opening-pain-v1"}


def test_formal_candidate_dataset_has_pending_review_cases_per_skill() -> None:
  corpus_ids = {item.id for item in default_video_diagnosis_corpus()}
  cases = formal_candidate_query_dataset()

  assert len(cases) >= 60
  assert {case.skill_code for case in cases} == {
    "hook_analysis",
    "structure_rhythm_analysis",
    "value_delivery_analysis",
  }
  for skill_code in {case.skill_code for case in cases}:
    assert sum(1 for case in cases if case.skill_code == skill_code) >= 20
  assert {case.difficulty for case in cases} >= {"EXACT", "SEMANTIC", "MIXED"}
  assert {case.annotation_status for case in cases} == {"PENDING_REVIEW"}
  assert all(set(case.expected_knowledge_ids).issubset(corpus_ids) for case in cases)


def test_retrieval_runner_defaults_to_verified_only() -> None:
  report = RetrievalBenchmarkRunner().run()

  assert report.dataset_version == DEFAULT_DATASET_VERSION
  assert report.verified_sample_count == 0
  assert report.corpus_size == len(default_video_diagnosis_corpus())
  assert report.cases == []
  assert set(report.strategies) == {
    "BM25_ONLY",
    "EMBEDDING_ONLY",
    "HYBRID_BM25_EMBEDDING_RRF",
    "HYBRID_BM25_EMBEDDING_RRF_RERANK",
  }
  assert all(metrics["queryCount"] == 0.0 for metrics in report.strategies.values())


def test_retrieval_runner_can_run_smoke_four_strategies() -> None:
  report = RetrievalBenchmarkRunner(config=RetrievalRunConfig(repeat_count=2)).run_smoke()

  assert report.dataset_version == "video-diagnosis-rag-smoke-v0.1"
  assert report.verified_sample_count == 6
  assert set(report.strategies) == {"BM25_ONLY", "VECTOR_ONLY", "HYBRID_RRF", "HYBRID_RRF_RERANK"}
  assert all("recallAt5" in metrics for metrics in report.strategies.values())
  assert all("avgLatencyMs" in metrics for metrics in report.strategies.values())
  assert all("p50LatencyMs" in metrics for metrics in report.strategies.values())
  assert all("p95LatencyMs" in metrics for metrics in report.strategies.values())
  assert len(report.cases) == 24


def test_retrieval_runner_can_include_pending_for_analysis() -> None:
  report = RetrievalBenchmarkRunner(config=RetrievalRunConfig(repeat_count=2)).run(
    strategies=["BM25_ONLY", "VECTOR_ONLY", "HYBRID_RRF", "HYBRID_RRF_RERANK"],
    verified_only=False,
  )

  assert report.verified_sample_count == 0
  assert len(report.cases) == len(formal_candidate_query_dataset()) * 4
  assert set(report.by_skill_code) == {"hook_analysis", "structure_rhythm_analysis", "value_delivery_analysis"}
  assert set(report.by_difficulty) >= {"EXACT", "SEMANTIC", "MIXED"}
  assert "recall_at_5_misses" not in report.strategies


def test_benchmark_dataset_and_reports_can_be_written(tmp_path) -> None:
  dataset_paths = save_default_datasets(tmp_path)
  report = RetrievalBenchmarkRunner().run_smoke()
  report_paths = RetrievalBenchmarkRunner().write_report(report, tmp_path)

  for path in [*dataset_paths, *report_paths]:
    assert path.exists()
    assert path.read_text(encoding="utf-8")

  assert (tmp_path / "retrieval_golden_candidates.v0.2.json").exists()
  assert (tmp_path / "retrieval_golden_candidates.v0.2.jsonl").exists()


def test_review_rows_include_expected_summary_and_three_retrieval_channels() -> None:
  case = formal_candidate_query_dataset()[0]

  rows = build_review_rows([case])

  assert rows[0]["queryId"] == case.query_id
  assert rows[0]["expectedKnowledgeIds"] == case.expected_knowledge_ids
  assert rows[0]["expectedKnowledgeSummaries"]
  assert rows[0]["bm25Top5"]
  assert rows[0]["vectorTop5"]
  assert rows[0]["hybridTop5"]


def test_review_golden_v03_uses_benchmark_corpus_for_expected_summaries() -> None:
  cases = benchmark_v03_candidate_query_dataset()[:1]
  corpus = load_review_corpus("v0.3")
  rows = build_review_rows(cases, corpus)

  assert len(corpus) == 34
  assert missing_expected_ids(cases, corpus) == []
  assert "未在当前 corpus 中找到" not in rows[0]["expectedKnowledgeSummaries"][0]
  assert rows[0]["bm25Top5"]
  assert rows[0]["vectorTop5"]
  assert rows[0]["hybridTop5"]


def test_review_golden_wrong_corpus_fails_fast_before_manual_review(tmp_path) -> None:
  json_path, _ = save_benchmark_v03_candidate_dataset(tmp_path)
  output_path = tmp_path / "verified.json"

  with pytest.raises(SystemExit) as error:
    review_golden_main([
      "--input",
      str(json_path),
      "--output",
      str(output_path),
    ])

  assert "missing from the selected corpus" in str(error.value)
  assert not output_path.exists()


def test_review_golden_default_runtime_corpus_still_has_six_items() -> None:
  assert len(load_review_corpus("runtime")) == 6
  assert len(default_video_diagnosis_corpus()) == 6


def test_review_dataset_only_manual_v_marks_verified_and_writes_new_file(tmp_path) -> None:
  cases = formal_candidate_query_dataset()[:4]
  answers = iter([
    "v",
    "r",
    "s",
    "e",
    "编辑后的 query",
    "value-delivery-pattern-clear-outcome-v1",
    "MIXED",
  ])

  reviewed = review_dataset(
    cases,
    input_func=lambda _: next(answers),
    output_func=lambda _: None,
  )
  output_path = write_review_dataset(reviewed, tmp_path / "retrieval_golden_verified.v0.3.json")
  stats = review_stats(reviewed)

  assert cases[0].annotation_status == "PENDING_REVIEW"
  assert reviewed[0].annotation_status == "VERIFIED"
  assert reviewed[1].annotation_status == "REJECTED"
  assert reviewed[2].annotation_status == "PENDING_REVIEW"
  assert reviewed[3].annotation_status == "PENDING_REVIEW"
  assert reviewed[3].query == "编辑后的 query"
  assert reviewed[3].expected_knowledge_ids == ["value-delivery-pattern-clear-outcome-v1"]
  assert reviewed[3].difficulty == "MIXED"
  assert stats["VERIFIED"] == 1
  assert stats["REJECTED"] == 1
  assert stats["PENDING"] == 2
  assert output_path.exists()
  assert "retrieval_golden_verified.v0.3.json" in str(output_path)


def test_agent_finding_metrics() -> None:
  metrics = evaluate_findings(
    [GoldenFinding("g1", "hook_analysis", "opening hook weak", ["FRAME:1"])],
    [
      PredictedFinding("p1", "hook_analysis", "opening hook weak", ["FRAME:1"], supported=True),
      PredictedFinding("p2", "value_delivery_analysis", "unsupported value", [], supported=False),
    ],
  )

  assert metrics["findingPrecision"] == 0.5
  assert metrics["findingRecall"] == 1.0
  assert round(metrics["findingF1"], 4) == 0.6667
  assert metrics["evidenceGroundingRate"] == 0.5
  assert metrics["unsupportedFindingRate"] == 0.5


def test_agent_ablation_ignores_unlabeled_cases() -> None:
  report = evaluate_agent_variant(
    [
      AgentGoldenCase(
        id="case-1",
        video_case_id="video-1",
        golden_findings=[GoldenFinding("g1", "hook_analysis", "opening hook weak", ["FRAME:1"])],
        needs_human_label=False,
      ),
      AgentGoldenCase(id="case-2", video_case_id="video-2", golden_findings=[], needs_human_label=True),
    ],
    [
      AgentVariantPrediction(
        case_id="case-1",
        variant="RAG",
        findings=[PredictedFinding("p1", "hook_analysis", "opening hook weak", ["FRAME:1"])],
      ),
      AgentVariantPrediction(
        case_id="case-2",
        variant="RAG",
        findings=[PredictedFinding("p2", "hook_analysis", "not labeled", ["FRAME:2"])],
      ),
    ],
    dataset_version="agent-test-v1",
    model="manual-prediction-fixture",
  )

  assert report.sample_count == 1
  assert report.variants["RAG"]["findingF1"] == 1.0


def _embedding_text(item) -> str:
  return " ".join([item.title, item.content, " ".join(item.tags)])
