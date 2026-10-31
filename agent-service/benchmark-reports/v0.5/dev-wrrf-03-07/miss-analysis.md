# Retrieval Miss Analysis

- Dataset version: `video-diagnosis-rag-dev-v0.5`
- Corpus version: `v0.3`
- Benchmark mode: `GLOBAL`

## Top 10 Recurring Confused Knowledge Pairs
- `value-bad-case-feature-without-benefit-v1 -> hook-bad-case-feature-first-v1`: 2
- `hook-pattern-curiosity-gap-v1 -> hook-bad-case-empty-suspense-v1`: 1
- `hook-good-case-authority-fast-v1 -> hook-pattern-self-intro-delay-v1`: 1
- `hook-pattern-target-audience-v1 -> value-pattern-use-scenario-v1`: 1
- `hook-rule-first-three-seconds-v1 -> value-pattern-use-scenario-v1`: 1
- `hook-rule-avoid-late-payoff-v1 -> value-pattern-audience-outcome-v1`: 1
- `structure-rule-density-scene-change-v1 -> structure-bad-case-static-talking-v1`: 1
- `structure-pattern-contrast-before-after-v1 -> value-rule-before-after-outcome-v1`: 1
- `structure-rule-midpoint-retention-v1 -> structure-rule-density-scene-change-v1`: 1
- `value-pattern-audience-outcome-v1 -> hook-pattern-pain-benefit-v2`: 1

## Miss Count By SkillCode
- `hook_analysis`: 4
- `value_delivery_analysis`: 2

## Miss Count By ErrorType
- `CROSS_SKILL_CONTAMINATION`: 13
- `HARD_NEGATIVE_CONFUSION`: 7
- `MULTI_LABEL_AMBIGUITY`: 5
- `RERANK_INVERSION`: 8
- `SEMANTIC_BOUNDARY_CONFUSION`: 3
- `UNKNOWN`: 4

## Hard Negative Failure Knowledge IDs
- `hook-bad-case-feature-first-v1`: 2
- `hook-bad-case-empty-suspense-v1`: 1
- `hook-pattern-self-intro-delay-v1`: 1
- `value-pattern-use-scenario-v1`: 1
- `value-pattern-audience-outcome-v1`: 1
- `structure-bad-case-static-talking-v1`: 1
- `value-rule-before-after-outcome-v1`: 1
- `structure-rule-density-scene-change-v1`: 1
- `hook-pattern-pain-benefit-v2`: 1
- `value-pattern-actionable-advice-v1`: 1

## Suppressed Expected Knowledge IDs
- `hook-pattern-target-audience-v1`: 2
- `hook-rule-avoid-late-payoff-v1`: 2
- `structure-bad-case-topic-jump-v1`: 2
- `value-bad-case-feature-without-benefit-v1`: 2
- `value-good-case-proof-before-claim-v1`: 2
- `hook-pattern-pain-benefit-v2`: 1
- `hook-pattern-curiosity-gap-v1`: 1
- `hook-bad-case-empty-suspense-v1`: 1
- `hook-bad-case-generic-opening-v1`: 1
- `hook-good-case-authority-fast-v1`: 1

## Query Rows

