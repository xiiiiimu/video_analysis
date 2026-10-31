# RAG 与 Agent 实验复盘

## RAG 实现边界

当前项目有两套 corpus：

- Runtime MVP corpus：`agent-service/src/agent_service/knowledge/corpus.py` 的 `default_video_diagnosis_corpus()`，共 6 条，用于线上 Agent MVP 默认行为。
- Benchmark corpus：同文件的 `load_benchmark_corpus("v0.3")`，共 34 条，只服务 retrieval benchmark 和人工审核，不影响 runtime 默认 corpus。

面试时要明确说：

- 没有引入 Elasticsearch / Milvus / PGVector。
- 当前 benchmark 使用内存索引，因为 corpus 只有 34 条，重点展示检索算法和评测方法。
- Runtime 默认检索仍使用轻量 `InMemoryHybridKnowledgeRetriever`。
- v0.4/v0.5 benchmark 新增 OpenAI embedding cosine 检索，但没有改变 runtime 默认行为。

## Retriever 代码

核心文件：

- `agent-service/src/agent_service/retrieval/models.py`
- `agent-service/src/agent_service/retrieval/hybrid.py`
- `agent-service/src/agent_service/retrieval/embeddings.py`
- `agent-service/src/agent_service/retrieval/rrf.py`
- `agent-service/src/agent_service/retrieval/benchmark.py`

主要抽象：

- `KnowledgeEvidence`：知识条目。
- `KnowledgeQuery`：查询条件。
- `KnowledgeRetriever`：检索接口。
- `EmbeddingProvider`：embedding provider 抽象。
- `OpenAIEmbeddingProvider`：真实 OpenAI embedding 适配器。
- `StaticEmbeddingProvider`：测试用静态向量，不是生产 fallback。

## Runtime Retriever

文件：`agent-service/src/agent_service/retrieval/hybrid.py`

当前 runtime 的 `InMemoryHybridKnowledgeRetriever` 包含：

- 简化 BM25-like 词面打分。
- keyword-vector-like Jaccard baseline。
- RRF 融合。
- heuristic rerank。

注意：

- 早期 `VECTOR_ONLY` 不是语义 embedding，而是 keyword baseline。
- 后续正式 embedding benchmark 在 `benchmark.py` 的 `BenchmarkKnowledgeRetriever` 内实现。

## Embedding Retriever

文件：`agent-service/src/agent_service/retrieval/embeddings.py`

真实 embedding 接入：

- Provider：`OpenAIEmbeddingProvider`
- 默认模型：`text-embedding-3-small`
- 维度：最终报告显示 `1536`
- 相似度：`cosine_similarity`

工程细节：

- corpus embedding 在构建 benchmark retriever 时批量生成并缓存在内存。
- query embedding 每个 query 只生成一次，并在 runner 内缓存。
- 如果缺少 `EMBEDDING_OPENAI_API_KEY` 或 `OPENAI_API_KEY`，会抛出明确异常。
- `.env` 中 Chat 模型可以走 DeepSeek，Embedding 单独走 OpenAI，配置在 `agent-service/src/agent_service/config.py`。

## Benchmark Dataset

真实数据文件：

- v0.3 人工审核全集：`agent-service/benchmarks/retrieval_golden_verified.v0.3.clean2.json`
- v0.5 dev split：`agent-service/benchmarks/retrieval_golden_dev.v0.5.json`
- v0.5 test split：`agent-service/benchmarks/retrieval_golden_test.v0.5.json`

v0.3 corpus：

- 总数：34 条。
- `hook_analysis`：12 条。
- `structure_rhythm_analysis`：11 条。
- `value_delivery_analysis`：11 条。
- 包含 hard negative confusion group，如 `self_intro_authority`、`curiosity_empty_suspense`、`hook_value_boundary`、`visual_proof_value_proof`。

v0.5 split：

- Dev：40 条，用于选择参数。
- Test：20 条，用于最终 held-out test。
- Test 已人工 VERIFIED，正式报告标记 `datasetSplit = TEST`、`testUsedForTuning = false`。

## 指标

核心指标只使用 `expectedKnowledgeIds`：

- `Recall@1`
- `Recall@3`
- `Recall@5`
- `MRR`

辅助指标：

- `acceptableKnowledgeIds` 只做 soft hit，不进入核心 Recall/MRR。
- `HardNegativeAboveExpectedRate`：如果任意 hard negative 排名高于所有 expected，则记为一次 hard-negative failure。

延迟指标：

- `embeddingGenerationLatencyMs`
- `retrievalRankingLatencyMs`
- `endToEndLatencyMs`
- `embeddingCacheHit`

## Dev 选择

Dev-selected configuration：

- `corpusVersion = v0.3`
- `benchmarkMode = GLOBAL`
- `useRetrievalText = true`
- `bm25Weight = 0.7`
- `embeddingWeight = 0.3`
- `rrfK = 60`
- `embedding model = text-embedding-3-small`
- heuristic reranker：final strategy 关闭

Dev 选择依据：

