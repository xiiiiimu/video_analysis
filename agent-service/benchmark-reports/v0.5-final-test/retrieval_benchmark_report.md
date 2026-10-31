# Video Diagnosis RAG Retrieval Benchmark

- Dataset version: `video-diagnosis-rag-test-v0.5`
- Corpus version: `v0.3`
- Verified sample count: `20`
- Corpus size: `34`
- Benchmark mode: `GLOBAL`
- Candidate pool: `{"candidatePoolMin": 34.0, "candidatePoolMedian": 34.0, "candidatePoolMax": 34.0}`
- Model: `in_memory_bm25_embedding_benchmark`
- Embedding provider: `openai`
- Embedding model: `text-embedding-3-small`
- Embedding dimension: `1536`
- Run started at: `2026-09-11T15:40:41Z`
- Run finished at: `2026-09-11T15:41:01Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF_05_05", "FINAL_WEIGHTED_HYBRID"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "useRetrievalText": true, "weightedRrf": {"bm25Weight": 0.7, "embeddingWeight": 0.3, "rrfK": 60}, "corpusEmbeddingMode": "precomputed_at_runner_init", "queryEmbeddingCache": "enabled_per_runner", "embeddingLatencyIncludedInEndToEnd": true, "rerankEnabled": false, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default.", "datasetSplit": "TEST", "selectionSource": "DEV", "devSelectedBm25Weight": 0.7, "devSelectedEmbeddingWeight": 0.3, "testUsedForTuning": false, "heuristicRerankerFinalStrategy": false}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1", "reportMetadata": {"datasetSplit": "TEST", "selectionSource": "DEV", "devSelectedBm25Weight": 0.7, "devSelectedEmbeddingWeight": 0.3, "testUsedForTuning": false, "heuristicRerankerFinalStrategy": false}}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.4500 | 0.7500 | 0.8500 | 0.6185 | 0.2000 | 5.914 | 5.994 | 7.045 |
| EMBEDDING_ONLY | 0.5000 | 0.7500 | 0.8000 | 0.6375 | 0.2500 | 943.502 | 674.463 | 1995.146 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.6000 | 0.8500 | 0.9000 | 0.7363 | 0.1500 | 17.709 | 17.938 | 19.000 |
| FINAL_WEIGHTED_HYBRID | 0.5000 | 0.8000 | 0.9000 | 0.6808 | 0.1500 | 19.005 | 18.625 | 21.526 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.1250 | 0.6250 | 0.7500 | 0.3762 | 0.5000 | 5.365 | 5.410 | 6.957 |
| EMBEDDING_ONLY | 0.5000 | 0.5000 | 0.6250 | 0.5312 | 0.5000 | 1181.516 | 924.302 | 2113.584 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.3750 | 0.6250 | 0.7500 | 0.5491 | 0.3750 | 16.662 | 17.473 | 17.979 |
| FINAL_WEIGHTED_HYBRID | 0.2500 | 0.6250 | 0.7500 | 0.4833 | 0.3750 | 18.859 | 18.372 | 21.238 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.3333 | 0.6667 | 0.8333 | 0.5602 | 0.0000 | 6.214 | 5.994 | 6.937 |
| EMBEDDING_ONLY | 0.3333 | 0.8333 | 0.8333 | 0.5833 | 0.1667 | 930.462 | 693.845 | 1501.560 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.5000 | 1.0000 | 1.0000 | 0.7222 | 0.0000 | 18.235 | 18.340 | 18.745 |
| FINAL_WEIGHTED_HYBRID | 0.3333 | 0.8333 | 1.0000 | 0.6250 | 0.0000 | 19.343 | 19.294 | 20.282 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 6.344 | 6.283 | 7.190 |
| EMBEDDING_ONLY | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.0000 | 639.189 | 635.799 | 676.304 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 18.581 | 18.547 | 19.210 |
| FINAL_WEIGHTED_HYBRID | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 18.863 | 18.578 | 20.847 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.3333 | 0.6667 | 1.0000 | 0.5278 | 0.3333 | 6.747 | 6.996 | 7.297 |
| EMBEDDING_ONLY | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 690.070 | 666.643 | 786.355 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 18.219 | 18.383 | 18.710 |
| FINAL_WEIGHTED_HYBRID | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.0000 | 18.079 | 18.365 | 18.421 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.3333 | 1.0000 | 1.0000 | 0.6667 | 0.0000 | 6.200 | 6.024 | 6.797 |
| EMBEDDING_ONLY | 0.3333 | 1.0000 | 1.0000 | 0.6111 | 0.0000 | 592.970 | 583.879 | 622.271 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.0000 | 18.564 | 18.728 | 19.229 |
| FINAL_WEIGHTED_HYBRID | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.0000 | 18.920 | 18.538 | 20.175 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6250 | 0.8750 | 1.0000 | 0.7750 | 0.2500 | 5.737 | 5.709 | 6.730 |
| EMBEDDING_ONLY | 0.2500 | 0.5000 | 0.6250 | 0.4271 | 0.5000 | 942.781 | 662.984 | 1795.114 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.5000 | 0.7500 | 0.8750 | 0.6741 | 0.2500 | 17.924 | 17.883 | 18.901 |
| FINAL_WEIGHTED_HYBRID | 0.5000 | 0.8750 | 0.8750 | 0.7083 | 0.2500 | 19.361 | 18.747 | 21.749 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.3333 | 0.5000 | 0.5000 | 0.4312 | 0.1667 | 5.589 | 5.859 | 6.874 |
| EMBEDDING_ONLY | 0.6667 | 0.8333 | 0.8333 | 0.7500 | 0.1667 | 1246.446 | 1191.374 | 2017.362 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.5000 | 0.8333 | 0.8333 | 0.6389 | 0.1667 | 16.741 | 17.800 | 18.210 |
| FINAL_WEIGHTED_HYBRID | 0.3333 | 0.5000 | 0.8333 | 0.4917 | 0.1667 | 19.037 | 18.767 | 20.055 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.3333 | 1.0000 | 1.0000 | 0.6667 | 0.0000 | 6.200 | 6.024 | 6.797 |
| EMBEDDING_ONLY | 0.3333 | 1.0000 | 1.0000 | 0.6111 | 0.0000 | 592.970 | 583.879 | 622.271 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.0000 | 18.564 | 18.728 | 19.229 |
| FINAL_WEIGHTED_HYBRID | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.0000 | 18.920 | 18.538 | 20.175 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.4444 | 0.7778 | 0.8889 | 0.6177 | 0.2222 | 5.767 | 5.914 | 7.197 |
| EMBEDDING_ONLY | 0.6667 | 0.8889 | 1.0000 | 0.8056 | 0.1111 | 981.366 | 799.656 | 1886.387 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.7778 | 1.0000 | 1.0000 | 0.8889 | 0.1111 | 17.254 | 17.843 | 18.732 |
| FINAL_WEIGHTED_HYBRID | 0.5556 | 0.8889 | 1.0000 | 0.7444 | 0.1111 | 18.910 | 18.630 | 20.923 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5000 | 0.6250 | 0.7500 | 0.6014 | 0.2500 | 5.971 | 6.209 | 6.939 |
| EMBEDDING_ONLY | 0.3750 | 0.5000 | 0.5000 | 0.4583 | 0.5000 | 1032.355 | 695.913 | 1822.929 |
| HYBRID_BM25_EMBEDDING_RRF_05_05 | 0.3750 | 0.6250 | 0.7500 | 0.5283 | 0.2500 | 17.901 | 17.980 | 18.901 |
| FINAL_WEIGHTED_HYBRID | 0.3750 | 0.6250 | 0.7500 | 0.5521 | 0.2500 | 19.145 | 18.737 | 21.241 |


## Recall@5 Miss Analysis

- `v03-hook-001` `BM25_ONLY` query=开头一直讲自己做账号三年，第四秒才说粉丝能少踩什么坑 expected=['hook-pattern-self-intro-delay-v1'] hardNegative=['hook-good-case-authority-fast-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.7745966692414834}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.6115928396627265}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.5734623443633283}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.4788521306805733}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.43852900965351466}]
- `v03-hook-013` `BM25_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0801234497346432}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.7088812050083358}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.6139406135149205}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.6115928396627265}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.4915391523114243}]
- `v03-structure-012` `BM25_ONLY` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.8451542547285166}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.7863336509949341}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.693687975619296}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.6553855364152325}, {'knowledgeId': 'structure-good-case-example-driven-v1', 'score': 0.5640760748177662}]
- `v03-hook-002` `EMBEDDING_ONLY` query=第一句说自己是营养师，下一句马上告诉宝妈怎么避开配料表陷阱 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.28227679977799053}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.2789453480272453}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.278586927348559}, {'knowledgeId': 'structure-good-case-example-driven-v1', 'score': 0.2545519679263142}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.2516981248645664}]
- `v03-hook-006` `EMBEDDING_ONLY` query=首屏没有明确谁该看、为什么看，也没有冲突点 expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] actualTop5=[{'knowledgeId': 'hook-platform-short-feed-v1', 'score': 0.4154181066066938}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.4094230304208077}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.40360467499462777}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.4031631263508801}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4018182520803491}]
- `v03-hook-013` `EMBEDDING_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.38656511685739037}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.35209716602738605}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.34207284968650126}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.30964202679530534}, {'knowledgeId': 'structure-bad-case-static-talking-v1', 'score': 0.30690742787686937}]
- `v03-structure-007` `EMBEDDING_ONLY` query=故事开头收益不明显，但人物冲突一直在升级，所以不一定要立刻收束 expected=['structure-rule-slow-burn-exception-v1'] hardNegative=['hook-rule-avoid-late-payoff-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4184600684985762}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.4037981838663323}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.3993639314247284}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.39279523799092203}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.39216183213722805}]
- `v03-hook-006` `HYBRID_BM25_EMBEDDING_RRF_05_05` query=首屏没有明确谁该看、为什么看，也没有冲突点 expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.015877016129032258}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.015640273704789834}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015549662487945998}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015512265512265512}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015504807692307693}]
- `v03-hook-013` `HYBRID_BM25_EMBEDDING_RRF_05_05` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015772478887232988}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.01562881562881563}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015549662487945998}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.015527202696196438}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015399194503672116}]
- `v03-hook-006` `FINAL_WEIGHTED_HYBRID` query=首屏没有明确谁该看、为什么看，也没有冲突点 expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.01597782258064516}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015887174541947928}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015656565656565653}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015552884615384614}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.01544477028347996}]
- `v03-hook-013` `FINAL_WEIGHTED_HYBRID` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015887174541947928}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015588723051409618}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.01553113553113553}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.01552409339294585}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.015286470871449204}]
