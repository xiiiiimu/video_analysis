# Agent Evaluation Golden Case Review

- Dataset version: `video-diagnosis-agent-eval-v0.3-verified`
- Dataset role: `EVAL_CANDIDATE`
- Review status: `24 / 24 VERIFIED`
- Rule: only human-reviewed cases may be changed to `VERIFIED`.

## agent-case-hook-value-boundary-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `cross_skill_ambiguity`
- Case type: `cross_skill_ambiguity`
- Candidate only: `False`

### Evidence

- ASR: 前三秒说新品升级了三种功能，第四秒才解释能帮用户少走弯路。
- OCR: 升级版 / 三大功能 / 省时间
- Metadata: duration=18s; opening_text_visible=0-4s; benefit_statement_start=4.2s
- Frame / Knowledge refs: ASR:agent-hv-001, OCR:agent-hv-001, META:agent-hv-001, KNOWLEDGE:hook-pattern-pain-benefit-v2, KNOWLEDGE:value-pattern-audience-outcome-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `opening_value_boundary`
- Label: 前三秒主要展示产品功能升级，显式用户收益直到约 4.2 秒才出现，因此开场的用户价值表达存在延迟。
- Candidate Evidence Refs: ASR:agent-hv-001, OCR:agent-hv-001, META:agent-hv-001
- Acceptable Variants: opening feature claim before explicit benefit, hook value boundary ambiguous

- Cross-Skill Ambiguity? `True`
- Expected Handoff? `value_delivery`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [x] Cross-skill 标记正确

Final Finding:

前三秒主要展示产品功能升级，显式用户收益直到约 4.2 秒才出现，因此开场的用户价值表达存在延迟。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-visual-proof-value-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `cross_skill_ambiguity`
- Case type: `cross_skill_ambiguity`
- Candidate only: `False`

### Evidence

- ASR: 开头展示一张夸张前后对比图，但旁白只说你看这个变化很明显，没有解释变化对用户有什么用。
- OCR: 前后对比 / 变化明显
- Metadata: duration=22s; visual_proof_start=0.5s; explicit_outcome_absent=true
- Frame / Knowledge refs: ASR:agent-hv-002, OCR:agent-hv-002, FRAME:agent-hv-002, KNOWLEDGE:hook-good-case-visual-proof-v1, KNOWLEDGE:value-good-case-proof-before-claim-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `visual_attention_without_value`
- Label: 首屏展示了明显的前后对比，但旁白和画面文字没有说明这种变化对应什么用户结果，因此视觉证据尚未被转化为清晰的价值表达。
- Candidate Evidence Refs: ASR:agent-hv-002, OCR:agent-hv-002, FRAME:agent-hv-002
- Acceptable Variants: visual proof helps hook but does not prove value, attention evidence lacks user outcome

- Cross-Skill Ambiguity? `True`
- Expected Handoff? `value_delivery`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [x] Cross-skill 标记正确

Final Finding:

