---
skill: hook_analysis
dimension: 开场钩子
---

# 开场钩子评分点

每条评分点是一个 `## 标题` 小节：下面几行 `- 字段: 值` 是元数据，之后的段落是判定重点和边界（检索和诊断都会用到）。

- id：全局唯一，建议 `维度-类型-简称-v版本`；改了 id 等于新增一条（检索评测的 Golden Query 按 id 标注）。
- type：模式 / 规则 / 好例 / 反例 / 平台规则 / 品类最佳实践。
- tags、focus、group 可选。

修改后新任务就会读到（每个任务开始时重新读取）；建议改完执行 `docker compose restart agent-service`，启动时会校验格式，写错会直接报错并指出文件和行号。

## 自我介绍拖慢开场
- id: hook-pattern-self-intro-delay-v1
- type: 模式
- tags: hook, self-intro, opening-delay
- focus: OPENING_RETENTION
- group: self_intro_authority

开头把时间用于身份、品牌、经历铺垫，几秒后才进入用户问题或收益，会削弱信息流停留。判定重点是用户价值是否被明显后置，而不是是否出现身份信息。

## 权威背书快速接收益
- id: hook-good-case-authority-fast-v1
- type: 好例
- tags: hook, authority, benefit
- focus: OPENING_RETENTION
- group: self_intro_authority

可以用一句身份或资质建立信任，但必须马上连接到用户能得到的具体结果。判定重点是权威信息是否服务于首屏收益，而不是占用开头铺垫。

## 首屏痛点收益钩子
- id: hook-pattern-pain-benefit-v2
- type: 模式
- tags: hook, pain-point, benefit, opening
- focus: OPENING_RETENTION
- group: hook_value_boundary

只评估开头首屏是否同时给出用户痛点和可感知收益，用于判断停留理由是否成立。不评估整条视频是否完整交付价值。

## 有效好奇缺口
- id: hook-pattern-curiosity-gap-v1
- type: 模式
- tags: hook, curiosity, contrast
- focus: OPENING_RETENTION
- group: curiosity_empty_suspense

通过反常识、悬念或结果反差制造继续观看理由，但悬念必须绑定具体对象、问题、冲突或结果。不是单纯让用户等到最后。

## 空泛悬念吊胃口
- id: hook-bad-case-empty-suspense-v1
- type: 反例
- tags: hook, bad-case, empty-suspense
- focus: OPENING_RETENTION
- group: curiosity_empty_suspense

开头只说“看到最后”“很多人不知道”“很重要”，但没有给具体对象、问题或收益。问题在于悬念没有可判断的内容承诺。

## 前三秒信息承诺
- id: hook-rule-first-three-seconds-v1
- type: 规则
- tags: hook, rule, first-three-seconds
- focus: OPENING_RETENTION
- group: opening_transition

前三秒至少需要明确对象、问题、收益或冲突之一。它是开头诊断规则，不等同于后续结构转场或完整价值交付。

## 首屏视觉证据抓停留
- id: hook-good-case-visual-proof-v1
- type: 好例
- tags: hook, visual-proof, opening
- focus: OPENING_RETENTION
- group: visual_proof_value_proof

在首屏展示结果图、前后对比、价格差或效果变化，让用户立刻判断值得继续看。判定重点是首屏停留，不是全文价值证明。

## 点名目标人群
- id: hook-pattern-target-audience-v1
- type: 模式
- tags: hook, audience
- focus: OPENING_RETENTION
- group: audience_scenario

开头明确“谁需要看”，适合垂直内容。有效点名必须继续连接具体问题或收益，不能只喊人群标签。

## 泛泛开场白
- id: hook-bad-case-generic-opening-v1
- type: 反例
- tags: hook, bad-case, generic-opening
- focus: OPENING_RETENTION
- group: generic_opening_topic_list

“大家好今天分享一下”这类开场缺少对象、问题、收益或冲突。判定重点是开头没有形成任何停留承诺。

## 避免收益后置
- id: hook-rule-avoid-late-payoff-v1
- type: 规则
- tags: hook, late-payoff, rule
- focus: OPENING_RETENTION
- group: late_payoff_slow_burn

如果用户收益点出现在五秒后，需要检查前段是否已有足够强的冲突、悬念或情绪张力支撑停留。关注收益出现时机。

## 信息流首屏决策
- id: hook-platform-short-feed-v1
- type: 平台规则
- tags: hook, feed, platform
- focus: OPENING_RETENTION
- group: feed_opening_structure_length

信息流用户先判断是否值得停留，因此首屏表达优先于完整铺垫。该知识用于平台环境下的开头诊断。

## 开头先堆功能
- id: hook-bad-case-feature-first-v1
- type: 反例
- tags: hook, feature-first, bad-case
- focus: OPENING_RETENTION
- group: feature_without_benefit

开头直接罗列功能、参数或成分，却没有说明用户问题和结果感，会导致 hook 偏弱。关注的是功能信息出现在开头且没有用户连接。
