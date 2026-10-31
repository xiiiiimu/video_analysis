# Agent Architecture Ablation Report

## A. Evaluation Metadata

- Dataset version: `video-diagnosis-agent-eval-v0.3-verified`
- Dataset hash before: `FBBF7AF33D507CECBFFBAE2CFB681821C84B1D40A18C796202C7FC15BACE140D`
- Dataset hash after: `FBBF7AF33D507CECBFFBAE2CFB681821C84B1D40A18C796202C7FC15BACE140D`
- Dataset modified during run: `False`
- Evaluation type: `single-run architecture ablation`
- Executions: `24 cases × 2 architectures = 48`
- Model config: `{"provider": "deepseek", "model": "deepseek-v4-flash", "baseUrl": "https://api.deepseek.com", "temperature": 0.2}`
- Token usage: `unavailable`

## B/C/D. All 24 Architecture Metrics

| Architecture | Precision | Recall | F1 | Runtime Success | EvidenceRefPresence | Avg Latency ms | Median Latency ms | Model Calls | Agent Calls | Tool Calls | Handoff Count | Replan Count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PARALLEL_SKILLS | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.4583 | 40325.0 | 42929.8 | 3.46 | 17.12 | 29.33 | 0.00 | 0.00 |
| SPECIALIST_MULTI_AGENT | 0.0417 | 0.0417 | 0.0417 | 0.0000 | 0.4583 | 35051.3 | 36151.0 | 3.00 | 16.12 | 28.25 | 0.75 | 0.75 |
| DELTA multi-parallel | 0.0417 | 0.0417 | 0.0417 | 0.0000 | 0.0000 | -5273.7 | -6778.8 | -0.46 | -1.00 | -1.08 | 0.75 | 0.75 |

## E. Cross-Skill 6 Cases

| Metric | Parallel | Multi-Agent |
|---|---:|---:|
| findingF1 | 0.0000 | 0.0000 |
| executionSuccessRate | 0.0000 | 0.0000 |
| handoffSuccessRate | 0.0000 | 0.0000 |
| endToEndLatencyMs | 46974.7206 | 38722.7367 |
| modelCallCount | 3.3333 | 3.1667 |
| agentCallCount | 16.6667 | 16.6667 |
| toolCallCount | 28.6667 | 29.0000 |
| handoffCount | 0.0000 | 0.8333 |
| replanCount | 0.0000 | 0.8333 |
- Handoff success: `3/6`
- Wrong handoff: `2`
- Missed handoff: `1`

## F. Normal 18 Cases

| Metric | Parallel | Multi-Agent |
|---|---:|---:|
| findingF1 | 0.0000 | 0.0556 |
| executionSuccessRate | 0.0000 | 0.0000 |
| endToEndLatencyMs | 38108.4181 | 33827.4784 |
| modelCallCount | 3.5000 | 2.9444 |
| agentCallCount | 17.2778 | 15.9444 |
| toolCallCount | 29.5556 | 28.0000 |
- Unnecessary handoff count: `13`
- Unnecessary handoff rate: `0.7222`

## G. Handoff Analysis

- `agent-case-hook-value-boundary-001` expected=`value_delivery` actual=`['hook_analysis']` status=`WRONG_HANDOFF`
- `agent-case-visual-proof-value-001` expected=`value_delivery` actual=`['value_delivery']` status=`CORRECT_HANDOFF`
- `agent-case-cross-hook-value-002` expected=`value_delivery` actual=`[]` status=`MISSED_HANDOFF`
- `agent-case-cross-hook-structure-001` expected=`structure_rhythm_analysis` actual=`['structure_rhythm_analysis']` status=`CORRECT_HANDOFF`
- `agent-case-cross-hook-structure-002` expected=`structure_rhythm_analysis` actual=`['structure_rhythm_analysis']` status=`CORRECT_HANDOFF`
- `agent-case-cross-structure-value-001` expected=`value_delivery` actual=`['structure_rhythm_analysis']` status=`WRONG_HANDOFF`
- `agent-case-hook-clear-positive-001` actual=`['value_delivery']` status=`UNNECESSARY_HANDOFF`
- `agent-case-hook-clear-negative-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-hook-hard-negative-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-hook-curiosity-negative-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-hook-transition-001` actual=`['value_delivery']` status=`UNNECESSARY_HANDOFF`
- `agent-case-structure-clear-positive-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-structure-clear-negative-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-structure-hard-negative-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-structure-static-density-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-structure-example-driven-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-value-clear-positive-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-value-hard-negative-001` actual=`['structure_rhythm_analysis']` status=`UNNECESSARY_HANDOFF`
- `agent-case-value-proof-positive-001` actual=`['hook_analysis']` status=`UNNECESSARY_HANDOFF`

## H. Abstention Analysis

- `PARALLEL_SKILLS`: `0.0/3.0` accuracy=`0.0000`
- `SPECIALIST_MULTI_AGENT`: `1.0/3.0` accuracy=`0.3333`

## I. Runtime Failure Analysis

- `PARALLEL_SKILLS` failures: `24` reasons=`{"MISSING_SKILL_FINDING": 20, "UNRESOLVED_EVIDENCE_GAP": 23, "LOW_CONFIDENCE": 12}`
- `SPECIALIST_MULTI_AGENT` failures: `24` reasons=`{"MISSING_SKILL_FINDING": 20, "UNRESOLVED_EVIDENCE_GAP": 10, "LOW_CONFIDENCE": 11}`

## J. Efficiency

- `PARALLEL_SKILLS` avg latency=`40325.0ms`, median=`42929.8ms`, model calls=`3.46`, agent calls=`17.12`, tool calls=`29.33`
- `SPECIALIST_MULTI_AGENT` avg latency=`35051.3ms`, median=`36151.0ms`, model calls=`3.00`, agent calls=`16.12`, tool calls=`28.25`

## Conclusion

Multi-Agent improved measured Finding Quality and produced some correct handoff/replan behavior, with additional orchestration cost.