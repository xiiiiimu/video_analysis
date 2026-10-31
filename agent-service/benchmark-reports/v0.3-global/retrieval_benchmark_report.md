# Video Diagnosis RAG Retrieval Benchmark

- Dataset version: `video-diagnosis-rag-verified-v0.3`
- Corpus version: `v0.3`
- Verified sample count: `60`
- Corpus size: `34`
- Benchmark mode: `GLOBAL`
- Candidate pool: `{"candidatePoolMin": 34.0, "candidatePoolMedian": 34.0, "candidatePoolMax": 34.0}`
- Model: `in_memory_keyword_vector_baseline`
- Run started at: `2026-09-11T10:52:09Z`
- Run finished at: `2026-09-11T10:52:20Z`
- Configuration: `{"strategies": ["BM25_ONLY", "VECTOR_ONLY", "HYBRID_RRF", "HYBRID_RRF_RERANK"], "top_k": 10, "repeat_count": 5, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "vector_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6167 | 0.8333 | 0.8833 | 0.7296 | 0.2545 | 4.321 | 4.268 | 5.205 |
| VECTOR_ONLY | 0.6167 | 0.8167 | 0.8833 | 0.7271 | 0.2364 | 3.089 | 2.777 | 5.153 |
| HYBRID_RRF | 0.6167 | 0.8167 | 0.8833 | 0.7271 | 0.2364 | 9.365 | 7.131 | 17.967 |
| HYBRID_RRF_RERANK | 0.5500 | 0.8167 | 0.8833 | 0.6963 | 0.2727 | 18.231 | 19.236 | 31.272 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.4000 | 0.7000 | 0.7500 | 0.5421 | 0.4444 | 4.101 | 4.043 | 4.576 |
| VECTOR_ONLY | 0.3500 | 0.6500 | 0.7500 | 0.5121 | 0.3889 | 2.850 | 2.771 | 3.400 |
| HYBRID_RRF | 0.3500 | 0.6500 | 0.7500 | 0.5121 | 0.3889 | 12.776 | 10.363 | 18.590 |
| HYBRID_RRF_RERANK | 0.3000 | 0.7000 | 0.8000 | 0.5033 | 0.3889 | 9.133 | 8.659 | 11.761 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.9000 | 0.9500 | 0.8342 | 0.0556 | 4.221 | 4.134 | 5.288 |
| VECTOR_ONLY | 0.8000 | 0.9000 | 0.9500 | 0.8567 | 0.0556 | 2.525 | 2.512 | 2.800 |
| HYBRID_RRF | 0.8000 | 0.9000 | 0.9500 | 0.8567 | 0.0556 | 9.466 | 7.131 | 15.850 |
| HYBRID_RRF_RERANK | 0.6500 | 0.8500 | 0.9000 | 0.7758 | 0.1667 | 18.189 | 19.687 | 27.278 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7000 | 0.9000 | 0.9500 | 0.8125 | 0.2632 | 4.642 | 4.581 | 5.207 |
| VECTOR_ONLY | 0.7000 | 0.9000 | 0.9500 | 0.8125 | 0.2632 | 3.891 | 3.584 | 5.728 |
| HYBRID_RRF | 0.7000 | 0.9000 | 0.9500 | 0.8125 | 0.2632 | 5.853 | 5.855 | 6.418 |
| HYBRID_RRF_RERANK | 0.7000 | 0.9000 | 0.9500 | 0.8097 | 0.2632 | 27.370 | 24.448 | 42.942 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6667 | 0.8333 | 1.0000 | 0.7639 | 0.3333 | 4.467 | 4.329 | 5.359 |
| VECTOR_ONLY | 0.6667 | 0.7500 | 1.0000 | 0.7528 | 0.3333 | 3.278 | 2.672 | 5.801 |
| HYBRID_RRF | 0.6667 | 0.7500 | 1.0000 | 0.7528 | 0.3333 | 6.916 | 6.300 | 9.350 |
| HYBRID_RRF_RERANK | 0.5833 | 0.8333 | 0.9167 | 0.7292 | 0.5556 | 18.050 | 18.465 | 26.349 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.1818 | 4.396 | 4.322 | 5.063 |
| VECTOR_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.1818 | 3.399 | 2.836 | 5.319 |
| HYBRID_RRF | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.1818 | 9.006 | 6.061 | 17.649 |
| HYBRID_RRF_RERANK | 0.5000 | 0.8333 | 0.9167 | 0.6829 | 0.1818 | 18.648 | 19.527 | 32.160 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6111 | 0.8889 | 0.9444 | 0.7611 | 0.3529 | 4.276 | 4.177 | 5.163 |
| VECTOR_ONLY | 0.6667 | 0.8889 | 0.9444 | 0.7889 | 0.3529 | 3.005 | 2.807 | 3.939 |
| HYBRID_RRF | 0.6667 | 0.8889 | 0.9444 | 0.7889 | 0.3529 | 10.654 | 8.595 | 18.048 |
| HYBRID_RRF_RERANK | 0.6111 | 0.8889 | 0.9444 | 0.7611 | 0.3529 | 18.345 | 16.676 | 32.692 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6111 | 0.7222 | 0.7222 | 0.6709 | 0.1667 | 4.220 | 4.241 | 4.679 |
| VECTOR_ONLY | 0.5556 | 0.7222 | 0.7222 | 0.6421 | 0.1111 | 2.840 | 2.691 | 3.609 |
| HYBRID_RRF | 0.5556 | 0.7222 | 0.7222 | 0.6421 | 0.1111 | 9.948 | 8.398 | 17.918 |
| HYBRID_RRF_RERANK | 0.5000 | 0.7222 | 0.7778 | 0.6185 | 0.1111 | 17.959 | 15.364 | 32.647 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6250 | 1.0000 | 1.0000 | 0.7917 | 0.0000 | 4.221 | 4.266 | 4.545 |
| VECTOR_ONLY | 0.6250 | 1.0000 | 1.0000 | 0.7917 | 0.0000 | 3.262 | 2.836 | 4.956 |
| HYBRID_RRF | 0.6250 | 1.0000 | 1.0000 | 0.7917 | 0.0000 | 10.588 | 9.290 | 17.715 |
| HYBRID_RRF_RERANK | 0.5000 | 0.8750 | 1.0000 | 0.7188 | 0.0000 | 16.285 | 9.790 | 33.803 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5385 | 0.8077 | 0.8846 | 0.6786 | 0.3636 | 4.369 | 4.271 | 5.256 |
| VECTOR_ONLY | 0.5385 | 0.7692 | 0.8846 | 0.6728 | 0.3636 | 3.076 | 2.775 | 4.439 |
| HYBRID_RRF | 0.5385 | 0.7692 | 0.8846 | 0.6728 | 0.3636 | 9.010 | 6.862 | 16.710 |
| HYBRID_RRF_RERANK | 0.5385 | 0.8077 | 0.8846 | 0.6882 | 0.4091 | 19.657 | 20.142 | 39.428 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6923 | 0.8077 | 0.8462 | 0.7615 | 0.2400 | 4.304 | 4.242 | 4.853 |
| VECTOR_ONLY | 0.6923 | 0.8077 | 0.8462 | 0.7615 | 0.2000 | 3.049 | 2.777 | 4.828 |
| HYBRID_RRF | 0.6923 | 0.8077 | 0.8462 | 0.7615 | 0.2000 | 9.343 | 6.920 | 17.985 |
| HYBRID_RRF_RERANK | 0.5769 | 0.8077 | 0.8462 | 0.6974 | 0.2400 | 17.403 | 19.593 | 28.691 |


## Recall@5 Miss Analysis

- `v03-hook-001` `BM25_ONLY` query=开头一直讲自己做账号三年，第四秒才说粉丝能少踩什么坑 expected=['hook-pattern-self-intro-delay-v1'] hardNegative=['hook-good-case-authority-fast-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.9434563530497265}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.7258661863112977}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.6897304947150052}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.5644325210301584}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.539163866017192}]
- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8867963503478639}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.8295613557843402}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.7774815830232241}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.6928203230275508}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.647150228929434}]
- `v03-hook-013` `BM25_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3794609894300105}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.8638684255813601}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.7548294124240689}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.7258661863112977}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.5911975668985759}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.257941804066302}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.7633700367119739}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.7}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.4363696929192158}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.3867504905630728}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.2229371288986763}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.1230289532557682}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 1.0838622059807226}]
- `v03-structure-012` `BM25_ONLY` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.0}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.9332565252573828}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.8386278693775346}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.7882634225314346}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.6897304947150052}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.0}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.9712858623572641}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.9667364890456636}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.8}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.7107423155935334}]
- `v03-hook-001` `VECTOR_ONLY` query=开头一直讲自己做账号三年，第四秒才说粉丝能少踩什么坑 expected=['hook-pattern-self-intro-delay-v1'] hardNegative=['hook-good-case-authority-fast-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.07258064516129033}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.05785123966942149}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.050724637681159424}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.044444444444444446}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.040983606557377046}]
- `v03-hook-004` `VECTOR_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.07258064516129033}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.07142857142857142}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.061224489795918366}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.05921052631578947}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.05384615384615385}]
- `v03-hook-013` `VECTOR_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.1111111111111111}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.06329113924050633}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.058823529411764705}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.058333333333333334}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.043478260869565216}]
- `v03-hook-014` `VECTOR_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.09090909090909091}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.07857142857142857}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.0763888888888889}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.05263157894736842}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.050359712230215826}]
- `v03-hook-019` `VECTOR_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.12962962962962962}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.11627906976744186}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.09848484848484848}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 0.09090909090909091}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.08870967741935484}]
- `v03-structure-012` `VECTOR_ONLY` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.08}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.07692307692307693}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.06451612903225806}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.05925925925925926}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.05303030303030303}]
- `v03-value-014` `VECTOR_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.07575757575757576}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.07407407407407407}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.07407407407407407}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.06201550387596899}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.056451612903225805}]
- `v03-hook-001` `HYBRID_RRF` query=开头一直讲自己做账号三年，第四秒才说粉丝能少踩什么坑 expected=['hook-pattern-self-intro-delay-v1'] hardNegative=['hook-good-case-authority-fast-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.03125}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.03076923076923077}]
- `v03-hook-004` `HYBRID_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.03149801587301587}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.03149801587301587}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.03076923076923077}]
- `v03-hook-013` `HYBRID_RRF` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.03125}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.03076923076923077}]
- `v03-hook-014` `HYBRID_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.03125}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.030536130536130537}]
- `v03-hook-019` `HYBRID_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 0.030776515151515152}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 0.03076923076923077}]
- `v03-structure-012` `HYBRID_RRF` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.03125}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03076923076923077}]
- `v03-value-014` `HYBRID_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.03125}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.03076923076923077}]
- `v03-hook-004` `HYBRID_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3991803278688524}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3971230158730157}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2483870967741935}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0961538461538463}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.9473710317460315}]
- `v03-hook-013` `HYBRID_RRF_RERANK` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 2.1491803278688524}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.5483870967741935}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 1.0976190476190477}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.096875}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9761538461538461}]
- `v03-hook-014` `HYBRID_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8491803278688523}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.7276190476190474}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6983870967741934}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3968749999999999}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1256876456876457}]
- `v03-hook-019` `HYBRID_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2983870967741935}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.1491803278688524}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9976190476190476}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9954823975044562}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8426673567977914}]
- `v03-structure-012` `HYBRID_RRF_RERANK` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.5791803278688525}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.3983870967741934}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.276875}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.2476190476190476}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0961538461538463}]
- `v03-structure-017` `HYBRID_RRF_RERANK` query=第一段钩子很好，但第二段没有接上承诺，像换了一个话题 expected=['structure-rule-opening-transition-v1', 'structure-bad-case-topic-jump-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.3991803278688524}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3983870967741934}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 1.0976190476190477}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.8247827706387848}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.7966346153846153}]
- `v03-value-014` `HYBRID_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5776190476190475}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.5491803278688525}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.5483870967741935}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.276875}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.1252284034373587}]
