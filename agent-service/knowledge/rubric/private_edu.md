---
skill: mixed
dimension: 品类私有规范
---

# 示例私有规范：知识教程类

这是**示例**：演示"平台 / 企业自己的评分规范"怎么放进知识库。和通用评分点的区别：

- 每条带 `- category:`，只对创建任务时 `category` 相同的任务生效，不影响其它任务；
- 检索时同品类的私有规范全部带上（不参与相关度排序，避免被挤掉）；
- 与通用评分点冲突时以私有规范为准（例如通用评分点认为"有效的反问开场"可以接受，这里规定不行）。

这些规则是模型不可能事先知道的，评测里用它们检验"没有检索时，系统能不能按私有规范判断"。

## 开场 2 秒内出标题字幕
- id: private-edu-hook-title-2s-v1
- skill: hook_analysis
- category: 知识教程
- type: 平台规则
- tags: 标题字幕, 开场, 两秒

知识教程类视频：开场 2 秒内屏幕上必须出现概括主题的标题字幕。只有口播、标题字幕到第 3 秒以后才出现的，即使口播已经说出收益，也判为开场缺少屏幕文字强化（hook_weak_visual_text）。

## 开场第一句不用反问
- id: private-edu-hook-no-question-v1
- skill: hook_analysis
- category: 知识教程
- type: 平台规则
- tags: 反问, 设问, 第一句, 直接结论

知识教程类视频：开场第一句不能用反问句或设问句（"你知道吗""为什么……"），必须直接陈述结论或收益。第一句是反问 / 设问时，即使后面有悬念或答案，也判为开场没有价值承诺（hook_no_value_promise）。本条优先于通用评分点"有效好奇缺口"。

## 单个镜头不超过 8 秒
- id: private-edu-structure-shot-8s-v1
- skill: structure_rhythm_analysis
- category: 知识教程
- type: 平台规则
- tags: 镜头时长, 8秒, 节奏

知识教程类视频：任何单个镜头超过 8 秒即视为节奏过慢（pacing_too_slow），即使字幕在变化、即使平均镜头时长与参考接近。判定看最长镜头和超过 8 秒的镜头个数。

## 结尾给评论区关键词
- id: private-edu-value-cta-keyword-v1
- skill: value_delivery_analysis
- category: 知识教程
- type: 平台规则
- tags: 行动号召, 评论区, 关键词, 私信

知识教程类视频：结尾的行动号召必须给出具体动作，例如"评论区扣关键词领取""私信关键词获取"。只说"关注我""下期见"视为没有有效的行动号召（no_cta）。

## 收益必须量化
- id: private-edu-value-number-v1
- skill: value_delivery_analysis
- category: 知识教程
- type: 平台规则
- tags: 数字, 量化, 收益

知识教程类视频：收益承诺必须带具体数字（时间、金额、数量、百分比）。只说"更好看""更高效""更省事"视为收益表述模糊（value_unclear）。
