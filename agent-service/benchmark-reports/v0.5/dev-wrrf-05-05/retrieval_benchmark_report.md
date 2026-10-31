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
- Run started at: `2026-09-11T15:24:04Z`
- Run finished at: `2026-09-11T15:24:42Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "useRetrievalText": true, "weightedRrf": {"bm25Weight": 0.5, "embeddingWeight": 0.5, "rrfK": 60}, "corpusEmbeddingMode": "precomputed_at_runner_init", "queryEmbeddingCache": "enabled_per_runner", "embeddingLatencyIncludedInEndToEnd": true, "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6750 | 0.8750 | 0.9000 | 0.7771 | 0.2857 | 4.391 | 4.554 | 5.239 |
| EMBEDDING_ONLY | 0.5500 | 0.8250 | 0.8750 | 0.6948 | 0.2571 | 927.257 | 779.178 | 1697.855 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7250 | 0.8500 | 0.8750 | 0.8045 | 0.2000 | 12.229 | 12.711 | 14.689 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.8750 | 0.9000 | 0.7449 | 0.2857 | 17.073 | 16.988 | 17.996 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5000 | 0.7500 | 0.7500 | 0.6111 | 0.4000 | 3.565 | 3.579 | 3.940 |
| EMBEDDING_ONLY | 0.4167 | 0.7500 | 0.7500 | 0.5938 | 0.2000 | 951.304 | 750.735 | 1733.836 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.6667 | 0.7500 | 0.6994 | 0.2000 | 9.759 | 9.786 | 11.868 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.7500 | 0.7500 | 0.6333 | 0.3000 | 17.632 | 17.599 | 18.175 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 4.461 | 4.598 | 5.011 |
| EMBEDDING_ONLY | 0.6429 | 0.9286 | 1.0000 | 0.7798 | 0.2500 | 858.539 | 763.986 | 1383.024 |
| HYBRID_BM25_EMBEDDING_RRF | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 12.569 | 12.641 | 13.280 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7857 | 1.0000 | 1.0000 | 0.8929 | 0.1667 | 16.931 | 16.811 | 17.649 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5714 | 0.8571 | 0.9286 | 0.7321 | 0.3846 | 5.028 | 4.947 | 5.868 |
| EMBEDDING_ONLY | 0.5714 | 0.7857 | 0.8571 | 0.6964 | 0.3077 | 975.362 | 864.481 | 1627.086 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5714 | 0.8571 | 0.8571 | 0.7347 | 0.3077 | 14.005 | 13.914 | 14.835 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8571 | 0.9286 | 0.6925 | 0.3846 | 16.735 | 16.730 | 17.187 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 1.0000 | 0.8426 | 0.3333 | 4.481 | 4.635 | 5.055 |
| EMBEDDING_ONLY | 0.5556 | 0.8889 | 1.0000 | 0.7315 | 0.5000 | 1088.032 | 977.642 | 1762.670 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 1.0000 | 1.0000 | 0.8889 | 0.1667 | 12.686 | 13.202 | 14.017 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 1.0000 | 0.7500 | 0.5000 | 17.357 | 17.465 | 17.942 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5556 | 0.8889 | 0.8889 | 0.7222 | 0.2500 | 4.555 | 4.745 | 5.223 |
| EMBEDDING_ONLY | 0.6667 | 0.7778 | 0.7778 | 0.7361 | 0.1250 | 777.838 | 745.220 | 1118.898 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.7778 | 0.8889 | 0.7659 | 0.2500 | 12.249 | 13.143 | 14.440 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 0.8889 | 0.7160 | 0.2500 | 17.054 | 17.003 | 17.830 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 4.244 | 4.152 | 5.238 |
| EMBEDDING_ONLY | 0.4000 | 0.7000 | 0.8000 | 0.5750 | 0.4444 | 849.902 | 726.757 | 1495.611 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7000 | 0.8000 | 0.8000 | 0.7643 | 0.3333 | 12.241 | 12.274 | 14.885 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 16.908 | 16.848 | 17.624 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.8333 | 0.8333 | 0.7917 | 0.1667 | 4.321 | 4.227 | 5.752 |
| EMBEDDING_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.0833 | 983.202 | 895.408 | 1651.787 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.8333 | 0.8333 | 0.8036 | 0.0833 | 11.860 | 12.390 | 13.783 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8333 | 0.8333 | 0.7583 | 0.0833 | 17.010 | 16.810 | 18.112 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 4.378 | 4.612 | 5.208 |
| EMBEDDING_ONLY | 0.6000 | 0.8000 | 0.8000 | 0.6917 | 0.0000 | 763.988 | 706.281 | 1187.668 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8000 | 0.8000 | 1.0000 | 0.8500 | 0.0000 | 11.315 | 11.964 | 14.452 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 17.123 | 16.974 | 17.953 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5882 | 0.8235 | 0.8824 | 0.7108 | 0.4615 | 4.337 | 4.666 | 5.185 |
| EMBEDDING_ONLY | 0.4706 | 0.7647 | 0.8235 | 0.6324 | 0.3846 | 976.208 | 753.066 | 1642.822 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6471 | 0.8235 | 0.8235 | 0.7521 | 0.3077 | 12.374 | 12.583 | 14.383 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5294 | 0.8235 | 0.8824 | 0.7036 | 0.4615 | 17.104 | 17.035 | 18.052 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.2353 | 4.445 | 4.516 | 5.440 |
| EMBEDDING_ONLY | 0.6111 | 0.8889 | 0.9444 | 0.7546 | 0.2353 | 926.377 | 845.202 | 1722.517 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8889 | 0.8889 | 0.8413 | 0.1765 | 12.346 | 12.867 | 14.173 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8889 | 0.8889 | 0.7685 | 0.2353 | 17.029 | 16.941 | 17.753 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.6989632453288304}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.6943650748294136}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.6379930845075023}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.5595028849441883}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5449492609130661}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.0405319634289438}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9011551125709446}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8486684247915055}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.6316761657092368}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.5916079783099616}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.1874645015519594}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.1677484162422844}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.9662823901213162}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.9215455665108366}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.9135002783911397}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.8333333333333334}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.8137884587711595}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.7474350927519359}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.6761234037828132}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.5499719409228703}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.4474259274184908}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.412380043342796}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.391435416244097}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.374910869921816}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.3695049618531465}]
- `v03-hook-008` `EMBEDDING_ONLY` query=开场第一句话点名新手妈妈，但后面还要马上接具体困扰 expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4451446049840928}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.4402809516329178}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.43882396380950944}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.4131800326199664}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.33932407031893336}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.42271634439980904}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.361846378609876}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.35987884794284036}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.33513681144787044}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.3280984013250289}]
- `v03-value-012` `EMBEDDING_ONLY` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5229764990826943}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.38029014096636293}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.3791570833823853}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.37151292737607305}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3594964568398064}]
- `v03-value-014` `EMBEDDING_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.3989479756337441}, {'knowledgeId': 'value-good-case-step-by-step-v1', 'score': 0.39764265212884686}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.3970330743435612}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.3914895955697113}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.38808400457875586}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.01639344262295082}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015640273704789834}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015527202696196438}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.01518288474810214}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.015165441176470588}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.015749007936507936}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.015504807692307693}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015399194503672116}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.015873015873015872}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.015165441176470588}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015154994259471873}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.014863387978142076}]
- `v03-value-012` `HYBRID_BM25_EMBEDDING_RRF` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.01639344262295082}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015877016129032258}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015399194503672116}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015388257575757576}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.014978761457634698}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.016009221311475412}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.01562881562881563}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.01488095238095238}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.014835164835164835}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3817693059628542}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3780451113643035}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2327868852459016}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0796599343477629}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.9314002185692123}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8326546800634584}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.7123902696985722}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6807838098882875}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3816220238095236}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1111298076923077}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2826546800634584}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.1302480033627575}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9820020481310803}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9810384570494863}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8286749482401654}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5626546800634586}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.5321382535695398}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.5305059523809523}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.2585552536231885}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.1087751464222053}]