首屏展示了明显的前后对比，但旁白和画面文字没有说明这种变化对应什么用户结果，因此视觉证据尚未被转化为清晰的价值表达。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-hook-clear-positive-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_FIXTURE`
- Primary skill: `hook_analysis`
- Case type: `clear_positive`
- Candidate only: `False`

### Evidence

- ASR: 
- OCR: 前三秒直接给出痛点
- Metadata: {"duration":12}
- Frame / Knowledge refs: OCR:target-1, FRAME:target-1, KNOWLEDGE:hook-pattern-opening-pain-v1
- Reference evidence count: `1`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `strong_opening_hook`
- Label: 前三秒直接给出用户痛点，开场信息明确，能够形成清晰的 Hook 线索。
- Candidate Evidence Refs: OCR:target-1, FRAME:target-1
- Acceptable Variants: opening hook is clear, first three seconds show direct pain point

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

前三秒直接给出用户痛点，开场信息明确，能够形成清晰的 Hook 线索。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-hook-clear-negative-001

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `hook_analysis`
- Case type: `clear_negative`
- Candidate only: `False`

### Evidence

- ASR: 大家好我是小林，我做这个行业已经八年了，今天给大家分享一下我的经历。
- OCR: 8年经验 / 我的经历
- Metadata: duration=30s; benefit_statement_start=8.1s
- Frame / Knowledge refs: ASR:agent-hook-002, OCR:agent-hook-002, META:agent-hook-002, KNOWLEDGE:hook-pattern-self-intro-delay-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `self_intro_delay`
- Label: 开头长时间介绍自己，用户能获得什么出现太晚，容易削弱前三秒停留。
- Candidate Evidence Refs: ASR:agent-hook-002, OCR:agent-hook-002, META:agent-hook-002
- Acceptable Variants: delayed user benefit due to self introduction, authority intro delays hook

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

开头长时间介绍自己，用户能获得什么出现太晚，容易削弱前三秒停留。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-hook-hard-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `hook_analysis`
- Case type: `hard_negative`
- Candidate only: `False`

### Evidence

- ASR: 我做这行八年，踩过这三个坑，所以今天直接告诉你怎么避开。
- OCR: 8年经验 / 3个坑 / 直接避开
- Metadata: duration=25s; authority_claim=0.6s; user_benefit=2.2s
- Frame / Knowledge refs: ASR:agent-hook-003, OCR:agent-hook-003, META:agent-hook-003, KNOWLEDGE:hook-good-case-authority-fast-v1, KNOWLEDGE:hook-pattern-self-intro-delay-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `authority_fast_hook`
- Label: 虽然出现了资历信息，但资历马上服务于用户避坑收益，不应误判为自我介绍拖延。
- Candidate Evidence Refs: ASR:agent-hook-003, OCR:agent-hook-003, META:agent-hook-003
- Acceptable Variants: authority supports immediate benefit, not self intro delay

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

虽然出现了资历信息，但资历马上服务于用户避坑收益，不应误判为自我介绍拖延。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-hook-insufficient-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_FIXTURE`
- Primary skill: `hook_analysis`
- Case type: `insufficient_evidence`
- Candidate only: `False`

### Evidence

- ASR: 
- OCR: 
- Metadata: 
- Frame / Knowledge refs: 
- Reference evidence count: `0`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `evidence_gap`
- Label: 缺少前三秒画面文字、关键帧和 ASR，不能强行判断 Hook 强弱，应输出低置信或 evidence gap。
- Candidate Evidence Refs: 
- Acceptable Variants: insufficient opening evidence, abstain until frame text or ASR is available

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

缺少前三秒画面文字、关键帧和 ASR，不能强行判断 Hook 强弱，应输出低置信或 evidence gap。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-hook-curiosity-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `hook_analysis`
- Case type: `clear_negative`
- Candidate only: `False`

### Evidence

- ASR: 很多人都不知道这个秘密，看到最后你就懂了。
- OCR: 99%的人不知道 / 看到最后
- Metadata: duration=19s; concrete_topic_start=7.0s
- Frame / Knowledge refs: ASR:agent-hook-005, OCR:agent-hook-005, META:agent-hook-005, KNOWLEDGE:hook-bad-case-empty-suspense-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `empty_suspense`
- Label: 开头使用悬念词但没有给出具体对象或收益，属于空悬念，停留理由不稳定。
- Candidate Evidence Refs: ASR:agent-hook-005, OCR:agent-hook-005, META:agent-hook-005
- Acceptable Variants: empty suspense without concrete payoff, curiosity hook lacks object

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

开头使用悬念词但没有给出具体对象或收益，属于空悬念，停留理由不稳定。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-hook-transition-001

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `hook_analysis`
- Case type: `conflict_case`
- Candidate only: `False`

### Evidence

- ASR: 别急，先看这个结果，后面我再拆为什么。
- OCR: 先看结果
- Metadata: duration=28s; result_visual=0.7s; explanation_start=5.6s
- Frame / Knowledge refs: ASR:agent-hook-006, OCR:agent-hook-006, FRAME:agent-hook-006, KNOWLEDGE:hook-good-case-visual-proof-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `hook_analysis`
- Type: `visual_result_hook`
- Label: 首屏先展示结果画面，解释在约 5.6 秒后才开始，因此不能仅因解释延后就判断开场缺少 Hook；该开场主要依赖结果展示建立初始吸引。
- Candidate Evidence Refs: ASR:agent-hook-006, OCR:agent-hook-006, FRAME:agent-hook-006
- Acceptable Variants: visual result creates initial hook, opening transition relies on result proof

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

