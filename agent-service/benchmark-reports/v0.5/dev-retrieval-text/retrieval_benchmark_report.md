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
- Run started at: `2026-09-11T15:19:07Z`
- Run finished at: `2026-09-11T15:19:48Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "useRetrievalText": true, "weightedRrf": {"bm25Weight": 0.5, "embeddingWeight": 0.5, "rrfK": 60}, "corpusEmbeddingMode": "precomputed_at_runner_init", "queryEmbeddingCache": "enabled_per_runner", "embeddingLatencyIncludedInEndToEnd": true, "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6750 | 0.8750 | 0.9000 | 0.7771 | 0.2857 | 11.191 | 10.432 | 18.011 |
| EMBEDDING_ONLY | 0.5500 | 0.8250 | 0.8750 | 0.6948 | 0.2571 | 986.201 | 805.158 | 1996.634 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7250 | 0.8500 | 0.8750 | 0.8045 | 0.2000 | 12.217 | 13.265 | 14.109 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.8750 | 0.9000 | 0.7449 | 0.2857 | 16.917 | 16.972 | 17.341 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5000 | 0.7500 | 0.7500 | 0.6111 | 0.4000 | 13.371 | 11.831 | 18.613 |
| EMBEDDING_ONLY | 0.4167 | 0.7500 | 0.7500 | 0.5938 | 0.2000 | 970.703 | 815.693 | 1850.170 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.6667 | 0.7500 | 0.6994 | 0.2000 | 9.570 | 9.681 | 11.469 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.7500 | 0.7500 | 0.6333 | 0.3000 | 16.913 | 16.984 | 17.273 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 10.870 | 10.266 | 14.590 |
| EMBEDDING_ONLY | 0.6429 | 0.9286 | 1.0000 | 0.7798 | 0.2500 | 1111.412 | 858.632 | 2126.140 |
| HYBRID_BM25_EMBEDDING_RRF | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 13.055 | 13.414 | 14.111 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7857 | 1.0000 | 1.0000 | 0.8929 | 0.1667 | 16.996 | 17.013 | 17.667 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5714 | 0.8571 | 0.9286 | 0.7321 | 0.3846 | 9.642 | 9.062 | 12.630 |
| EMBEDDING_ONLY | 0.5714 | 0.7857 | 0.8571 | 0.6964 | 0.3077 | 874.276 | 781.809 | 1361.696 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5714 | 0.8571 | 0.8571 | 0.7347 | 0.3077 | 13.647 | 13.640 | 14.074 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8571 | 0.9286 | 0.6925 | 0.3846 | 16.841 | 16.924 | 17.219 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 1.0000 | 0.8426 | 0.3333 | 11.889 | 11.127 | 18.262 |
| EMBEDDING_ONLY | 0.5556 | 0.8889 | 1.0000 | 0.7315 | 0.5000 | 1077.900 | 791.043 | 2106.925 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 1.0000 | 1.0000 | 0.8889 | 0.1667 | 12.806 | 13.467 | 14.087 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 1.0000 | 0.7500 | 0.5000 | 16.996 | 17.138 | 17.468 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5556 | 0.8889 | 0.8889 | 0.7222 | 0.2500 | 10.483 | 10.381 | 13.026 |
| EMBEDDING_ONLY | 0.6667 | 0.7778 | 0.7778 | 0.7361 | 0.1250 | 1061.049 | 809.670 | 2067.786 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.7778 | 0.8889 | 0.7659 | 0.2500 | 12.380 | 13.582 | 14.095 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 0.8889 | 0.7160 | 0.2500 | 16.798 | 16.942 | 17.074 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 11.462 | 11.451 | 14.757 |
| EMBEDDING_ONLY | 0.4000 | 0.7000 | 0.8000 | 0.5750 | 0.4444 | 766.614 | 773.761 | 1036.561 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7000 | 0.8000 | 0.8000 | 0.7643 | 0.3333 | 11.872 | 12.249 | 13.858 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 17.035 | 17.065 | 17.576 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.8333 | 0.8333 | 0.7917 | 0.1667 | 10.971 | 9.935 | 16.305 |
| EMBEDDING_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.0833 | 1044.281 | 988.171 | 1728.762 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.8333 | 0.8333 | 0.8036 | 0.0833 | 11.939 | 12.649 | 14.072 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8333 | 0.8333 | 0.7583 | 0.0833 | 16.848 | 16.939 | 17.208 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 10.935 | 10.810 | 13.370 |
| EMBEDDING_ONLY | 0.6000 | 0.8000 | 0.8000 | 0.6917 | 0.0000 | 854.552 | 756.702 | 1216.626 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8000 | 0.8000 | 1.0000 | 0.8500 | 0.0000 | 11.184 | 12.526 | 13.657 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 16.841 | 16.963 | 17.003 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5882 | 0.8235 | 0.8824 | 0.7108 | 0.4615 | 11.610 | 10.484 | 18.155 |
| EMBEDDING_ONLY | 0.4706 | 0.7647 | 0.8235 | 0.6324 | 0.3846 | 1090.696 | 759.555 | 2316.068 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6471 | 0.8235 | 0.8235 | 0.7521 | 0.3077 | 12.300 | 13.088 | 14.078 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5294 | 0.8235 | 0.8824 | 0.7036 | 0.4615 | 16.937 | 16.995 | 17.376 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.2353 | 10.865 | 9.838 | 14.879 |
| EMBEDDING_ONLY | 0.6111 | 0.8889 | 0.9444 | 0.7546 | 0.2353 | 924.081 | 871.924 | 1485.653 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8889 | 0.8889 | 0.8413 | 0.1765 | 12.425 | 13.298 | 14.112 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8889 | 0.8889 | 0.7685 | 0.2353 | 16.919 | 16.980 | 17.346 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.6989632453288304}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.6943650748294136}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.6379930845075023}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.5595028849441883}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5449492609130661}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.0405319634289438}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9011551125709446}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8486684247915055}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.6316761657092368}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.5916079783099616}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.1874645015519594}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.1677484162422844}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.9662823901213162}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.9215455665108366}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.9135002783911397}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.8333333333333334}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.8137884587711595}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.7474350927519359}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.6761234037828132}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.5499719409228703}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.4474281415807856}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.41238219663161335}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.3918800297196462}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.3749681738294638}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.36951460484976517}]
- `v03-hook-008` `EMBEDDING_ONLY` query=开场第一句话点名新手妈妈，但后面还要马上接具体困扰 expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4451270907276547}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.4400106428606835}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.43912589802028507}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.41317648548117525}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.33911530390153716}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.42275087669904676}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3617870419303066}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.3598549908300786}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3349447241957647}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.3275932093399742}]
- `v03-value-012` `EMBEDDING_ONLY` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5230120415826781}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.37992218906987174}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.37915205143743064}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3715077190185666}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3600430522787104}]
- `v03-value-014` `EMBEDDING_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.40046749368601126}, {'knowledgeId': 'value-good-case-step-by-step-v1', 'score': 0.39763000436156587}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.39738797401653825}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.3914661257159941}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.38820208402131934}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.01639344262295082}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015640273704789834}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015527202696196438}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.01518288474810214}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.015165441176470588}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.015749007936507936}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.015504807692307693}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015399194503672116}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.015873015873015872}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.015165441176470588}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015154994259471873}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.014863387978142076}]
- `v03-value-012` `HYBRID_BM25_EMBEDDING_RRF` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.01639344262295082}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015877016129032258}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015399194503672116}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015388257575757576}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015079365079365078}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.016009221311475412}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.01562881562881563}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.01488095238095238}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.014835164835164835}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3817693059628542}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3780451113643035}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2327868852459016}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0796599343477629}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.9314002185692123}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8326546800634584}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.7123902696985722}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6807838098882875}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3816220238095236}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1111298076923077}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2826546800634584}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.1302480033627575}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9820020481310803}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9810384570494863}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8286749482401654}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5626546800634586}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.5321382535695398}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.5305059523809523}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.2585552536231885}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.1087751464222053}]
