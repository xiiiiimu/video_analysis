# 短视频对比诊断 Java 目录结构建议

## 1. 设计目标

这份目录结构的目标是：

- 符合 DDD 四层
- 符合 Java / Spring Boot 常见工程习惯
- 适合短视频对比诊断这个业务
- 方便后续扩展 Hook、Cover、Title、Performance 等能力
- 尽量贴近小傅哥常见的分层表达方式

## 2. 推荐顶层包

建议使用一个统一根包，例如：

`com.xxx.videodiagnosis`

下面按四层展开：

```text
com.xxx.videodiagnosis
├── interface
├── application
├── domain
├── infrastructure
└── types
```

## 3. 目录结构总览

```text
src/main/java/com/xxx/videodiagnosis
├── interface
│   ├── controller
│   ├── dto
│   ├── vo
│   ├── assembler
│   ├── request
│   └── response
├── application
│   ├── service
│   ├── command
│   ├── query
│   ├── workflow
│   └── case
├── domain
│   ├── model
│   ├── entity
│   ├── valueobject
│   ├── service
│   ├── repository
│   ├── event
│   └── policy
├── infrastructure
│   ├── repository
│   ├── client
│   ├── adapter
│   ├── storage
│   ├── mq
│   ├── cache
│   ├── media
│   ├── asr
│   └── model
└── types
    ├── constants
    ├── enums
    ├── error
    └── common
```

## 4. 各层目录职责

### 4.1 interface

职责：
- 接收 HTTP 请求
- 完成参数校验
- 做 Request / Response 转换
- 返回统一结构

建议放的类：
- `AnalysisCommandController`
- `AnalysisQueryController`
- `VideoCommandController`
- `HealthQueryController`
- `CreateAnalysisJobRequest`
- `CreateAnalysisJobResponse`
- `AnalysisJobResultVO`
- `AnalysisJobAssembler`

### 4.2 application

职责：
- 执行业务用例
- 编排多个领域对象和仓储
- 控制任务流程
- 处理幂等、重试、状态流转

建议放的类：
- `CreateAnalysisJobService`
- `SubmitAnalysisJobService`
- `QueryAnalysisJobService`
- `QueryAnalysisResultService`
- `AnalysisPreprocessWorkflow`
- `AnalysisDiagnosisWorkflow`
- `CreateAnalysisJobCommand`
- `QueryAnalysisJobQuery`

### 4.3 domain

职责：
- 表达核心业务规则
- 表达聚合根和实体
- 表达领域服务和策略
- 定义仓储接口

建议放的类：
- `AnalysisJob`
- `VideoAsset`
- `VideoFeature`
- `SkillDefinition`
- `SkillRun`
- `Finding`
- `CoverageState`
- `AnalysisJobRepository`
- `VideoAssetRepository`
- `SkillDefinitionRepository`
- `DiagnosisDomainService`
- `CoveragePolicy`
- `FindingRankPolicy`

### 4.4 infrastructure

职责：
- 对接数据库
- 对接对象存储
- 对接 FFmpeg
- 对接 ASR
- 对接 LLM / VLM
- 对接缓存和消息队列

建议放的类：
- `AnalysisJobRepositoryImpl`
- `VideoAssetRepositoryImpl`
- `SkillDefinitionRepositoryImpl`
- `MinioStorageClient`
- `FfmpegMediaAdapter`
- `AsrClientAdapter`
- `ModelClientAdapter`
- `AnalysisJobMqProducer`
- `AnalysisJobCache`

### 4.5 types

职责：
- 放通用枚举
- 放通用错误码
- 放通用常量
- 放通用返回体

建议放的类：
- `Result`
- `ErrorCode`
- `JobStatusEnum`
- `VideoStatusEnum`
- `AnalysisDimensionEnum`
- `PriorityEnum`

## 5. 按业务域进一步拆分

如果你希望结构更清晰，可以在 `domain` 和 `application` 里按子域再拆一层。

### 5.1 analysis 子域

```text
analysis
├── entity
├── service
├── repository
├── policy
└── event
```

### 5.2 video 子域

```text
video
├── entity
├── valueobject
├── repository
└── service
```

### 5.3 skill 子域

```text
skill
├── entity
├── repository
├── service
└── policy
```

### 5.4 diagnosis 子域

```text
diagnosis
├── entity
├── service
├── policy
└── event
```

## 6. 推荐的包命名规则

建议保持以下习惯：

- 用例类用 `Service` 结尾
- 命令对象用 `Command`
- 查询对象用 `Query`
- 领域对象尽量直接叫业务名
- 仓储接口放在 `domain`
- 仓储实现放在 `infrastructure`
- 对外请求对象用 `Request`
- 对外返回对象用 `Response` 或 `VO`

## 7. 一个典型用例的调用路径

以“创建分析任务”为例，目录和调用路径建议是：

```text
interface/controller
  -> application/service
  -> domain/service
  -> domain/repository
  -> infrastructure/repository
```

如果中间需要预处理：

```text
application/workflow
  -> infrastructure/media
  -> infrastructure/asr
  -> domain/service
```

## 8. 首版不要过度拆分的部分

MVP 阶段建议先不要拆得太细：

- 不要一开始就把 `case`、`workflow`、`process` 全都并行使用
- 不要给每个维度都单独开一个模块
- 不要把 DTO / VO 拆得太碎
- 不要在 domain 里引入过多子包导致找不到入口

第一版重点是：
- 边界清晰
- 目录稳定
- 用例容易找
- 未来方便扩展

## 9. 推荐的首版目录

如果你想更稳一点，第一版可以先按这个最小结构开始：

```text
com.xxx.videodiagnosis
├── interface
├── application
├── domain
├── infrastructure
└── types
```

后面再按子域慢慢拆。

## 10. 一句话总结

这套目录结构的核心原则是：

**接口层负责进来，应用层负责怎么走，领域层负责怎么判断，基础设施层负责怎么实现。**

