# Retrieval Miss Analysis

- Dataset version: `video-diagnosis-rag-test-v0.5`
- Corpus version: `v0.3`
- Benchmark mode: `GLOBAL`

## Top 10 Recurring Confused Knowledge Pairs
- `hook-bad-case-feature-first-v1 -> value-bad-case-feature-without-benefit-v1`: 2
- `hook-good-case-authority-fast-v1 -> hook-pattern-self-intro-delay-v1`: 1
- `hook-rule-first-three-seconds-v1 -> hook-bad-case-generic-opening-v1`: 1
- `hook-pattern-curiosity-gap-v1 -> hook-rule-first-three-seconds-v1`: 1
- `hook-pattern-pain-benefit-v2 -> value-bad-case-feature-without-benefit-v1`: 1
- `structure-rule-slow-burn-exception-v1 -> hook-rule-avoid-late-payoff-v1`: 1

## Miss Count By SkillCode
- `hook_analysis`: 4
- `structure_rhythm_analysis`: 2

## Miss Count By ErrorType
- `CROSS_SKILL_CONTAMINATION`: 4
- `HARD_NEGATIVE_CONFUSION`: 6
- `LEXICAL_MISMATCH`: 1
- `MULTI_LABEL_AMBIGUITY`: 2
- `SEMANTIC_BOUNDARY_CONFUSION`: 3
- `UNKNOWN`: 4

## Hard Negative Failure Knowledge IDs
- `value-bad-case-feature-without-benefit-v1`: 2
- `hook-pattern-self-intro-delay-v1`: 1
- `hook-bad-case-generic-opening-v1`: 1
- `hook-rule-first-three-seconds-v1`: 1
- `hook-rule-avoid-late-payoff-v1`: 1

## Suppressed Expected Knowledge IDs
- `hook-bad-case-feature-first-v1`: 2
- `structure-pattern-problem-expand-close-v1`: 2
- `hook-pattern-self-intro-delay-v1`: 1
- `hook-good-case-authority-fast-v1`: 1
- `hook-rule-first-three-seconds-v1`: 1
- `hook-good-case-visual-proof-v1`: 1
- `hook-platform-short-feed-v1`: 1
- `hook-pattern-curiosity-gap-v1`: 1
- `hook-pattern-pain-benefit-v2`: 1
- `structure-rule-slow-burn-exception-v1`: 1

## Query Rows

- `v03-hook-001` `hook_analysis` `UNKNOWN` expected=['hook-pattern-self-intro-delay-v1'] hardNegative=['hook-good-case-authority-fast-v1'] hybridRank=None
- `v03-hook-002` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-good-case-authority-fast-v1'] hardNegative=['hook-pattern-self-intro-delay-v1'] hybridRank=None
- `v03-hook-006` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-rule-first-three-seconds-v1'] hardNegative=['hook-bad-case-generic-opening-v1'] hybridRank=None
- `v03-hook-007` `hook_analysis` `UNKNOWN` expected=['hook-good-case-visual-proof-v1'] hardNegative=['value-good-case-proof-before-claim-v1'] hybridRank=None
- `v03-hook-011` `hook_analysis` `LEXICAL_MISMATCH` expected=['hook-platform-short-feed-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] hybridRank=None
- `v03-hook-012` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-bad-case-feature-first-v1'] hardNegative=['value-bad-case-feature-without-benefit-v1'] hybridRank=None
- `v03-hook-013` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-pattern-curiosity-gap-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] hybridRank=None
- `v03-hook-016` `hook_analysis` `HARD_NEGATIVE_CONFUSION` expected=['hook-bad-case-feature-first-v1', 'hook-pattern-pain-benefit-v2'] hardNegative=['value-bad-case-feature-without-benefit-v1'] hybridRank=None
- `v03-structure-001` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] hybridRank=None
- `v03-structure-007` `structure_rhythm_analysis` `HARD_NEGATIVE_CONFUSION` expected=['structure-rule-slow-burn-exception-v1'] hardNegative=['hook-rule-avoid-late-payoff-v1'] hybridRank=None
- `v03-structure-010` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-rule-midpoint-retention-v1'] hardNegative=['value-rule-specificity-v1'] hybridRank=None
- `v03-structure-012` `structure_rhythm_analysis` `CROSS_SKILL_CONTAMINATION` expected=['structure-pattern-problem-expand-close-v1'] hardNegative=['value-pattern-actionable-advice-v1'] hybridRank=None
- `v03-structure-017` `structure_rhythm_analysis` `MULTI_LABEL_AMBIGUITY` expected=['structure-rule-opening-transition-v1', 'structure-bad-case-topic-jump-v1'] hardNegative=['hook-rule-first-three-seconds-v1'] hybridRank=None
- `v03-structure-019` `structure_rhythm_analysis` `SEMANTIC_BOUNDARY_CONFUSION` expected=['structure-rule-slow-burn-exception-v1'] hardNegative=['hook-pattern-curiosity-gap-v1'] hybridRank=None
- `v03-value-003` `value_delivery_analysis` `UNKNOWN` expected=['value-pattern-actionable-advice-v1'] hardNegative=['value-rule-call-to-action-fit-v1'] hybridRank=None
- `v03-value-004` `value_delivery_analysis` `CROSS_SKILL_CONTAMINATION` expected=['value-rule-specificity-v1'] hardNegative=['structure-rule-midpoint-retention-v1'] hybridRank=None
- `v03-value-007` `value_delivery_analysis` `UNKNOWN` expected=['value-good-case-proof-before-claim-v1'] hardNegative=['hook-good-case-visual-proof-v1'] hybridRank=None
- `v03-value-009` `value_delivery_analysis` `SEMANTIC_BOUNDARY_CONFUSION` expected=['value-rule-call-to-action-fit-v1'] hardNegative=['value-pattern-actionable-advice-v1'] hybridRank=None
- `v03-value-016` `value_delivery_analysis` `MULTI_LABEL_AMBIGUITY` expected=['value-pattern-actionable-advice-v1', 'value-good-case-step-by-step-v1'] hardNegative=['structure-good-case-rhythm-marker-v1'] hybridRank=None
- `v03-value-020` `value_delivery_analysis` `SEMANTIC_BOUNDARY_CONFUSION` expected=['value-bad-case-scattered-benefits-v1'] hardNegative=['structure-bad-case-topic-jump-v1'] hybridRank=None