首屏先展示结果画面，解释在约 5.6 秒后才开始，因此不能仅因解释延后就判断开场缺少 Hook；该开场主要依赖结果展示建立初始吸引。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-structure-clear-positive-001

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `structure_rhythm_analysis`
- Case type: `clear_positive`
- Candidate only: `False`

### Evidence

- ASR: 先看问题，再看原因，最后给你三个动作。
- OCR: 问题-原因-动作
- Metadata: duration=34s; segment_count=3; scene_changes=5; midpoint_summary=true
- Frame / Knowledge refs: ASR:agent-structure-001, OCR:agent-structure-001, META:agent-structure-001, KNOWLEDGE:structure-rule-midpoint-retention-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `clear_structure_flow`
- Label: 视频按问题、原因、动作推进，中段有承接，结构路径清晰。
- Candidate Evidence Refs: ASR:agent-structure-001, OCR:agent-structure-001, META:agent-structure-001
- Acceptable Variants: clear problem-cause-action flow, midpoint transition supports retention

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

视频按问题、原因、动作推进，中段有承接，结构路径清晰。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-structure-clear-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `structure_rhythm_analysis`
- Case type: `clear_negative`
- Candidate only: `False`

### Evidence

- ASR: 第一个建议是选题，第二个是剪辑，第三个又回到选题，后面再讲账号定位。
- OCR: 选题 / 剪辑 / 选题 / 定位
- Metadata: duration=42s; topic_jumps=4; segment_order_repeats=true
- Frame / Knowledge refs: ASR:agent-structure-002, OCR:agent-structure-002, META:agent-structure-002, KNOWLEDGE:structure-bad-case-topic-jump-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `topic_jump`
- Label: 内容多次跳回同一主题，段落推进不稳定，影响结构节奏判断。
- Candidate Evidence Refs: ASR:agent-structure-002, OCR:agent-structure-002, META:agent-structure-002
- Acceptable Variants: topic order is scattered, structure repeats and jumps

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

内容多次跳回同一主题，段落推进不稳定，影响结构节奏判断。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-structure-hard-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `structure_rhythm_analysis`
- Case type: `hard_negative`
- Candidate only: `False`

### Evidence

- ASR: 先展示改造前，再展示改造后，然后按三个步骤解释中间怎么做。
- OCR: 前 / 后 / 三步拆解
- Metadata: duration=38s; before_after_visual=0-5s; process_steps=3
- Frame / Knowledge refs: ASR:agent-structure-003, OCR:agent-structure-003, META:agent-structure-003, KNOWLEDGE:structure-pattern-contrast-before-after-v1, KNOWLEDGE:value-rule-before-after-outcome-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `before_after_structure`
- Label: 视频先展示改造前后结果，再按三个步骤解释过程，前后对比在这里构成了明确的内容组织顺序和结构递进。
- Candidate Evidence Refs: ASR:agent-structure-003, OCR:agent-structure-003, META:agent-structure-003
- Acceptable Variants: before-after organizes the explanation, structure sequence uses contrast

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

