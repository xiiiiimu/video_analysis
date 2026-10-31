# Video Diagnosis RAG Retrieval Benchmark

- Dataset version: `video-diagnosis-rag-verified-v0.3`
- Corpus version: `v0.3`
- Verified sample count: `60`
- Corpus size: `34`
- Benchmark mode: `GLOBAL`
- Candidate pool: `{"candidatePoolMin": 34.0, "candidatePoolMedian": 34.0, "candidatePoolMax": 34.0}`
- Model: `in_memory_bm25_embedding_benchmark`
- Embedding provider: `openai`
- Embedding model: `text-embedding-3-small`
- Embedding dimension: `1536`
- Run started at: `2026-09-11T11:52:24Z`
- Run finished at: `2026-09-11T11:53:03Z`
- Configuration: `{"strategies": ["BM25_ONLY", "EMBEDDING_ONLY", "HYBRID_BM25_EMBEDDING_RRF", "HYBRID_BM25_EMBEDDING_RRF_RERANK"], "top_k": 10, "repeat_count": 1, "verified_only": true, "benchmarkMode": "GLOBAL", "corpusVersion": "v0.3", "rerankEnabled": true, "note": "Formal metrics only use VERIFIED samples. PENDING_REVIEW candidates are excluded by default."}`
- Retriever params: `{"bm25_limit": 30, "embedding_limit": 30, "rrf_k": 60, "final_top_k": 10, "rerank": "keyword_overlap_phrase_type_position_v1"}`

## Overall Metrics

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6167 | 0.8333 | 0.8833 | 0.7296 | 0.2545 | 4.212 | 4.232 | 4.674 |
| EMBEDDING_ONLY | 0.6333 | 0.7833 | 0.8667 | 0.7339 | 0.2727 | 611.002 | 581.405 | 933.061 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6333 | 0.8500 | 0.8833 | 0.7486 | 0.2545 | 13.637 | 13.425 | 15.530 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5500 | 0.8333 | 0.9000 | 0.6993 | 0.2909 | 13.401 | 13.276 | 14.736 |

## Metrics By Skill

### `hook_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.4000 | 0.7000 | 0.7500 | 0.5421 | 0.4444 | 4.396 | 4.346 | 4.922 |
| EMBEDDING_ONLY | 0.4500 | 0.6500 | 0.6500 | 0.5667 | 0.4444 | 476.133 | 473.806 | 564.905 |
| HYBRID_BM25_EMBEDDING_RRF | 0.4500 | 0.7000 | 0.7000 | 0.5708 | 0.4444 | 14.295 | 14.524 | 15.706 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.3500 | 0.7000 | 0.8000 | 0.5308 | 0.4444 | 13.942 | 13.580 | 15.918 |

### `structure_rhythm_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7500 | 0.9000 | 0.9500 | 0.8342 | 0.0556 | 4.045 | 4.035 | 4.466 |
| EMBEDDING_ONLY | 0.7500 | 0.9000 | 1.0000 | 0.8392 | 0.1667 | 679.592 | 602.066 | 1176.093 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.9500 | 1.0000 | 0.8625 | 0.1111 | 13.346 | 13.201 | 14.416 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6500 | 0.9000 | 0.9500 | 0.7822 | 0.1667 | 13.107 | 13.060 | 13.954 |

### `value_delivery_analysis`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.7000 | 0.9000 | 0.9500 | 0.8125 | 0.2632 | 4.196 | 4.261 | 4.659 |
| EMBEDDING_ONLY | 0.7000 | 0.8000 | 0.9500 | 0.7958 | 0.2105 | 677.281 | 632.471 | 939.003 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7000 | 0.9000 | 0.9500 | 0.8125 | 0.2105 | 13.270 | 13.019 | 14.669 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6500 | 0.9000 | 0.9500 | 0.7847 | 0.2632 | 13.154 | 13.103 | 13.716 |


## Metrics By Difficulty

