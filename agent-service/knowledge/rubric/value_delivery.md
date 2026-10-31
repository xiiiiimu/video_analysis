---
skill: value_delivery_analysis
dimension: 价值传递
---

# 价值传递评分点

每条评分点是一个 `## 标题` 小节：下面几行 `- 字段: 值` 是元数据，之后的段落是判定重点和边界（检索和诊断都会用到）。

- id：全局唯一，建议 `维度-类型-简称-v版本`；改了 id 等于新增一条（检索评测的 Golden Query 按 id 标注）。
- type：模式 / 规则 / 好例 / 反例 / 平台规则 / 品类最佳实践。
- tags、focus、group 可选。

修改后新任务就会读到（每个任务开始时重新读取）；建议改完执行 `docker compose restart agent-service`，启动时会校验格式，写错会直接报错并指出文件和行号。

## 明确观众获得什么
- id: value-pattern-audience-outcome-v1
- type: 模式
- tags: value, audience, outcome
- focus: VALUE_CLARITY
- group: hook_value_boundary

价值表达要说清用户对象、使用场景和最终结果。关注整条内容的价值清晰度，不评价首屏是否足够抓人。

## 场景化价值
- id: value-pattern-use-scenario-v1
- type: 模式
- tags: value, scenario
- focus: VALUE_CLARITY
- group: audience_scenario

不只说产品或方法好，而是说明在哪个使用场景解决什么问题。关注价值落点的场景，不是开头点名人群。

## 可执行下一步
- id: value-pattern-actionable-advice-v1
- type: 模式
- tags: value, actionable
- focus: ACTION_ALIGNMENT
- group: action_cta_fit, structure_actionable_advice

内容需要让观众知道下一步如何检查、尝试或判断。判定重点是有没有可执行建议，不是 CTA 是否匹配商业目标。

## 收益具体化
- id: value-rule-specificity-v1
- type: 规则
- tags: value, specificity
- focus: VALUE_CLARITY
- group: midpoint_specificity

“更好、更快、更省”需要转成具体结果、数字、对比或体验变化。关注收益是否可感知，不评价中段是否推进。

## 只讲功能不讲收益
- id: value-bad-case-feature-without-benefit-v1
- type: 反例
- tags: value, bad-case, feature-without-benefit
- focus: VALUE_CLARITY
- group: feature_without_benefit

只罗列功能、参数、成分或流程，没有说明用户为什么需要。关注全片价值表达缺失，不限于开头。

## 空泛价值主张
- id: value-bad-case-vague-claim-v1
- type: 反例
- tags: value, bad-case, vague
- focus: VALUE_CLARITY
- group: vague_claim_empty_suspense

只说“效果很好”“很实用”“值得买”，但没有对象、场景、结果或证据。关注价值主张不可验证。

## 证据支撑价值主张
- id: value-good-case-proof-before-claim-v1
- type: 好例
- tags: value, proof, credibility
- focus: VALUE_CREDIBILITY
- group: visual_proof_value_proof, example_proof

先给案例、数据、反馈或对比，再提出价值判断，更可信。判定重点是证据支撑价值主张，不是首屏抓停留或结构解释。

## 步骤化价值交付
- id: value-good-case-step-by-step-v1
- type: 好例
- tags: value, step-by-step
- focus: ACTION_ALIGNMENT
- group: rhythm_step_delivery

把价值拆成用户可照做的步骤，降低理解成本。关注步骤是否帮助用户完成行动，不是段落节奏标记。

## 行动号召匹配价值
- id: value-rule-call-to-action-fit-v1
- type: 规则
- tags: value, cta, alignment
- focus: ACTION_ALIGNMENT
- group: action_cta_fit

CTA 应与前文价值承诺一致，不能从自测、科普或避坑突然跳到购买或关注。关注行动建议是否匹配前文。

## 收益点分散无主线
- id: value-bad-case-scattered-benefits-v1
- type: 反例
- tags: value, bad-case, scattered-benefits
- focus: VALUE_CLARITY
- group: topic_jump_scattered_value

多个收益散落各处，没有主价值主线，用户记不住核心结果。关注价值主线分散，不是段落跳跃本身。

## 前后变化表达收益
- id: value-rule-before-after-outcome-v1
- type: 规则
- tags: value, before-after, outcome
- focus: VALUE_CREDIBILITY
- group: before_after_structure_value

用使用前后的变化结果表达观众收益，适合改造、学习、效率类内容。判定重点是变化结果证明价值，不是内容组织顺序。