视频先展示改造前后结果，再按三个步骤解释过程，前后对比在这里构成了明确的内容组织顺序和结构递进。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-structure-insufficient-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_FIXTURE`
- Primary skill: `structure_rhythm_analysis`
- Case type: `insufficient_evidence`
- Candidate only: `False`

### Evidence

- ASR: 
- OCR: 
- Metadata: 
- Frame / Knowledge refs: FRAME:agent-structure-004
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `evidence_gap`
- Label: 只有一个关键帧，缺少 ASR、镜头节奏和时长信息，不能稳定判断结构节奏。
- Candidate Evidence Refs: FRAME:agent-structure-004
- Acceptable Variants: insufficient rhythm metadata, needs transcript or scene metadata

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

只有一个关键帧，缺少 ASR、镜头节奏和时长信息，不能稳定判断结构节奏。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-structure-static-density-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `structure_rhythm_analysis`
- Case type: `clear_negative`
- Candidate only: `False`

### Evidence

- ASR: 今天我从四个方面给你讲，第一点很重要，第二点也重要，第三点还是很关键。
- OCR: 四个重点
- Metadata: duration=45s; scene_changes=0; face_talking_head=true; on_screen_text_changes=1
- Frame / Knowledge refs: ASR:agent-structure-005, OCR:agent-structure-005, META:agent-structure-005, KNOWLEDGE:structure-bad-case-static-talking-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `static_talking_low_density`
- Label: 长时间静态口播且画面信息变化少，节奏密度不足。
- Candidate Evidence Refs: ASR:agent-structure-005, OCR:agent-structure-005, META:agent-structure-005
- Acceptable Variants: static talking head reduces rhythm, low scene density

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

长时间静态口播且画面信息变化少，节奏密度不足。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-structure-example-driven-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `structure_rhythm_analysis`
- Case type: `clear_positive`
- Candidate only: `False`

### Evidence

- ASR: 先给你看一个真实例子，再从这个例子里拆出三个步骤。
- OCR: 案例 -> 三步
- Metadata: duration=36s; example_start=0.8s; steps_start=8.4s
- Frame / Knowledge refs: ASR:agent-structure-006, OCR:agent-structure-006, META:agent-structure-006, KNOWLEDGE:structure-good-case-example-driven-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `example_driven_structure`
- Label: 先用例子建立上下文，再从例子拆步骤，结构承接清楚。
- Candidate Evidence Refs: ASR:agent-structure-006, OCR:agent-structure-006, META:agent-structure-006
- Acceptable Variants: example drives structure, case-to-steps flow

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

先用例子建立上下文，再从例子拆步骤，结构承接清楚。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-value-clear-positive-001

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `value_delivery_analysis`
- Case type: `clear_positive`
- Candidate only: `False`

### Evidence

- ASR: 看完你能直接拿走一个选题模板，今晚就能改你的第一条视频。
- OCR: 选题模板 / 今晚可用
- Metadata: duration=24s; outcome_statement_start=1.5s; action_steps=3
- Frame / Knowledge refs: ASR:agent-value-001, OCR:agent-value-001, META:agent-value-001, KNOWLEDGE:value-pattern-actionable-advice-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `actionable_value`
- Label: 价值表达具体，明确说明用户能拿走模板并立即执行。
- Candidate Evidence Refs: ASR:agent-value-001, OCR:agent-value-001, META:agent-value-001
- Acceptable Variants: clear actionable outcome, specific user takeaway

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

价值表达具体，明确说明用户能拿走模板并立即执行。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-value-clear-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `value_delivery_analysis`
- Case type: `clear_negative`
- Candidate only: `False`

### Evidence

- ASR: 这个功能很强大，体验也很顺滑，整体升级很多。
- OCR: 强大 / 顺滑 / 升级
- Metadata: duration=20s; feature_terms=5; explicit_user_outcome=0
- Frame / Knowledge refs: ASR:agent-value-002, OCR:agent-value-002, META:agent-value-002, KNOWLEDGE:value-bad-case-feature-without-benefit-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `feature_without_benefit`
- Label: 只描述功能和体验，没有翻译成用户收益，价值交付不清晰。
- Candidate Evidence Refs: ASR:agent-value-002, OCR:agent-value-002, META:agent-value-002
- Acceptable Variants: feature claims lack user benefit, value outcome absent

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

只描述功能和体验，没有翻译成用户收益，价值交付不清晰。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-value-hard-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `value_delivery_analysis`
- Case type: `hard_negative`
- Candidate only: `False`

### Evidence

- ASR: 最后点主页领表格，但前面已经教完三个判断标准。
- OCR: 三个标准 / 主页领表格
- Metadata: duration=32s; advice_steps=3; cta_start=29s
- Frame / Knowledge refs: ASR:agent-value-003, OCR:agent-value-003, META:agent-value-003, KNOWLEDGE:value-pattern-actionable-advice-v1, KNOWLEDGE:value-rule-call-to-action-fit-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `actionable_advice_with_fit_cta`
- Label: 主体内容已经给出可执行标准，结尾 CTA 与前文价值一致，不应误判为只有引流没有价值。
- Candidate Evidence Refs: ASR:agent-value-003, OCR:agent-value-003, META:agent-value-003
- Acceptable Variants: CTA fits delivered advice, actionable content precedes call to action

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

主体内容已经给出可执行标准，结尾 CTA 与前文价值一致，不应误判为只有引流没有价值。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-value-insufficient-001

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `value_delivery_analysis`
- Case type: `insufficient_evidence`
- Candidate only: `False`

### Evidence

- ASR: 
- OCR: 第2步
- Metadata: duration=15s; transcript_missing=true; partial_frame_text=true
- Frame / Knowledge refs: OCR:agent-value-004, META:agent-value-004
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `evidence_gap`
- Label: 只有局部步骤文字，缺少上下文和完整 ASR，不能稳定判断价值是否完整交付。
- Candidate Evidence Refs: OCR:agent-value-004, META:agent-value-004
- Acceptable Variants: insufficient value context, needs full transcript before value judgment

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

只有局部步骤文字，缺少上下文和完整 ASR，不能稳定判断价值是否完整交付。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-value-proof-positive-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `value_delivery_analysis`
- Case type: `clear_positive`
- Candidate only: `False`

### Evidence

- ASR: 我先给你看后台数据，再说为什么这个方法能让转化率提高。
- OCR: 转化率 +18%
- Metadata: duration=27s; proof_before_claim=true; metric_visible=0.9s
- Frame / Knowledge refs: ASR:agent-value-005, OCR:agent-value-005, FRAME:agent-value-005, KNOWLEDGE:value-good-case-proof-before-claim-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `proof_before_claim`
- Label: 先展示数据证据再解释价值主张，价值可信度有证据支撑。
- Candidate Evidence Refs: ASR:agent-value-005, OCR:agent-value-005, FRAME:agent-value-005
- Acceptable Variants: proof supports value claim, evidence precedes claim

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

先展示数据证据再解释价值主张，价值可信度有证据支撑。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-value-specificity-negative-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `value_delivery_analysis`
- Case type: `clear_negative`
- Candidate only: `False`

### Evidence

- ASR: 这个方法能提升很多，让你的内容更好，效果也会更明显。
- OCR: 提升很多 / 效果明显
- Metadata: duration=21s; numeric_metric_absent=true; audience_absent=true
- Frame / Knowledge refs: ASR:agent-value-006, OCR:agent-value-006, META:agent-value-006, KNOWLEDGE:value-rule-specificity-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `low_specificity`
- Label: 价值表述主要停留在“提升很多”“效果更明显”等泛化描述，缺少明确适用对象、可验证指标和具体结果，因此价值表达的具体性不足。
- Candidate Evidence Refs: ASR:agent-value-006, OCR:agent-value-006, META:agent-value-006
- Acceptable Variants: value claim lacks specificity, generic outcome wording

- Cross-Skill Ambiguity? `False`
- Expected Handoff? `NONE`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [ ] Cross-skill 标记正确

Final Finding:

价值表述主要停留在“提升很多”“效果更明显”等泛化描述，缺少明确适用对象、可验证指标和具体结果，因此价值表达的具体性不足。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-cross-hook-value-002

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `cross_skill_ambiguity`
- Case type: `cross_skill_ambiguity`
- Candidate only: `False`

### Evidence

- ASR: 开头说这个工具能让你少加班，但后面只演示按钮位置。
- OCR: 少加班 / 一键生成
- Metadata: duration=26s; benefit_in_opening=true; later_value_detail=weak
- Frame / Knowledge refs: ASR:agent-cross-hv-002, OCR:agent-cross-hv-002, META:agent-cross-hv-002, KNOWLEDGE:hook-pattern-pain-benefit-v2, KNOWLEDGE:value-bad-case-feature-without-benefit-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `opening_benefit_not_delivered`
- Label: 开头承诺少加班能形成 Hook，但后续只讲按钮功能，价值交付可能不足。
- Candidate Evidence Refs: ASR:agent-cross-hv-002, OCR:agent-cross-hv-002, META:agent-cross-hv-002
- Acceptable Variants: hook promise not supported by value detail, benefit claim needs value verification

- Cross-Skill Ambiguity? `True`
- Expected Handoff? `value_delivery`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [x] Cross-skill 标记正确

Final Finding:

开头承诺少加班能形成 Hook，但后续只讲按钮功能，价值交付可能不足。

Reviewer Notes:

Human reviewed and accepted.

## agent-case-cross-hook-structure-001

- Verification status: `VERIFIED`
- Source type: `SYNTHETIC`
- Primary skill: `cross_skill_ambiguity`
- Case type: `cross_skill_ambiguity`
- Candidate only: `False`

### Evidence

- ASR: 前三秒抛出一个问题，接着连续切了五个场景但没有回答问题。
- OCR: 你是不是也这样？
- Metadata: duration=24s; scene_changes_first_5s=5; answer_start=9.5s
- Frame / Knowledge refs: ASR:agent-cross-hs-001, OCR:agent-cross-hs-001, META:agent-cross-hs-001, KNOWLEDGE:hook-pattern-curiosity-gap-v1, KNOWLEDGE:structure-rule-density-scene-change-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `fast_cut_without_answer`
- Label: 开头提出了明确问题，但随后连续高频切换场景，直到约 9.5 秒才开始回答，开场问题与后续内容之间的结构承接存在明显延迟。
- Candidate Evidence Refs: ASR:agent-cross-hs-001, OCR:agent-cross-hs-001, META:agent-cross-hs-001
- Acceptable Variants: hook question lacks structural follow-through, scene density does not answer opening question

- Cross-Skill Ambiguity? `True`
- Expected Handoff? `structure_rhythm`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [x] Cross-skill 标记正确

Final Finding:

开头提出了明确问题，但随后连续高频切换场景，直到约 9.5 秒才开始回答，开场问题与后续内容之间的结构承接存在明显延迟。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-cross-hook-structure-002

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `cross_skill_ambiguity`
- Case type: `conflict_case`
- Candidate only: `False`

### Evidence

- ASR: 先展示最终效果，然后中间跳过步骤，直接说你照做就行。
- OCR: 最终效果 / 照做就行
- Metadata: duration=31s; result_visual=0.5s; process_gap=true
- Frame / Knowledge refs: ASR:agent-cross-hs-002, OCR:agent-cross-hs-002, META:agent-cross-hs-002, KNOWLEDGE:hook-good-case-visual-proof-v1, KNOWLEDGE:structure-pattern-contrast-before-after-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `structure_rhythm_analysis`
- Type: `proof_hook_process_gap`
- Label: 首屏直接展示最终效果，但中间过程被跳过，结果展示与后续方法说明之间缺少必要衔接，结构上存在明显的过程断层。
- Candidate Evidence Refs: ASR:agent-cross-hs-002, OCR:agent-cross-hs-002, META:agent-cross-hs-002
- Acceptable Variants: visual proof hook but weak structure, result-to-process transition gap

- Cross-Skill Ambiguity? `True`
- Expected Handoff? `structure_rhythm`
- Review notes: Human reviewed; finding wording normalized to evidence-supported diagnosis.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [x] Cross-skill 标记正确

Final Finding:

首屏直接展示最终效果，但中间过程被跳过，结果展示与后续方法说明之间缺少必要衔接，结构上存在明显的过程断层。

Reviewer Notes:

Human reviewed; finding wording normalized to evidence-supported diagnosis.

## agent-case-cross-structure-value-001

- Verification status: `VERIFIED`
- Source type: `EXISTING_BENCHMARK`
- Primary skill: `cross_skill_ambiguity`
- Case type: `cross_skill_ambiguity`
- Candidate only: `False`

### Evidence

- ASR: 第一步找账号，第二步看数据，第三步套模板，但没有说明什么人适合这个方法。
- OCR: 三步流程 / 找账号 / 看数据 / 套模板
- Metadata: duration=40s; structure_steps=3; target_audience_absent=true
- Frame / Knowledge refs: ASR:agent-cross-sv-001, OCR:agent-cross-sv-001, META:agent-cross-sv-001, KNOWLEDGE:structure-good-case-example-driven-v1, KNOWLEDGE:value-pattern-audience-outcome-v1
- Reference evidence count: `0`

### Candidate Finding

- Skill: `value_delivery_analysis`
- Type: `clear_steps_missing_audience_outcome`
- Label: 结构上步骤清楚，但价值层缺少适用人群和预期结果，需要 Value 维度补判。
- Candidate Evidence Refs: ASR:agent-cross-sv-001, OCR:agent-cross-sv-001, META:agent-cross-sv-001
- Acceptable Variants: clear structure but weak audience outcome, steps do not equal value clarity

- Cross-Skill Ambiguity? `True`
- Expected Handoff? `value_delivery`
- Review notes: Human reviewed and accepted.

### Human Review

- [x] Finding 正确
- [x] Evidence 正确
- [ ] Finding 需要修改
- [ ] Evidence 需要修改
- [ ] 应该是 insufficient evidence
- [x] Cross-skill 标记正确

Final Finding:

结构上步骤清楚，但价值层缺少适用人群和预期结果，需要 Value 维度补判。

Reviewer Notes:

Human reviewed and accepted.