### `ADVERSARIAL`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6667 | 0.8333 | 1.0000 | 0.7639 | 0.3333 | 4.242 | 4.271 | 4.477 |
| EMBEDDING_ONLY | 0.5833 | 0.8333 | 1.0000 | 0.7458 | 0.4444 | 560.919 | 579.325 | 689.891 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5000 | 1.0000 | 1.0000 | 0.7361 | 0.4444 | 13.916 | 14.153 | 14.739 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8333 | 1.0000 | 0.6903 | 0.5556 | 13.282 | 13.283 | 13.856 |

### `EASY`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5833 | 0.9167 | 0.9167 | 0.7361 | 0.1818 | 4.125 | 4.123 | 4.618 |
| EMBEDDING_ONLY | 0.6667 | 0.8333 | 0.9167 | 0.7708 | 0.0909 | 662.401 | 596.266 | 1109.160 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 0.9167 | 0.9167 | 0.8472 | 0.0909 | 13.612 | 13.323 | 15.496 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.9167 | 0.9167 | 0.6898 | 0.1818 | 13.452 | 13.447 | 14.464 |

### `HARD`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6111 | 0.8889 | 0.9444 | 0.7611 | 0.3529 | 4.191 | 4.306 | 4.917 |
| EMBEDDING_ONLY | 0.5556 | 0.7222 | 0.7778 | 0.6620 | 0.4118 | 646.420 | 567.820 | 1185.318 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6111 | 0.8333 | 0.8333 | 0.7269 | 0.3529 | 13.498 | 13.059 | 15.651 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6111 | 0.8889 | 0.9444 | 0.7611 | 0.3529 | 13.462 | 13.317 | 15.318 |

### `MEDIUM`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6111 | 0.7222 | 0.7222 | 0.6709 | 0.1667 | 4.272 | 4.179 | 4.859 |
| EMBEDDING_ONLY | 0.7222 | 0.7778 | 0.8333 | 0.7731 | 0.1667 | 574.707 | 569.438 | 758.230 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6667 | 0.7222 | 0.8333 | 0.7130 | 0.1667 | 13.607 | 13.635 | 15.619 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5556 | 0.7222 | 0.7778 | 0.6497 | 0.1667 | 13.386 | 12.979 | 14.741 |


## Metrics By Match Type

### `EXACT`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6250 | 1.0000 | 1.0000 | 0.7917 | 0.0000 | 4.031 | 3.975 | 4.568 |
| EMBEDDING_ONLY | 0.6250 | 0.8750 | 0.8750 | 0.7500 | 0.0000 | 673.244 | 542.058 | 1192.910 |
| HYBRID_BM25_EMBEDDING_RRF | 0.7500 | 1.0000 | 1.0000 | 0.8750 | 0.0000 | 13.615 | 13.194 | 15.563 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 1.0000 | 1.0000 | 0.7292 | 0.0000 | 13.386 | 13.218 | 14.555 |

### `MIXED`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.5385 | 0.8077 | 0.8846 | 0.6786 | 0.3636 | 4.202 | 4.264 | 4.547 |
| EMBEDDING_ONLY | 0.6538 | 0.8077 | 0.9231 | 0.7660 | 0.3182 | 607.161 | 592.235 | 811.665 |
| HYBRID_BM25_EMBEDDING_RRF | 0.5769 | 0.8846 | 0.9231 | 0.7276 | 0.3182 | 13.765 | 13.617 | 15.434 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.5000 | 0.8077 | 0.9231 | 0.6722 | 0.4091 | 13.390 | 13.290 | 14.476 |

### `SEMANTIC`

| Strategy | Recall@1 | Recall@3 | Recall@5 | MRR | HardNegAboveExpected | AvgLatencyMs | P50LatencyMs | P95LatencyMs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25_ONLY | 0.6923 | 0.8077 | 0.8462 | 0.7615 | 0.2400 | 4.279 | 4.179 | 5.116 |
| EMBEDDING_ONLY | 0.6154 | 0.7308 | 0.8077 | 0.6968 | 0.3200 | 595.692 | 582.091 | 861.691 |
| HYBRID_BM25_EMBEDDING_RRF | 0.6538 | 0.7692 | 0.8077 | 0.7308 | 0.2800 | 13.516 | 13.502 | 15.033 |
| HYBRID_BM25_EMBEDDING_RRF_RERANK | 0.6154 | 0.8077 | 0.8462 | 0.7171 | 0.2800 | 13.417 | 13.145 | 14.940 |


