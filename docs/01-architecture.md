# 短视频对比诊断 MVP 架构说明

## 1. 设计原则

按 DDD 四层组织：接口层、应用层、领域层、基础设施层。

参考小傅哥常见的 DDD 思路，这个项目的关键不是把类拆很多，而是把职责边界守住：
- 接口层负责接入和出入参转换
- 应用层负责流程编排和用例执行
- 领域层负责业务规则和核心判断
- 基础设施层负责数据库、文件、模型和媒体能力实现

Java 只承载编排和领域建模，不直接承担重媒体算法实现。

## 2. 总体链路

Client -> Interface -> Application -> Domain -> Infrastructure -> Storage / Model / Media

## 3. 四层职责

### 3.1 接口层

职责：
- 接收上传请求
- 接收任务创建请求
- 接收任务状态查询请求
- 接收结果查询请求
- 做参数校验、鉴权、DTO/VO 转换
- 返回统一响应

适合放的内容：
- Controller
- Request / Response
- Assembler
- VO / DTO

不适合放的内容：
- 任务编排
- 业务规则
- 抽帧、ASR、模型调用
- 数据库访问

### 3.2 应用层

职责：
- 创建分析任务
- 编排预处理流程
- 编排诊断流程
- 控制任务状态流转
- 做幂等、重试、恢复
- 汇总领域结果并输出最终结果

适合放的内容：
- Application Service
- Command / Query
- Workflow / Case
- Job Orchestrator

不适合放的内容：
- 具体判断规则
- 媒体处理实现
- 第三方 SDK 细节

### 3.3 领域层

职责：
- 表达业务模型
- 表达核心规则
- 表达诊断判断逻辑
- 定义仓储接口
- 定义领域事件
- 定义值对象和聚合根

适合放的内容：
- Entity
- Value Object
- Aggregate Root
- Domain Service
- Repository Interface
- Domain Event
- Policy / Specification

这个项目里最核心的领域对象建议是：
- VideoAsset
- AnalysisJob
- VideoFeature
- SkillDefinition
- SkillRun
- Finding
- CoverageState

### 3.4 基础设施层

职责：
- 持久化实现
- 对象存储实现
- FFmpeg 处理实现
- ASR 服务适配
- LLM / VLM 服务适配
- 缓存、消息队列、定时任务实现

适合放的内容：
- Repository Impl
- Client Adapter
- Storage Adapter
- MQ Adapter
- Media Adapter
- Model Adapter

不适合放的内容：
- 领域判断
- 用例编排
- 接口转换

## 4. 按小傅哥风格的结构建议

如果你希望和知识星球里常见的 DDD 风格接近，我建议每个模块保持下面这组职责感：

- interface：对外触发层
- application：用例编排层
- domain：业务核心层
- infrastructure：技术实现层
- types：通用类型层

其中 types 可以单独放：
- 枚举
- 常量
- 通用错误码
- 通用返回体
- 基础 VO / DTO

## 5. 推荐项目结构

### 5.1 顶层模块

- `interface`
- `application`
- `domain`
- `infrastructure`
- `types`

### 5.2 interface 层建议包

- `controller`
- `dto`
- `vo`
- `assembler`
- `request`
- `response`

### 5.3 application 层建议包

- `service`
- `command`
- `query`
- `workflow`
- `case`

### 5.4 domain 层建议包

- `model`
- `entity`
- `valueobject`
- `service`
- `repository`
- `event`
- `policy`

### 5.5 infrastructure 层建议包

- `repository`
- `client`
- `adapter`
- `storage`
- `mq`
- `cache`
- `media`
- `asr`
- `model`

## 6. 这个项目各层该放什么

### 6.1 接口层

放：
- 上传视频接口
- 创建诊断任务接口
- 查询任务状态接口
- 查询诊断结果接口
- 入参校验
- 返回封装

### 6.2 应用层

放：
- `CreateAnalysisJob`
- `RunPreprocess`
- `RunDiagnosis`
- `CollectFindings`
- `BuildRevisionPlan`

### 6.3 领域层

放：
- `AnalysisJob` 状态规则
- `Finding` 的结构约束
- `CoverageState` 规则
- 核心诊断判断逻辑
- 证据和反证的校验逻辑

### 6.4 基础设施层

放：
- MySQL 实现
- Redis 实现
- MinIO / S3 实现
- FFmpeg 调用
- ASR 调用
- LLM / VLM 调用
- 消息队列实现

## 7. 关键分层边界

### 接口层不碰规则
接口层只负责请求和响应，不做业务判断。

### 应用层不碰技术细节
应用层只负责编排，不直接写媒体和存储实现。

### 领域层不碰外部实现
领域层只表达业务，不依赖数据库、SDK 和文件系统。

### 基础设施层不碰业务结论
基础设施层只提供能力，不决定对错。

## 8. MVP 推荐落地方式

第一版不要拆太碎，按这四层就够：
- 接口层
- 应用层
- 领域层
- 基础设施层

如果后面流程变复杂，再细分 `case`、`trigger`、`types` 的使用范围。

## 9. MVP 推荐技术选型

- Java 21
- Spring Boot 3.x
- MySQL 8
- Redis
- MinIO 或兼容 S3 的对象存储
- RabbitMQ 或 Kafka，二选一即可
- FFmpeg
- 第三方 ASR API 或内部转写服务
- 第三方 LLM / VLM API

## 10. 任务流

1. Client 上传视频
2. 接口层接收请求并校验
3. 应用层创建 AnalysisJob
4. 基础设施层做视频预处理
5. 领域层接收 VideoFeature
6. 应用层编排诊断流程
7. 领域层产出 Finding
8. 应用层汇总并返回结果

## 11. 关键工程原则

- 同一视频的预处理结果必须可复用
- 每次运行都要记录版本快照
- 任务必须幂等
- 失败要能重试
- 所有结论必须回指证据

## 12. 一句话总结

接口层负责“进来”，应用层负责“怎么走”，领域层负责“怎么判断”，基础设施层负责“怎么实现”。
