# Video Diagnosis RAG Retrieval Benchmark

- Dataset version: `video-diagnosis-rag-verified-v0.3`
- Corpus version: `v0.3`
- Verified sample count: `60`
- Corpus size: `34`
- Benchmark mode: `SKILL_FILTERED`
- Candidate pool: `{"candidatePoolMin": 11.0, "candidatePoolMedian": 11.0, "candidatePoolMax": 12.0}`
- Model: `in_memory_bm25_embedding_benchmark`
- Embedding provider: `openai`
- Embedding model: `text-embedding-3-small`
- Embedding dimension: `1536`
- Run started at: `2026-09-11T11:50:59Z`
- Run finished at: `2026-09-11T11:51:46Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "SKILL_FILTERED", "corpusVersion": "v0.3", "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7833 | 0.8833 | 0.9333 | 0.8501 | 0.1091 | 2.376 | 2.121 | 4.046 |
| EMBEDDING_ONLY | 0.7833 | 0.8667 | 0.9167 | 0.8331 | 0.1273 | 772.607 | 723.710 | 1336.364 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7667 | 0.8833 | 0.9167 | 0.8356 | 0.1273 | 2.732 | 2.730 | 3.347 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7667 | 0.9000 | 0.9333 | 0.8474 | 0.1273 | 4.273 | 4.180 | 5.035 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5500 | 0.7500 | 0.8000 | 0.6753 | 0.2222 | 2.486 | 2.491 | 3.592 |
| EMBEDDING_ONLY | 0.5500 | 0.7000 | 0.7500 | 0.6435 | 0.2778 | 573.705 | 469.476 | 979.276 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5500 | 0.7000 | 0.7500 | 0.6527 | 0.2778 | 2.401 | 2.349 | 2.821 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5500 | 0.8000 | 0.8000 | 0.6921 | 0.2222 | 4.538 | 4.412 | 5.175 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0556 | 1.606 | 1.371 | 2.388 |
| EMBEDDING_ONLY | 0.9500 | 0.9500 | 1.0000 | 0.9600 | 0.0556 | 906.625 | 807.551 | 1438.708 |
| HYBRID_BM25_EMBEDDING_RRF | 0.9000 | 1.0000 | 1.0000 | 0.9500 | 0.0556 | 2.705 | 2.667 | 3.090 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.8500 | 0.9500 | 1.0000 | 0.9125 | 0.1111 | 4.148 | 4.083 | 4.553 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0526 | 3.036 | 3.244 | 4.053 |
| EMBEDDING_ONLY | 0.8500 | 0.9500 | 1.0000 | 0.8958 | 0.0526 | 837.492 | 807.720 | 1054.491 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8500 | 0.9500 | 1.0000 | 0.9042 | 0.0526 | 3.090 | 3.002 | 3.583 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.9000 | 0.9500 | 1.0000 | 0.9375 | 0.0526 | 4.133 | 4.081 | 4.570 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.9167 | 1.0000 | 1.0000 | 0.9583 | 0.0000 | 2.850 | 2.609 | 4.430 |
| EMBEDDING_ONLY | 0.8333 | 0.9167 | 1.0000 | 0.8778 | 0.1111 | 786.886 | 712.761 | 1229.568 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8333 | 1.0000 | 1.0000 | 0.9167 | 0.1111 | 2.912 | 2.951 | 3.450 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.9167 | 1.0000 | 1.0000 | 0.9583 | 0.1111 | 4.320 | 4.200 | 4.961 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.9167 | 1.0000 | 0.8542 | 0.0909 | 2.253 | 1.888 | 3.452 |
| EMBEDDING_ONLY | 0.8333 | 0.9167 | 1.0000 | 0.8778 | 0.0909 | 814.353 | 764.637 | 1471.200 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8333 | 1.0000 | 1.0000 | 0.9028 | 0.0909 | 2.702 | 2.803 | 3.249 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.9167 | 1.0000 | 0.8125 | 0.0909 | 4.111 | 4.141 | 4.388 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.8333 | 0.9444 | 0.9444 | 0.8858 | 0.1765 | 2.277 | 2.353 | 3.596 |
| EMBEDDING_ONLY | 0.7778 | 0.8333 | 0.8333 | 0.8181 | 0.1765 | 723.535 | 743.555 | 1054.098 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7778 | 0.8333 | 0.8889 | 0.8302 | 0.1765 | 2.685 | 2.704 | 3.180 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.8333 | 0.9444 | 0.9444 | 0.8858 | 0.1765 | 4.269 | 4.202 | 4.923 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6667 | 0.7222 | 0.8333 | 0.7395 | 0.1111 | 2.241 | 1.645 | 3.603 |
| EMBEDDING_ONLY | 0.7222 | 0.8333 | 0.8889 | 0.7886 | 0.1111 | 784.329 | 730.766 | 1327.294 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.7778 | 0.8333 | 0.7423 | 0.1111 | 2.679 | 2.637 | 3.183 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6667 | 0.7778 | 0.8333 | 0.7582 | 0.1111 | 4.353 | 4.304 | 5.193 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 2.138 | 1.888 | 3.087 |
| EMBEDDING_ONLY | 0.8750 | 0.8750 | 1.0000 | 0.9000 | 0.0000 | 852.856 | 829.356 | 1487.115 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8750 | 1.0000 | 1.0000 | 0.9375 | 0.0000 | 2.549 | 2.387 | 3.165 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6250 | 1.0000 | 1.0000 | 0.8125 | 0.0000 | 4.179 | 4.177 | 4.399 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.8077 | 0.8846 | 0.9615 | 0.8683 | 0.0909 | 2.501 | 2.330 | 4.116 |
| EMBEDDING_ONLY | 0.8462 | 0.9231 | 0.9615 | 0.8814 | 0.0909 | 784.169 | 809.886 | 1258.991 |
| HYBRID_BM25_EMBEDDING_RRF | 0.8077 | 0.9231 | 0.9615 | 0.8622 | 0.0909 | 2.754 | 2.794 | 3.302 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.8462 | 0.9231 | 0.9615 | 0.8997 | 0.0909 | 4.277 | 4.202 | 4.967 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7692 | 0.8462 | 0.8846 | 0.8243 | 0.1600 | 2.324 | 1.918 | 3.675 |
| EMBEDDING_ONLY | 0.6923 | 0.8077 | 0.8462 | 0.7642 | 0.2000 | 736.354 | 684.698 | 1083.551 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6923 | 0.8077 | 0.8462 | 0.7777 | 0.2000 | 2.767 | 2.730 | 3.355 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.7308 | 0.8462 | 0.8846 | 0.8057 | 0.2000 | 4.298 | 4.210 | 5.134 |


## Recall@5 Miss Analysis

- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8867963503478639}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.7774815830232241}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.647150228929434}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.6469966392206304}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.628970902033151}]
- `v03-hook-013` `BM25_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3794609894300105}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.8638684255813601}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.7548294124240689}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.5911975668985759}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.5241424183609592}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.257941804066302}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.7633700367119739}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.5644325210301584}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.3867504905630728}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.2229371288986763}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.1230289532557682}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.0178267156159653}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.9853292781642932}]
- `v03-hook-002` `EMBEDDING_ONLY` query=第一句说自己是营养师，下一句马上告诉宝妈怎么避开配料表陷阱 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.3253484606264125}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.30561125710469567}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.2795361251216519}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.27943390099148663}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.2730346492714428}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.4349471249011814}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4270774674809541}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.4056432938191725}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.4010698439342886}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.38743660710761413}]
- `v03-hook-006` `EMBEDDING_ONLY` query=首屏没有明确谁该看、为什么看，也没有冲突点 expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] actualTop5=[{'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.4628638780154425}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.4104487759100508}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.4025451622056182}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.3970445929252439}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.3851935708903953}]
- `v03-hook-013` `EMBEDDING_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4387810732863396}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.4189917834477632}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.41038711046273046}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.3527270760892343}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.35209266935716516}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.43173080848469536}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.37562802085329305}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.34389102024705376}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.33469947444454035}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.31822184249961205}]
- `v03-hook-002` `HYBRID_BM25_EMBEDDING_RRF` query=第一句说自己是营养师，下一句马上告诉宝妈怎么避开配料表陷阱 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03200204813108039}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03131881575727918}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.03128054740957967}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.031009615384615385}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.030776515151515152}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.032018442622950824}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.031544957774465976}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.0315136476426799}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.030798389007344232}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.03057889822595705}]
- `v03-hook-013` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.032018442622950824}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03177805800756621}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.031754032258064516}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.03125763125763126}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.030798389007344232}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03252247488101534}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.032266458495966696}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.0315136476426799}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.03149801587301587}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.030303030303030304}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.03278688524590164}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.031009615384615385}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.031009615384615385}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.03057889822595705}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3984118852459015}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3947238034998943}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.0964233890073443}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.9473866635156958}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.9452692687747034}]
- `v03-hook-013` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 2.1484118852459013}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.5449432942812817}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 1.0968826312576314}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9776270481310803}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.7979070902656307}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.848915917503966}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.728395490754031}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6973866635156956}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3971230158730157}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.9456876456876455}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.2991803278688523}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9983870967741935}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.9959635136105722}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.8466346153846152}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.5743501511276448}]
