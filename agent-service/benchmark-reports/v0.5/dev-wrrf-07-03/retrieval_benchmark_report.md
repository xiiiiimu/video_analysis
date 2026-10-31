# Video Diagnosis RAG Retrieval Benchmark

- Dataset version: `video-diagnosis-rag-dev-v0.5`
- Corpus version: `v0.3`
- Verified sample count: `40`
- Corpus size: `34`
- Benchmark mode: `GLOBAL`
- Candidate pool: `{"candidatePoolMin": 34.0, "candidatePoolMedian": 34.0, "candidatePoolMax": 34.0}`
- Model: `in_memory_bm25_embedding_benchmark`
- Embedding provider: `openai`
- Embedding model: `text-embedding-3-small`
- Embedding dimension: `1536`
- Run started at: `2026-09-11T15:21:23Z`
- Run finished at: `2026-09-11T15:22:30Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "useRetrievalText": true, "weightedRrf": {"bm25Weight": 0.7, "embeddingWeight": 0.3, "rrfK": 60}, "corpusEmbeddingMode": "precomputed_at_runner_init", "queryEmbeddingCache": "enabled_per_runner", "embeddingLatencyIncludedInEndToEnd": true, "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6750 | 0.8750 | 0.9000 | 0.7771 | 0.2857 | 3.991 | 3.993 | 5.129 |
| EMBEDDING_ONLY | 0.5500 | 0.8250 | 0.8750 | 0.6948 | 0.2571 | 1643.168 | 1034.782 | 1585.241 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.8500 | 0.8750 | 0.8157 | 0.2000 | 21.073 | 21.325 | 22.786 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.8750 | 0.9000 | 0.7449 | 0.2857 | 23.713 | 23.649 | 27.566 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5000 | 0.7500 | 0.7500 | 0.6111 | 0.4000 | 3.335 | 3.325 | 4.279 |
| EMBEDDING_ONLY | 0.4167 | 0.7500 | 0.7500 | 0.5938 | 0.2000 | 813.113 | 711.704 | 1517.656 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.7500 | 0.7500 | 0.7583 | 0.2000 | 21.029 | 21.516 | 23.559 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.7500 | 0.7500 | 0.6333 | 0.3000 | 24.806 | 24.040 | 27.733 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 3.878 | 3.676 | 4.918 |
| EMBEDDING_ONLY | 0.6429 | 0.9286 | 1.0000 | 0.7798 | 0.2500 | 2876.558 | 1073.790 | 10089.168 |
| HYBRID_BM25_EMBEDDING_RRF | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 21.502 | 21.636 | 22.258 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7857 | 1.0000 | 1.0000 | 0.8929 | 0.1667 | 25.036 | 24.793 | 27.396 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5714 | 0.8571 | 0.9286 | 0.7321 | 0.3846 | 4.666 | 4.558 | 5.314 |
| EMBEDDING_ONLY | 0.5714 | 0.7857 | 0.8571 | 0.6964 | 0.3077 | 1121.252 | 1141.130 | 1427.182 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5714 | 0.7857 | 0.8571 | 0.7163 | 0.3077 | 20.681 | 20.610 | 22.511 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8571 | 0.9286 | 0.6925 | 0.3846 | 21.453 | 21.303 | 22.601 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 1.0000 | 0.8426 | 0.3333 | 4.324 | 4.571 | 5.024 |
| EMBEDDING_ONLY | 0.5556 | 0.8889 | 1.0000 | 0.7315 | 0.5000 | 979.516 | 919.719 | 1360.658 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8889 | 1.0000 | 0.8611 | 0.1667 | 20.956 | 21.374 | 22.578 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 1.0000 | 0.7500 | 0.5000 | 23.960 | 23.702 | 26.900 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5556 | 0.8889 | 0.8889 | 0.7222 | 0.2500 | 4.023 | 4.176 | 5.119 |
| EMBEDDING_ONLY | 0.6667 | 0.7778 | 0.7778 | 0.7361 | 0.1250 | 972.092 | 1043.289 | 1332.197 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8889 | 0.8889 | 0.8457 | 0.2500 | 20.851 | 20.984 | 22.374 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 0.8889 | 0.7160 | 0.2500 | 23.101 | 23.601 | 25.202 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 3.970 | 3.556 | 5.246 |
| EMBEDDING_ONLY | 0.4000 | 0.7000 | 0.8000 | 0.5750 | 0.4444 | 1139.110 | 1177.042 | 1569.956 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7000 | 0.8000 | 0.8000 | 0.7667 | 0.3333 | 21.162 | 21.497 | 22.404 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 24.025 | 23.468 | 28.030 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.8333 | 0.8333 | 0.7917 | 0.1667 | 3.734 | 3.631 | 4.537 |
| EMBEDDING_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.0833 | 3064.260 | 1034.782 | 12471.581 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.8333 | 0.8333 | 0.8000 | 0.0833 | 21.252 | 21.310 | 23.658 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8333 | 0.8333 | 0.7583 | 0.0833 | 23.728 | 23.626 | 27.058 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 3.579 | 3.503 | 4.458 |
| EMBEDDING_ONLY | 0.6000 | 0.8000 | 0.8000 | 0.6917 | 0.0000 | 928.721 | 1043.289 | 1349.572 |
| HYBRID_BM25_EMBEDDING_RRF | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 20.738 | 21.311 | 22.527 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 23.151 | 23.601 | 25.352 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5882 | 0.8235 | 0.8824 | 0.7108 | 0.4615 | 4.196 | 4.497 | 5.290 |
| EMBEDDING_ONLY | 0.4706 | 0.7647 | 0.8235 | 0.6324 | 0.3846 | 1013.073 | 959.885 | 1485.699 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6471 | 0.7647 | 0.8235 | 0.7428 | 0.3077 | 20.860 | 21.218 | 22.099 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5294 | 0.8235 | 0.8824 | 0.7036 | 0.4615 | 23.564 | 23.133 | 26.996 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.2353 | 3.911 | 3.819 | 4.930 |
| EMBEDDING_ONLY | 0.6111 | 0.8889 | 0.9444 | 0.7546 | 0.2353 | 2436.714 | 1034.782 | 5261.028 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.1765 | 21.366 | 21.357 | 23.151 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8889 | 0.8889 | 0.7685 | 0.2353 | 24.010 | 23.947 | 27.702 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.6989632453288304}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.6943650748294136}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.6379930845075023}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.5595028849441883}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5449492609130661}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.0405319634289438}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9011551125709446}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8486684247915055}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.6316761657092368}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.5916079783099616}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.1874645015519594}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.1677484162422844}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.9662823901213162}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.9215455665108366}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.9135002783911397}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.8333333333333334}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.8137884587711595}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.7474350927519359}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.6761234037828132}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.5499719409228703}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.4474281415807856}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.41238219663161335}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.3918800297196462}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.3749681738294638}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.36951460484976517}]
- `v03-hook-008` `EMBEDDING_ONLY` query=开场第一句话点名新手妈妈，但后面还要马上接具体困扰 expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.44515143278815733}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.44000267190734194}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.4391182640103162}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.4131545638137728}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.3391743799679147}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.42275087669904676}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3617870419303066}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.3598549908300786}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3349447241957647}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.3275932093399742}]
- `v03-value-012` `EMBEDDING_ONLY` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5230120415826781}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.37992218906987174}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.37915205143743064}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3715077190185666}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3600430522787104}]
- `v03-value-014` `EMBEDDING_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.40046749368601126}, {'knowledgeId': 'value-good-case-step-by-step-v1', 'score': 0.39763000436156587}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.39738797401653825}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.3914661257159941}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.38820208402131934}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.016393442622950817}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015835777126099706}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015286470871449204}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.015223214285714284}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.014994582881906825}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.01631411951348493}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.016208355367530406}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.01569940476190476}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015588723051409618}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.015456730769230768}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.016208355367530406}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.015873015873015872}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.015475409836065573}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.015349264705882352}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015063145809414464}]
- `v03-value-012` `HYBRID_BM25_EMBEDDING_RRF` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.016393442622950817}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015776209677419356}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015396825396825395}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015293560606060606}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.01520966595593461}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.016208355367530406}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.016162909836065574}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.01553113553113553}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.015277777777777776}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.014795587280986372}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.381964809384164}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3794314512953774}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2327868852459016}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0803791982665223}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.931159486744465}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8327075621364355}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.712337387625595}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6812137230514095}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3815724206349205}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1108413461538462}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.282601797990481}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.1313484257090813}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9820020481310803}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9809742647058823}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8291365241748871}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5626017979904814}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.53229194209413}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.5309027777777777}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.259839015151515}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.1092080468551058}]
