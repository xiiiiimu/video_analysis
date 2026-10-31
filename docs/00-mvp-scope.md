# 短视频对比诊断 MVP 范围清单

## 1. MVP 目标

围绕一个 Target 短视频和 1~N 个 Reference 视频，完成上传、异步处理、基础诊断、证据汇总和结果输出。

从 DDD 视角看，MVP 的目标不是把所有能力做全，而是先把“分析任务”这个核心用例跑通。

## 2. MVP 只做什么

### 输入
- Target 视频 1 个，必填
- Reference 视频 1~N 个，必填
- 可选标题和文案
- 可选封面图
- 可选基础数据，例如点赞、评论、收藏、播放量、完播率

### 处理
- 视频上传登记
- 分析任务创建
- 异步预处理
- 抽帧
- ASR 转写
- 基础元数据提取
- 核心维度诊断
- 结构化结果汇总

### 输出
- 最多 1~3 条核心问题
- 每条问题都带证据
- 每条问题都给修改建议
- 明确说明缺失了哪些输入

## 3. MVP 不做什么

- 不做平台 API 抓取
- 不做自动找爆款视频
- 不做复杂模型训练
- 不做完整的在线评测平台
- 不做 Skill 在线热更新
- 不做复杂多租户权限体系
- 不做复杂可视化工作台
- 不追求全自动预测爆款

## 4. 核心分析维度

MVP 先固定 3 个核心维度：

1. Hook
2. Structure / Rhythm
3. Value Delivery

建议保留但首版不强依赖的维度：

- Title
- Cover
- Topic / Audience
- Emotion / Tone
- Interaction / CTA
- Performance Data

## 5. 最小用例流

1. 用户上传 Target 和 Reference
2. 接口层接收请求并校验
3. 应用层创建 AnalysisJob
4. 基础设施层完成预处理
5. 领域层生成 VideoFeature 和相关诊断上下文
6. 应用层编排三个核心诊断用例
7. 领域层产出 Finding 和 CoverageState
8. 应用层汇总 Revision Plan
9. 用户查询任务结果

## 6. MVP 成功标准

只要满足下面条件，就算 MVP 成功：

- 可以稳定处理短视频上传
- 可以稳定跑完异步分析
- 输出结果具备证据链
- 结论能收敛到 1~3 个核心问题
- 同一个输入重复运行，结果大体稳定

## 7. MVP 风险点

- ASR 质量不稳定
- 参考视频不够同类
- 视频过长导致成本上升
- 模型输出过于发散
- 证据链不够具体

## 8. 推荐的第一阶段范围

如果要尽快上线验证，建议先做：

- 视频上传
- 任务状态查询
- 抽帧
- ASR
- Hook 分析
- Structure / Rhythm 分析
- Value Delivery 分析
- 结果页

## 9. 和 DDD 的对应关系

- 输入属于 interface 层
- 流程编排属于 application 层
- 分析判断属于 domain 层
- 抽帧、ASR、存储属于 infrastructure 层

