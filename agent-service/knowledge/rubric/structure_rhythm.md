---
skill: structure_rhythm_analysis
dimension: 结构节奏
---

# 结构节奏评分点

每条评分点是一个 `## 标题` 小节：下面几行 `- 字段: 值` 是元数据，之后的段落是判定重点和边界（检索和诊断都会用到）。

- id：全局唯一，建议 `维度-类型-简称-v版本`；改了 id 等于新增一条（检索评测的 Golden Query 按 id 标注）。
- type：模式 / 规则 / 好例 / 反例 / 平台规则 / 品类最佳实践。
- tags、focus、group 可选。

修改后新任务就会读到（每个任务开始时重新读取）；建议改完执行 `docker compose restart agent-service`，启动时会校验格式，写错会直接报错并指出文件和行号。

## 问题展开收束结构
- id: structure-pattern-problem-expand-close-v1
- type: 模式
- tags: structure, flow, close
- focus: STRUCTURE_FLOW
- group: structure_actionable_advice

内容按问题引入、关键展开、行动收束组织。判定重点是段落顺序和承接关系，而不是行动建议本身是否有价值。

## 列表式信息结构
- id: structure-pattern-topic-list-v1
- type: 模式
- tags: structure, list
- focus: STRUCTURE_FLOW
- group: generic_opening_topic_list

多点内容适合列表式呈现，但每一点需要明确层级、顺序或递进。关注组织方式，不是泛泛开场。

## 开头到正文转场
- id: structure-rule-opening-transition-v1
- type: 规则
- tags: structure, transition
- focus: STRUCTURE_FLOW
- group: opening_transition

hook 后需要自然进入正文，否则用户会感觉承诺和内容断裂。关注开头之后的连接，不评价首屏承诺是否足够强。

## 信息密度与画面补偿
- id: structure-rule-density-scene-change-v1
- type: 规则
- tags: structure, density, scene-change
- focus: MIDPOINT_RETENTION
- group: static_density

镜头长期不变时，需要靠字幕、段落变化、例子或节奏点维持注意力。它是判断与补偿规则，不等于静态口播失败案例。

## 静态口播无节奏点
- id: structure-bad-case-static-talking-v1
- type: 反例
- tags: structure, bad-case, static-talking
- focus: MIDPOINT_RETENTION
- group: static_density

全程同一画面、同一语速、无字幕分段或示例推进，会降低注意力维持。它描述失败状态，而不是提供补偿规则。

## 节奏标记清晰
- id: structure-good-case-rhythm-marker-v1
- type: 好例
- tags: structure, rhythm-marker
- focus: STRUCTURE_FLOW
- group: rhythm_step_delivery

用数字、字幕、转场词或画面变化标记段落，让观众知道内容进度。关注节奏标记，不是步骤价值交付。

## 慢热叙事例外
- id: structure-rule-slow-burn-exception-v1
- type: 规则
- tags: structure, slow-burn, narrative
- focus: STRUCTURE_FLOW
- group: late_payoff_slow_burn

情绪故事或强人物冲突可以慢热，但前段必须有悬念、关系张力或情绪推进。关注整体叙事节奏例外。

## 前后对比组织顺序
- id: structure-pattern-contrast-before-after-v1
- type: 模式
- tags: structure, before-after, sequence
- focus: STRUCTURE_FLOW
- group: before_after_structure_value

按问题状态、改变过程、结果状态来组织内容。判定重点是内容顺序和段落推进，不是用结果证明价值本身。

## 主题跳跃缺少过渡
- id: structure-bad-case-topic-jump-v1
- type: 反例
- tags: structure, topic-jump, bad-case
- focus: STRUCTURE_FLOW
- group: topic_jump_scattered_value

内容从痛点跳到卖点再回背景，缺少过渡和承接，用户难以跟上。关注段落之间的断裂。

## 中段留存推进
- id: structure-rule-midpoint-retention-v1
- type: 规则
- tags: structure, midpoint-retention
- focus: MIDPOINT_RETENTION
- group: midpoint_specificity

中段需要新信息、例子、反转或步骤推进，避免重复解释。关注内容是否继续前进，而非收益是否具体。

## 例子驱动段落展开
- id: structure-good-case-example-driven-v1
- type: 好例
- tags: structure, example-driven
- focus: STRUCTURE_FLOW
- group: example_proof

用真实例子承载解释和段落推进，帮助观众跟上抽象概念。判定重点是例子服务于理解与结构推进，不是证明价值可信。