- `v03-hook-003` `hook_analysis` `RERANK_INVERSION` expected=['hook-pattern-pain-benefit-v2'] hardNegative=['value-pattern-audience-outcome-v1'] hybridRank=1
- `v03-hook-004` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] hybridRank=None
- `v03-hook-005` `hook_analysis` `UNKNOWN` expected=['hook-bad-case-empty-suspense-v1'] hardNegative=['hook-pattern-curiosity-gap-v1'] hybridRank=1
- `v03-hook-008` `hook_analysis` `CROSS_SKILL_CONTAMINATION` expected=['hook-pattern-target-audience-v1'] hardNegative=['value-pattern-use-scenario-v1'] hybridRank=5
- `v03-hook-009` `hook_analysis` `SEMANTIC_BOUNDARY_CONFUSION` expected=['hook-bad-case-generic-opening-v1'] hardNegative=['structure-pattern-topic-list-v1'] hybridRank=1
- `v03-hook-010` `hook_analysis` `UNKNOWN` expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['structure-rule-slow-burn-exception-v1'] hybridRank=1
- `v03-hook-014` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] hybridRank=None
- `v03-hook-015` `hook_analysis` `CROSS_SKILL_CONTAMINATION` expected=['hook-good-case-visual-proof-v1'] hardNegative=['value-good-case-proof-before-claim-v1'] hybridRank=1
- `v03-hook-017` `hook_analysis` `RERANK_INVERSION` expected=['hook-pattern-target-audience-v1', 'hook-rule-first-three-seconds-v1'] hardNegative=['value-pattern-use-scenario-v1'] hybridRank=1
- `v03-hook-018` `hook_analysis` `MULTI_LABEL_AMBIGUITY` expected=['hook-bad-case-generic-opening-v1', 'hook-pattern-self-intro-delay-v1'] hardNegative=[] hybridRank=1
- `v03-hook-019` `hook_analysis` `RERANK_INVERSION` expected=['hook-rule-avoid-late-payoff-v1'] hardNegative=['value-pattern-audience-outcome-v1'] hybridRank=4
- `v03-hook-020` `hook_analysis` `MULTI_LABEL_AMBIGUITY` expected=['hook-good-case-authority-fast-v1', 'hook-pattern-self-intro-delay-v1'] hardNegative=[] hybridRank=1
- `v03-structure-002` `structure_rhythm_analysis` `SEMANTIC_BOUNDARY_CONFUSION` expected=['structure-pattern-topic-list-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] hybridRank=1
- `v03-structure-003` `structure_rhythm_analysis` `UNKNOWN` expected=['structure-rule-opening-transition-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] hybridRank=1
- `v03-structure-004` `structure_rhythm_analysis` `HARD_NEGATIVE_CONFUSION` expected=['structure-rule-density-scene-change-v1'] hardNegative=['structure-bad-case-static-talking-v1'] hybridRank=3
- `v03-structure-005` `structure_rhythm_analysis` `UNKNOWN` expected=['structure-bad-case-static-talking-v1'] hardNegative=['structure-rule-density-scene-change-v1'] hybridRank=1
- `v03-structure-006` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-good-case-rhythm-marker-v1'] hardNegative=['value-good-case-step-by-step-v1'] hybridRank=1
- `v03-structure-008` `structure_rhythm_analysis` `HARD_NEGATIVE_CONFUSION` expected=['structure-pattern-contrast-before-after-v1'] hardNegative=['value-rule-before-after-outcome-v1'] hybridRank=2
- `v03-structure-009` `structure_rhythm_analysis` `RERANK_INVERSION` expected=['structure-bad-case-topic-jump-v1'] hardNegative=['value-bad-case-scattered-benefits-v1'] hybridRank=1
- `v03-structure-011` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-good-case-example-driven-v1'] hardNegative=['value-good-case-proof-before-claim-v1'] hybridRank=1
- `v03-structure-013` `structure_rhythm_analysis` `MULTI_LABEL_AMBIGUITY` expected=['structure-good-case-rhythm-marker-v1', 'structure-pattern-topic-list-v1'] hardNegative=[] hybridRank=1
- `v03-structure-014` `structure_rhythm_analysis` `HARD_NEGATIVE_CONFUSION` expected=['structure-rule-midpoint-retention-v1'] hardNegative=['structure-rule-density-scene-change-v1'] hybridRank=3
- `v03-structure-015` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-pattern-contrast-before-after-v1'] hardNegative=['value-rule-before-after-outcome-v1'] hybridRank=1
- `v03-structure-016` `structure_rhythm_analysis` `MULTI_LABEL_AMBIGUITY` expected=['structure-bad-case-static-talking-v1', 'structure-rule-density-scene-change-v1'] hardNegative=[] hybridRank=1
- `v03-structure-018` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-bad-case-topic-jump-v1'] hardNegative=['value-bad-case-scattered-benefits-v1'] hybridRank=1
- `v03-structure-020` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-good-case-example-driven-v1'] hardNegative=['value-good-case-proof-before-claim-v1'] hybridRank=1
- `v03-value-001` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] hybridRank=1
- `v03-value-002` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-pattern-use-scenario-v1'] hardNegative=['hook-pattern-target-audience-v1'] hybridRank=1
- `v03-value-005` `value_delivery_analysis` `RERANK_INVERSION` expected=['value-bad-case-feature-without-benefit-v1'] hardNegative=['hook-bad-case-feature-first-v1'] hybridRank=1
- `v03-value-006` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-bad-case-vague-claim-v1'] hardNegative=['hook-bad-case-empty-suspense-v1'] hybridRank=1
- `v03-value-008` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-good-case-step-by-step-v1'] hardNegative=['structure-good-case-rhythm-marker-v1'] hybridRank=1
- `v03-value-010` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-bad-case-scattered-benefits-v1'] hardNegative=['structure-bad-case-topic-jump-v1'] hybridRank=3
- `v03-value-011` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-rule-before-after-outcome-v1'] hardNegative=['structure-pattern-contrast-before-after-v1'] hybridRank=1
- `v03-value-012` `value_delivery_analysis` `HARD_NEGATIVE_CONFUSION` expected=['value-pattern-audience-outcome-v1'] hardNegative=['hook-pattern-pain-benefit-v2'] hybridRank=10
- `v03-value-013` `value_delivery_analysis` `SEMANTIC_BOUNDARY_CONFUSION` expected=['value-pattern-use-scenario-v1'] hardNegative=['value-rule-specificity-v1'] hybridRank=1
- `v03-value-014` `value_delivery_analysis` `RERANK_INVERSION` expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] hybridRank=6
- `v03-value-015` `value_delivery_analysis` `HARD_NEGATIVE_CONFUSION` expected=['value-good-case-proof-before-claim-v1'] hardNegative=['structure-good-case-example-driven-v1'] hybridRank=2
- `v03-value-017` `value_delivery_analysis` `RERANK_INVERSION` expected=['value-bad-case-feature-without-benefit-v1'] hardNegative=['hook-bad-case-feature-first-v1'] hybridRank=1
- `v03-value-018` `value_delivery_analysis` `MULTI_LABEL_AMBIGUITY` expected=['value-rule-specificity-v1', 'value-bad-case-vague-claim-v1'] hardNegative=[] hybridRank=3
- `v03-value-019` `value_delivery_analysis` `RERANK_INVERSION` expected=['value-rule-before-after-outcome-v1', 'value-good-case-proof-before-claim-v1'] hardNegative=['structure-pattern-contrast-before-after-v1'] hybridRank=2