## Recall@5 Miss Analysis

- `v03-hook-001` `BM25_ONLY` query=开头一直讲自己做账号三年，第四秒才说粉丝能少踩什么坑 expected=['hook-pattern-self-intro-delay-v1'] hardNegative=['hook-good-case-authority-fast-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.9434563530497265}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.7258661863112977}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.6897304947150052}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.5644325210301584}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.539163866017192}]
- `v03-hook-004` `BM25_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.8867963503478639}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.8295613557843402}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.7774815830232241}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.6928203230275508}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.647150228929434}]
- `v03-hook-013` `BM25_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3794609894300105}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 0.8638684255813601}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.7548294124240689}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.7258661863112977}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.5911975668985759}]
- `v03-hook-014` `BM25_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.257941804066302}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.0838622059807226}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.7633700367119739}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.7}]
- `v03-hook-019` `BM25_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 1.4363696929192158}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.3867504905630728}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.2229371288986763}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.1230289532557682}, {'knowledgeId': 'structure-pattern-problem-expand-close-v1', 'score': 1.0838622059807226}]
- `v03-structure-012` `BM25_ONLY` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.0}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.9332565252573828}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.8386278693775346}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.7882634225314346}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.6897304947150052}]
- `v03-value-014` `BM25_ONLY` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.0}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.9712858623572641}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.9667364890456636}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.8}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.7107423155935334}]
- `v03-hook-002` `EMBEDDING_ONLY` query=第一句说自己是营养师，下一句马上告诉宝妈怎么避开配料表陷阱 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.32520440763197583}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.30933222417238004}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.30563657058557014}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.2955888102201899}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.27948244706567926}]
- `v03-hook-004` `EMBEDDING_ONLY` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.508196114607645}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.435323902317978}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4270035265106762}, {'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.4194852648947629}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.40567636379788113}]
- `v03-hook-006` `EMBEDDING_ONLY` query=首屏没有明确谁该看、为什么看，也没有冲突点 expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] actualTop5=[{'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.4628743764925104}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.4205552870895717}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.410483417310328}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.40254573554523604}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.39688475356747155}]
- `v03-hook-008` `EMBEDDING_ONLY` query=开场第一句话点名新手妈妈，但后面还要马上接具体困扰 expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4745121511533194}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.4600720840343014}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.453009543918467}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.4460319055511175}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.4060921261104005}]
- `v03-hook-013` `EMBEDDING_ONLY` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.4386738792804992}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.4191770431194992}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.41045975084529546}, {'knowledgeId': 'structure-bad-case-static-talking-v1', 'score': 0.38156558728987827}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.3526127750530062}]
- `v03-hook-014` `EMBEDDING_ONLY` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.43130243693669135}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.37561175437850786}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.35498629579462615}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.3437423555014496}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.33474763765737875}]
- `v03-hook-019` `EMBEDDING_ONLY` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5604008801600513}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.504837887795984}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.4759731150345654}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.4656450212839884}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.45902729015074273}]
- `v03-value-012` `EMBEDDING_ONLY` query=开头有痛点，但整条视频没有回答这个人最后能获得什么改变 expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.5901033145937508}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.4143183501934042}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.3936808730171782}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.37075374667259964}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.36888905301318076}]
- `v03-hook-002` `HYBRID_BM25_EMBEDDING_RRF` query=第一句说自己是营养师，下一句马上告诉宝妈怎么避开配料表陷阱 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.031754032258064516}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.03128054740957967}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03076923076923077}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.029386529386529386}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.02938045560996381}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 0.03252247488101534}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.031544957774465976}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.030834914611005692}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.030798389007344232}, {'knowledgeId': 'value-bad-case-vague-claim-v1', 'score': 0.029910714285714284}]
- `v03-hook-006` `HYBRID_BM25_EMBEDDING_RRF` query=首屏没有明确谁该看、为什么看，也没有冲突点 expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] actualTop5=[{'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.03225806451612903}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.031544957774465976}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.03149801587301587}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.031099324975891997}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.030776515151515152}]
- `v03-hook-013` `HYBRID_BM25_EMBEDDING_RRF` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.03177805800756621}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.031544957774465976}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.0315136476426799}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 0.031024531024531024}, {'knowledgeId': 'hook-bad-case-feature-first-v1', 'score': 0.03057889822595705}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.03252247488101534}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.032266458495966696}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 0.03125763125763126}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 0.03125}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 0.031054405392392875}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 0.03252247488101534}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.03200204813108039}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 0.03177805800756621}, {'knowledgeId': 'value-bad-case-feature-without-benefit-v1', 'score': 0.030798389007344232}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.029910714285714284}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'value-pattern-actionable-advice-v1', 'score': 0.0315136476426799}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 0.0315136476426799}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 0.03131881575727918}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 0.031099324975891997}, {'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 0.031024531024531024}]
- `v03-hook-004` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“别急着买这个”，但立刻给出一个具体踩坑场景 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.3976739900325303}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.3771089709291955}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.2489159175039661}, {'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 1.09342383107089}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 0.9464233890073441}]
- `v03-hook-013` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头说“这三个错误很多人都在犯”，随后马上展示第一个具体错误 expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 2.148171500630517}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.5276232851316278}, {'knowledgeId': 'hook-pattern-target-audience-v1', 'score': 1.096649531024531}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.0921058362369338}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 0.9773866635156958}]
- `v03-hook-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=老师先报职称又马上承诺三分钟帮你判断孩子问题，这种开场不算拖沓 expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] actualTop5=[{'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.848915917503966}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.728395490754031}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.6964390207770081}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.3968749999999999}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.1271306471306473}]
- `v03-hook-019` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=短视频不是没有价值，而是收益点藏得太晚，首屏没人等到后面 expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] actualTop5=[{'knowledgeId': 'hook-pattern-pain-benefit-v2', 'score': 2.298915917503966}, {'knowledgeId': 'value-bad-case-scattered-benefits-v1', 'score': 2.1476510738805823}, {'knowledgeId': 'hook-good-case-visual-proof-v1', 'score': 1.9981310803891448}, {'knowledgeId': 'hook-good-case-authority-fast-v1', 'score': 1.993317895339954}, {'knowledgeId': 'hook-pattern-self-intro-delay-v1', 'score': 1.843703841043231}]
- `v03-structure-012` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=开头承诺解决收纳混乱，正文按原因、方法、检查动作一路推进 expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.5786599011189175}, {'knowledgeId': 'value-pattern-use-scenario-v1', 'score': 1.3774926686217008}, {'knowledgeId': 'hook-rule-first-three-seconds-v1', 'score': 1.276649531024531}, {'knowledgeId': 'hook-bad-case-generic-opening-v1', 'score': 1.2459635136105722}, {'knowledgeId': 'hook-bad-case-empty-suspense-v1', 'score': 1.094620637578384}]
- `v03-value-014` `HYBRID_BM25_EMBEDDING_RRF_RERANK` query=最后让用户收藏检查清单，比突然引导购买更符合这条内容 expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] actualTop5=[{'knowledgeId': 'hook-rule-avoid-late-payoff-v1', 'score': 1.5764091464091463}, {'knowledgeId': 'hook-pattern-curiosity-gap-v1', 'score': 1.5476426799007443}, {'knowledgeId': 'value-pattern-audience-outcome-v1', 'score': 1.547191831630295}, {'knowledgeId': 'structure-rule-opening-transition-v1', 'score': 1.2719589070567985}, {'knowledgeId': 'value-rule-before-after-outcome-v1', 'score': 1.1239352533109104}]
