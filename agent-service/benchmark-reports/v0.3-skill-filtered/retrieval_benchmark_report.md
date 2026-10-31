# Video Diagnosis RAG Retrieval Benchmark

- Dataset version: `video-diagnosis-rag-verified-v0.3`
- Corpus version: `v0.3`
- Verified sample count: `60`
- Corpus size: `34`
- Benchmark mode: `SKILL_FILTERED`
- Candidate pool: `{"candidatePoolMin": 11.0, "candidatePoolMedian": 11.0, "candidatePoolMax": 12.0}`
- Model: `in_memory_keyword_vector_baseline`
- Run started at: `2026-09-11T10:52:00Z`
- Run finished at: `2026-09-11T10:52:02Z`
- Configuration: `{"strategies": ["BM25_ONLY", "VECTOR_ONLY", "HYBRID_RRF", "HYBRID_RRF_RERANK"], "top_k": 10, "repeat_count": 5, "verified_only": true, "benchmarkMode": "SKILL_FILTERED", "corpusVersion": "v0.3", "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "vector_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7833 | 0.8833 | 0.9333 | 0.8501 | 0.1091 | 1.269 | 1.244 | 1.633 |
| VECTOR_ONLY | 0.7833 | 0.8833 | 0.9333 | 0.8497 | 0.1091 | 0.783 | 0.743 | 0.963 |
| HYBRID_RRF | 0.7833 | 0.8833 | 0.9333 | 0.8497 | 0.1091 | 1.878 | 1.883 | 2.134 |
| HYBRID_RRF_RERANK | 0.7667 | 0.9000 | 0.9333 | 0.8448 | 0.1273 | 2.499 | 2.378 | 3.088 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5500 | 0.7500 | 0.8000 | 0.6753 | 0.2222 | 1.470 | 1.457 | 1.683 |
| VECTOR_ONLY | 0.5500 | 0.7500 | 0.8000 | 0.6740 | 0.2222 | 0.911 | 0.895 | 1.005 |
| HYBRID_RRF | 0.5500 | 0.7500 | 0.8000 | 0.6740 | 0.2222 | 2.029 | 2.033 | 2.143 |
| HYBRID_RRF_RERANK | 0.5500 | 0.8000 | 0.8000 | 0.6844 | 0.2222 | 2.882 | 2.879 | 3.142 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0556 | 1.187 | 1.190 | 1.292 |
| VECTOR_ONLY | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0556 | 0.739 | 0.721 | 0.837 |
| HYBRID_RRF | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0556 | 1.878 | 1.899 | 2.038 |
| HYBRID_RRF_RERANK | 0.8500 | 0.9500 | 1.0000 | 0.9125 | 0.1111 | 2.282 | 2.312 | 2.397 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0526 | 1.151 | 1.133 | 1.324 |
| VECTOR_ONLY | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0526 | 0.700 | 0.671 | 0.801 |
| HYBRID_RRF | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0526 | 1.728 | 1.697 | 1.886 |
| HYBRID_RRF_RERANK | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0526 | 2.332 | 2.318 | 2.565 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9167 | 1.0000 | 1.0000 | 0.9583 | 0.0000 | 1.285 | 1.263 | 1.625 |
| VECTOR_ONLY | 0.9167 | 1.0000 | 1.0000 | 0.9583 | 0.0000 | 0.773 | 0.730 | 0.957 |
| HYBRID_RRF | 0.9167 | 1.0000 | 1.0000 | 0.9583 | 0.0000 | 1.873 | 1.896 | 2.087 |
| HYBRID_RRF_RERANK | 0.9167 | 1.0000 | 1.0000 | 0.9583 | 0.1111 | 2.542 | 2.438 | 3.057 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.9167 | 1.0000 | 0.8542 | 0.0909 | 1.253 | 1.242 | 1.461 |
| VECTOR_ONLY | 0.7500 | 0.9167 | 1.0000 | 0.8542 | 0.0909 | 0.786 | 0.755 | 0.948 |
| HYBRID_RRF | 0.7500 | 0.9167 | 1.0000 | 0.8542 | 0.0909 | 1.930 | 1.910 | 2.144 |
| HYBRID_RRF_RERANK | 0.6667 | 0.9167 | 1.0000 | 0.8125 | 0.0909 | 2.475 | 2.418 | 2.920 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.8333 | 0.9444 | 0.9444 | 0.8858 | 0.1765 | 1.270 | 1.221 | 1.638 |
| VECTOR_ONLY | 0.8333 | 0.9444 | 0.9444 | 0.8858 | 0.1765 | 0.775 | 0.737 | 0.943 |
| HYBRID_RRF | 0.8333 | 0.9444 | 0.9444 | 0.8858 | 0.1765 | 1.834 | 1.872 | 2.027 |
| HYBRID_RRF_RERANK | 0.8333 | 0.9444 | 0.9444 | 0.8858 | 0.1765 | 2.452 | 2.342 | 3.005 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6667 | 0.7222 | 0.8333 | 0.7395 | 0.1111 | 1.268 | 1.219 | 1.591 |
| VECTOR_ONLY | 0.6667 | 0.7222 | 0.8333 | 0.7381 | 0.1111 | 0.797 | 0.818 | 0.927 |
| HYBRID_RRF | 0.6667 | 0.7222 | 0.8333 | 0.7381 | 0.1111 | 1.892 | 1.884 | 2.154 |
| HYBRID_RRF_RERANK | 0.6667 | 0.7778 | 0.8333 | 0.7497 | 0.1111 | 2.533 | 2.383 | 3.116 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 1.268 | 1.237 | 1.462 |
| VECTOR_ONLY | 0.7500 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 0.809 | 0.789 | 0.979 |
| HYBRID_RRF | 0.7500 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 1.950 | 1.967 | 2.088 |
| HYBRID_RRF_RERANK | 0.6250 | 1.0000 | 1.0000 | 0.8125 | 0.0000 | 2.485 | 2.376 | 2.981 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.8077 | 0.8846 | 0.9615 | 0.8683 | 0.0909 | 1.282 | 1.259 | 1.653 |
| VECTOR_ONLY | 0.8077 | 0.8846 | 0.9615 | 0.8677 | 0.0909 | 0.785 | 0.753 | 0.959 |
| HYBRID_RRF | 0.8077 | 0.8846 | 0.9615 | 0.8677 | 0.0909 | 1.839 | 1.839 | 2.125 |
| HYBRID_RRF_RERANK | 0.8462 | 0.9231 | 0.9615 | 0.8933 | 0.0909 | 2.497 | 2.407 | 3.012 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7692 | 0.8462 | 0.8846 | 0.8243 | 0.1600 | 1.257 | 1.226 | 1.613 |
| VECTOR_ONLY | 0.7692 | 0.8462 | 0.8846 | 0.8238 | 0.1600 | 0.774 | 0.733 | 0.908 |
| HYBRID_RRF | 0.7692 | 0.8462 | 0.8846 | 0.8238 | 0.1600 | 1.896 | 1.902 | 2.167 |
| HYBRID_RRF_RERANK | 0.7308 | 0.8462 | 0.8846 | 0.8062 | 0.2000 | 2.504 | 2.380 | 3.082 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8867963503478639}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.7774815830232241}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.647150228929434}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.6469966392206304}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.628970902033151}]
- `v03-hook-013` `BM25_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3794609894300105}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.8638684255813601}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.7548294124240689}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.5911975668985759}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.5241424183609592}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.257941804066302}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.7633700367119739}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.5644325210301584}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.3867504905630728}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.2229371288986763}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.1230289532557682}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.0178267156159653}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.9853292781642932}]
- `v03-hook-004` `VECTOR_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.07258064516129033}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.05921052631578947}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.05384615384615385}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.05309734513274336}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.05}]
- `v03-hook-013` `VECTOR_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.1111111111111111}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.06329113924050633}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.058823529411764705}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.043478260869565216}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.0390625}]
- `v03-hook-014` `VECTOR_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.09090909090909091}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.07857142857142857}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.0763888888888889}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.05263157894736842}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.041379310344827586}]
- `v03-hook-019` `VECTOR_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.11627906976744186}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.09848484848484848}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.08387096774193549}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.07692307692307693}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.07643312101910828}]
- `v03-hook-004` `HYBRID_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.03125}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03076923076923077}]
- `v03-hook-013` `HYBRID_RRF` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.03125}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03076923076923077}]
- `v03-hook-014` `HYBRID_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.03125}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.03076923076923077}]
- `v03-hook-019` `HYBRID_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.031746031746031744}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.031009615384615385}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.031009615384615385}]
- `v03-hook-004` `HYBRID_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3991803278688524}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3983870967741934}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0976190476190477}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.9468749999999999}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.9461538461538461}]
- `v03-hook-013` `HYBRID_RRF_RERANK` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 2.1491803278688524}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.5483870967741935}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 1.0976190476190477}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9768749999999999}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.7961538461538462}]
- `v03-hook-014` `HYBRID_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.8491803278688523}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.7276190476190474}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6983870967741934}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3968749999999999}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.9461538461538461}]
- `v03-hook-019` `HYBRID_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2991803278688523}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9983870967741935}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9976190476190476}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8463942307692305}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.5754545454545454}]
