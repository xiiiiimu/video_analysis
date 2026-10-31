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
- Run started at: `2026-09-11T15:17:20Z`
- Run finished at: `2026-09-11T15:17:58Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "useRetrievalText": false, "weightedRrf": {"bm25Weight": 0.5, "embeddingWeight": 0.5, "rrfK": 60}, "corpusEmbeddingMode": "precomputed_at_runner_init", "queryEmbeddingCache": "enabled_per_runner", "embeddingLatencyIncludedInEndToEnd": true, "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6750 | 0.8750 | 0.9000 | 0.7771 | 0.2857 | 2.130 | 2.066 | 2.761 |
| EMBEDDING_ONLY | 0.6000 | 0.7500 | 0.8750 | 0.7133 | 0.2857 | 916.050 | 818.326 | 1469.499 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7000 | 0.9000 | 0.9000 | 0.7958 | 0.2571 | 12.011 | 12.317 | 13.405 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.8750 | 0.9000 | 0.7424 | 0.3143 | 14.974 | 14.972 | 15.912 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5000 | 0.7500 | 0.7500 | 0.6111 | 0.4000 | 1.810 | 1.838 | 2.105 |
| EMBEDDING_ONLY | 0.5000 | 0.6667 | 0.6667 | 0.6111 | 0.3000 | 897.578 | 721.729 | 1504.833 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.7500 | 0.7500 | 0.7083 | 0.3000 | 10.723 | 10.991 | 12.528 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.7500 | 0.7500 | 0.6250 | 0.4000 | 15.017 | 15.257 | 15.952 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 2.118 | 2.058 | 2.520 |
| EMBEDDING_ONLY | 0.7143 | 0.8571 | 1.0000 | 0.8060 | 0.2500 | 966.378 | 915.560 | 1280.942 |
| HYBRID_BM25_EMBEDDING_RRF | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 12.169 | 12.139 | 12.873 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7857 | 1.0000 | 1.0000 | 0.8929 | 0.1667 | 14.906 | 14.897 | 15.673 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5714 | 0.8571 | 0.9286 | 0.7321 | 0.3846 | 2.418 | 2.284 | 3.359 |
| EMBEDDING_ONLY | 0.5714 | 0.7143 | 0.9286 | 0.7083 | 0.3077 | 881.556 | 750.271 | 1648.460 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5000 | 0.9286 | 0.9286 | 0.7024 | 0.3846 | 12.955 | 12.912 | 13.662 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8571 | 0.9286 | 0.6925 | 0.3846 | 15.004 | 14.895 | 15.928 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 1.0000 | 0.8426 | 0.3333 | 2.331 | 2.068 | 3.342 |
| EMBEDDING_ONLY | 0.5556 | 0.7778 | 1.0000 | 0.7167 | 0.5000 | 869.333 | 753.239 | 1341.992 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 1.0000 | 1.0000 | 0.8333 | 0.3333 | 12.122 | 12.180 | 12.900 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 1.0000 | 0.7500 | 0.5000 | 15.309 | 15.256 | 16.054 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5556 | 0.8889 | 0.8889 | 0.7222 | 0.2500 | 2.135 | 2.196 | 2.506 |
| EMBEDDING_ONLY | 0.6667 | 0.7778 | 0.8889 | 0.7500 | 0.1250 | 862.909 | 748.363 | 1186.933 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.8889 | 0.8889 | 0.7963 | 0.2500 | 11.866 | 12.642 | 13.093 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 0.8889 | 0.7160 | 0.2500 | 14.703 | 14.670 | 15.485 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 2.167 | 2.173 | 2.826 |
| EMBEDDING_ONLY | 0.5000 | 0.7000 | 0.8000 | 0.6417 | 0.4444 | 1079.175 | 880.935 | 2081.329 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7000 | 0.9000 | 0.9000 | 0.7833 | 0.3333 | 11.948 | 12.204 | 13.642 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 15.007 | 15.046 | 15.775 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.8333 | 0.8333 | 0.7917 | 0.1667 | 1.946 | 2.022 | 2.209 |
| EMBEDDING_ONLY | 0.6667 | 0.7500 | 0.8333 | 0.7431 | 0.1667 | 855.007 | 824.653 | 1301.083 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.8333 | 0.8333 | 0.7778 | 0.1667 | 12.087 | 12.334 | 13.338 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8333 | 0.8333 | 0.7500 | 0.1667 | 14.897 | 14.919 | 15.722 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 1.979 | 2.157 | 2.233 |
| EMBEDDING_ONLY | 0.6000 | 0.8000 | 0.8000 | 0.7000 | 0.0000 | 887.746 | 748.363 | 1155.834 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8000 | 1.0000 | 1.0000 | 0.9000 | 0.0000 | 11.364 | 12.650 | 12.901 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 14.366 | 14.247 | 14.801 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5882 | 0.8235 | 0.8824 | 0.7108 | 0.4615 | 2.218 | 2.074 | 2.941 |
| EMBEDDING_ONLY | 0.5882 | 0.7059 | 0.8824 | 0.7010 | 0.3846 | 907.485 | 753.239 | 1560.063 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5882 | 0.8824 | 0.8824 | 0.7255 | 0.3846 | 12.025 | 12.180 | 13.249 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5294 | 0.8235 | 0.8824 | 0.6977 | 0.4615 | 15.074 | 15.284 | 15.993 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.2353 | 2.089 | 2.058 | 2.662 |
| EMBEDDING_ONLY | 0.6111 | 0.7778 | 0.8889 | 0.7287 | 0.2941 | 932.002 | 858.366 | 1478.333 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.2353 | 12.177 | 12.317 | 13.606 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8889 | 0.8889 | 0.7685 | 0.2941 | 15.047 | 15.225 | 15.832 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8867963503478639}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.8295613557843402}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.7774815830232241}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.6928203230275508}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.647150228929434}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.257941804066302}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.7633700367119739}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.7}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.4363696929192158}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.3867504905630728}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.2229371288986763}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.1230289532557682}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 1.0838622059807226}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.0}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.9712858623572641}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.9667364890456636}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.8}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.7107423155935334}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.5081472026946221}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.4349354017951593}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4270314650923857}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.4195379566741888}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.4058008226006029}]
- `v03-hook-008` `EMBEDDING_ONLY` query=开场第一句话点名新手妈妈，但后面还要马上接具体困扰 expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4745229015205019}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.4600636142298381}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.4524814251020992}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.4458959819217368}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.405374632916038}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.43173681883373155}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.37564908194088387}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3549461581772416}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.34380790267937833}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.33477073315329564}]
- `v03-hook-019` `EMBEDDING_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5603088862430032}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.5048238803465139}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.4759480374752217}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.4656445650957977}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.45902729015074273}]
- `v03-value-012` `EMBEDDING_ONLY` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5901553908601738}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.41517723525787054}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3936817605671211}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3707319163741354}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.36894868386802043}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015772478887232988}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.015417457305502846}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015399194503672116}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.014955357142857142}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.016133229247983348}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.01562881562881563}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.015625}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.015527202696196438}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.01626123744050767}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.016001024065540194}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.015889029003783105}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.015399194503672116}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.014955357142857142}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.01575682382133995}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.01575682382133995}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.01565940787863959}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.015549662487945998}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.015512265512265512}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3819015111452972}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3691724629926876}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2326546800634584}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0790648567119154}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.931024194503672}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8326546800634584}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.7122622615060479}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6809118180808116}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3812499999999999}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1115018315018315}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2826546800634584}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.131762044876799}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9821300563236046}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.978798760116695}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8290951163073923}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5608968808968808}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.5321502664442908}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.5315324237516554}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.2581223106712565}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.1094303132226193}]
