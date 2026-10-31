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
- Run started at: `2026-09-11T15:25:20Z`
- Run finished at: `2026-09-11T15:26:03Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "useRetrievalText": true, "weightedRrf": {"bm25Weight": 0.3, "embeddingWeight": 0.7, "rrfK": 60}, "corpusEmbeddingMode": "precomputed_at_runner_init", "queryEmbeddingCache": "enabled_per_runner", "embeddingLatencyIncludedInEndToEnd": true, "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6750 | 0.8750 | 0.9000 | 0.7771 | 0.2857 | 4.953 | 5.067 | 6.065 |
| EMBEDDING_ONLY | 0.5500 | 0.8250 | 0.8750 | 0.6948 | 0.2571 | 1048.986 | 900.086 | 1645.743 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6750 | 0.8500 | 0.9000 | 0.7637 | 0.2571 | 13.284 | 13.863 | 14.946 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.8750 | 0.9000 | 0.7449 | 0.2857 | 18.058 | 18.067 | 19.453 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5000 | 0.7500 | 0.7500 | 0.6111 | 0.4000 | 4.024 | 4.094 | 4.698 |
| EMBEDDING_ONLY | 0.4167 | 0.7500 | 0.7500 | 0.5938 | 0.2000 | 1111.913 | 879.340 | 2138.244 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.6667 | 0.8333 | 0.7042 | 0.2000 | 11.411 | 10.990 | 14.623 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.7500 | 0.7500 | 0.6333 | 0.3000 | 17.009 | 16.917 | 17.757 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9286 | 1.0000 | 1.0000 | 0.9643 | 0.0833 | 5.022 | 5.010 | 5.884 |
| EMBEDDING_ONLY | 0.6429 | 0.9286 | 1.0000 | 0.7798 | 0.2500 | 1042.036 | 955.235 | 1629.267 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7857 | 1.0000 | 1.0000 | 0.8690 | 0.2500 | 14.527 | 14.579 | 15.023 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7857 | 1.0000 | 1.0000 | 0.8929 | 0.1667 | 18.674 | 18.664 | 19.899 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5714 | 0.8571 | 0.9286 | 0.7321 | 0.3846 | 5.680 | 5.646 | 6.250 |
| EMBEDDING_ONLY | 0.5714 | 0.7857 | 0.8571 | 0.6964 | 0.3077 | 1002.000 | 835.582 | 1641.720 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5714 | 0.8571 | 0.8571 | 0.7095 | 0.3077 | 13.646 | 13.645 | 14.420 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8571 | 0.9286 | 0.6925 | 0.3846 | 18.340 | 18.315 | 19.132 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 1.0000 | 0.8426 | 0.3333 | 5.198 | 5.216 | 6.159 |
| EMBEDDING_ONLY | 0.5556 | 0.8889 | 1.0000 | 0.7315 | 0.5000 | 1241.866 | 887.429 | 2369.643 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5556 | 1.0000 | 1.0000 | 0.7407 | 0.5000 | 13.851 | 13.747 | 15.076 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 1.0000 | 0.7500 | 0.5000 | 18.189 | 18.322 | 19.339 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5556 | 0.8889 | 0.8889 | 0.7222 | 0.2500 | 5.092 | 5.439 | 5.953 |
| EMBEDDING_ONLY | 0.6667 | 0.7778 | 0.7778 | 0.7361 | 0.1250 | 1047.345 | 864.554 | 1538.433 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.7778 | 0.8889 | 0.8185 | 0.1250 | 12.866 | 13.640 | 14.714 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.8889 | 0.8889 | 0.7160 | 0.2500 | 18.283 | 18.673 | 19.278 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 4.993 | 4.806 | 6.143 |
| EMBEDDING_ONLY | 0.4000 | 0.7000 | 0.8000 | 0.5750 | 0.4444 | 905.873 | 843.054 | 1233.715 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6000 | 0.8000 | 0.8000 | 0.6933 | 0.4444 | 13.325 | 14.055 | 14.966 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 0.9000 | 0.9000 | 0.7500 | 0.4444 | 17.958 | 17.906 | 19.324 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.8333 | 0.8333 | 0.7917 | 0.1667 | 4.632 | 4.525 | 5.591 |
| EMBEDDING_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.0833 | 1024.818 | 922.312 | 1618.104 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.8333 | 0.9167 | 0.7986 | 0.0833 | 13.138 | 13.830 | 14.775 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8333 | 0.8333 | 0.7583 | 0.0833 | 17.874 | 17.927 | 19.283 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 4.635 | 5.028 | 5.696 |
| EMBEDDING_ONLY | 0.6000 | 0.8000 | 0.8000 | 0.6917 | 0.0000 | 1011.947 | 864.554 | 1466.008 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8000 | 0.8000 | 1.0000 | 0.8400 | 0.0000 | 11.999 | 12.757 | 14.685 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6000 | 1.0000 | 1.0000 | 0.8000 | 0.0000 | 17.868 | 17.610 | 19.239 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5882 | 0.8235 | 0.8824 | 0.7108 | 0.4615 | 5.085 | 5.207 | 6.092 |
| EMBEDDING_ONLY | 0.4706 | 0.7647 | 0.8235 | 0.6324 | 0.3846 | 1068.241 | 931.558 | 1652.890 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5882 | 0.8235 | 0.8235 | 0.7020 | 0.3846 | 13.450 | 13.940 | 14.981 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5294 | 0.8235 | 0.8824 | 0.7036 | 0.4615 | 18.099 | 17.988 | 19.277 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7778 | 0.8889 | 0.8889 | 0.8333 | 0.2353 | 4.916 | 5.050 | 5.793 |
| EMBEDDING_ONLY | 0.6111 | 0.8889 | 0.9444 | 0.7546 | 0.2353 | 1041.090 | 900.086 | 1796.214 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7222 | 0.8889 | 0.9444 | 0.8009 | 0.2353 | 13.483 | 13.863 | 14.837 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.8889 | 0.8889 | 0.7685 | 0.2353 | 18.071 | 18.138 | 19.862 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.6989632453288304}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.6943650748294136}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.6379930845075023}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.5595028849441883}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5449492609130661}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.0405319634289438}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9011551125709446}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8486684247915055}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.6316761657092368}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.5916079783099616}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.1874645015519594}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.1677484162422844}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.9662823901213162}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.9215455665108366}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.9135002783911397}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.8333333333333334}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.8137884587711595}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.7474350927519359}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.6761234037828132}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.5499719409228703}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.4474281415807856}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4123404046739965}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.3917194811647239}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.37492864942296833}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.36950611620903345}]
- `v03-hook-008` `EMBEDDING_ONLY` query=开场第一句话点名新手妈妈，但后面还要马上接具体困扰 expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4450625597649428}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.4403122960163689}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.43904047154780457}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.41318633565612717}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.3394521822154432}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.4227072864759545}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3617262614983622}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.35978684201125416}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3352387349792689}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.32766325292582643}]
- `v03-value-012` `EMBEDDING_ONLY` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5223869633735895}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.37985073438283906}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.37935556016743094}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3725219833666091}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3597311368751087}]
- `v03-value-014` `EMBEDDING_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.4004878033841}, {'knowledgeId': 'value-good-case-step-by-step-v1', 'score': 0.39763000436156587}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.39738797401653825}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.3914661257159941}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.3882577793158286}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.016393442622950817}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015767934520943667}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.01545893719806763}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.01544477028347996}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.015349264705882352}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.01631411951348493}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.016208355367530406}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.01579861111111111}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.015552884615384614}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.01520966595593461}]
- `v03-value-012` `HYBRID_BM25_EMBEDDING_RRF` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.016393442622950817}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.01597782258064516}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.015588723051409618}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.015482954545454545}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.015017825311942958}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.01631411951348493}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.015855532786885243}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.015726495726495725}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.015054945054945056}, {'knowledgeId': 'value-good-case-step-by-step-v1', 'score': 0.014819734345351042}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3810697702834798}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3767091532151772}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2327868852459016}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0789672931681507}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.9318969667790081}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8323373876255948}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.7127075621364356}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.68059428134055}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3816716269841267}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1111778846153846}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2827075621364354}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.128744119743407}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9820020481310803}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9801331327985738}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8290537084398975}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5627075621364357}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.5319845650449497}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.529190009337068}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.2569510135135136}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.10733499377335}]