- BM25 baseline：`Recall@1 = 0.675`，`Recall@3 = 0.875`，`Recall@5 = 0.900`，`MRR = 0.7771`，`HardNegativeAboveExpectedRate = 0.2857`
- Final Weighted Hybrid：`Recall@1 = 0.750`，`Recall@3 = 0.850`，`Recall@5 = 0.875`，`MRR = 0.8157`，`HardNegativeAboveExpectedRate = 0.2000`
- 预先选择优先级：`MRR > Recall@1 > HardNegative > Recall@3 > latency`

## Final Held-Out Test 真实结果

报告文件：

- `agent-service/benchmark-reports/v0.5-final-test/retrieval_benchmark_report.json`
- `agent-service/benchmark-reports/v0.5-final-test/retrieval_benchmark_report.md`
- `agent-service/benchmark-reports/v0.5-final-test/miss-analysis.json`
- `agent-service/benchmark-reports/v0.5-final-test/miss-analysis.md`

配置：

- Dataset version：`video-diagnosis-rag-test-v0.5`
- Corpus version：`v0.3`
- Verified sample count：20
- Corpus size：34
- Benchmark mode：`GLOBAL`
- Embedding provider：`openai`
- Embedding model：`text-embedding-3-small`
- Embedding dimension：1536
- `testUsedForTuning = false`

总体结果：

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected |
|---|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.4500 | 0.7500 | 0.8500 | 0.6185 | 0.2000 |
| EMBEDDING_ONLY | 0.5000 | 0.7500 | 0.8000 | 0.6375 | 0.2500 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.6000 | 0.8500 | 0.9000 | 0.7363 | 0.1500 |
| FINAL_WEIGHTED_HYBRID | 0.5000 | 0.8000 | 0.9000 | 0.6808 | 0.1500 |

诚实结论：

- Dev 选出的 `0.7 BM25 / 0.3 Embedding` 在 test 上没有超过 `0.5/0.5 Hybrid`。
- `0.5/0.5 Hybrid` 在 held-out test 上整体最好：`Recall@1 = 0.6000`，`MRR = 0.7363`。
- Final Weighted Hybrid 仍比 BM25 baseline 有更高 `Recall@1/MRR/Recall@5`，但不是 test 最优。
- 不能把这段包装成“调参必然提升”，应该讲成一次有 dev/test 纪律的真实实验。

## 分组结果重点

Final Weighted Hybrid by skill：

| Skill | Recall@1 | Recall@3 | Recall@5 | MRR | HardNeg |
|---|---:|---:|---:|---:|---:|
| hook_analysis | 0.2500 | 0.6250 | 0.7500 | 0.4833 | 0.3750 |
| structure_rhythm_analysis | 0.3333 | 0.8333 | 1.0000 | 0.6250 | 0.0000 |
| value_delivery_analysis | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |

说明：

- hook 类 query 最难，容易和 value 类知识混淆。
- value 类在 test split 上更容易，结果很好但样本只有 6 条，不能过度泛化。
- structure 类 Recall@5 已满，但 Top1 仍有提升空间。

## Miss Analysis

Top recurring confused pairs：

- `hook-bad-case-feature-first-v1 -> value-bad-case-feature-without-benefit-v1`：2 次。
- `hook-good-case-authority-fast-v1 -> hook-pattern-self-intro-delay-v1`：1 次。
- `hook-rule-first-three-seconds-v1 -> hook-bad-case-generic-opening-v1`：1 次。
- `hook-pattern-curiosity-gap-v1 -> hook-rule-first-three-seconds-v1`：1 次。
- `hook-pattern-pain-benefit-v2 -> value-bad-case-feature-without-benefit-v1`：1 次。
- `structure-rule-slow-burn-exception-v1 -> hook-rule-avoid-late-payoff-v1`：1 次。

错误类型统计：

- `CROSS_SKILL_CONTAMINATION`：4
- `HARD_NEGATIVE_CONFUSION`：6
- `LEXICAL_MISMATCH`：1
- `MULTI_LABEL_AMBIGUITY`：2
- `SEMANTIC_BOUNDARY_CONFUSION`：3
- `UNKNOWN`：4

可讲结论：

- 检索难点不是简单 TopK 命中，而是相似边界区分。
- Hard negative 指标比普通 Recall@5 更能暴露问题。
- Hook/value 边界仍然需要改进 query rewriting、skill-aware retrieval 或更强 rerank。

## Agent Ablation 框架

文件：`agent-service/src/agent_service/retrieval/benchmark.py`

当前已建立 Agent Ablation 的数据结构和指标计算：

- `VIDEO_EVIDENCE_ONLY`
- `RAG`
- `LOCAL_REACT`
- `EVALUATOR`

指标：

- Finding Precision
- Finding Recall
- Finding F1
- Evidence Grounding Rate
- Unsupported Finding Rate

限制：

- Golden Finding 需要人工标注。
- 没有让 LLM 自己生成 ground truth。
- 当前重点还是 retrieval benchmark，不要夸成完整 Agent eval 平台。

