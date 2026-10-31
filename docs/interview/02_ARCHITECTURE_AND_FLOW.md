# 架构与调用链

## 总体架构

```text
用户/前端
  -> Java Backend
     -> AnalysisJob / VideoAsset / Evidence / Finding / MySQL
     -> Redis progress cache
     -> dispatch agentRunId
  -> Python agent-service
     -> HarnessRunner
     -> Planner
     -> Parallel Diagnosis Skills
     -> Evaluator
     -> Synthesizer
     -> callback Java
```

核心边界：

- Java 是 System of Record：`AnalysisJob`、状态、证据、Finding、回调幂等以 Java/MySQL 为准。
- Python 是 Agent Runtime：只保存一次 `AgentRun` 的运行上下文和推理草稿。
- Redis 是缓存：任务进度和重复回调快速拦截可以丢失，不作为事实源。

## Java 分层

当前 Java 代码基本按 DDD 分层组织：

- 接口层：`backend/src/main/java/com/videodiagnosis/interface` 和 `backend/src/main/java/com/videodiagnosis/interfaces`
- 应用层：`backend/src/main/java/com/videodiagnosis/application`
- 领域层：`backend/src/main/java/com/videodiagnosis/domain`
- 基础设施层：`backend/src/main/java/com/videodiagnosis/infrastructure`
- 通用类型：`backend/src/main/java/com/videodiagnosis/types`

需要注意：仓库里同时存在 `interface` 和 `interfaces` 两个包。真实代码里内部 Agent API 在 `interfaces/controller/internal/InternalAnalysisController.java`，用户侧 API 在 `interface/controller`。这属于历史命名不统一，面试可以说后续会收敛包名，但当前没有为了重构而大规模改名。

## 端到端调用链

1. Java 创建/准备诊断任务。
   - 核心实体：`backend/src/main/java/com/videodiagnosis/domain/entity/AnalysisJob.java`
   - 创建用例：`backend/src/main/java/com/videodiagnosis/application/case/CreateAnalysisJobCase.java`
   - Agent 启动/调度相关：`StartAgentDiagnosisCase.java`、`DispatchAgentCase.java`

2. Java dispatch Agent。
   - `DispatchAgentCase.dispatchOne` 生成 `agentRunId`。
   - 调用 `job.markAgentRunning(agentRunId, timeoutAt)`。
   - 通过 `AgentDispatchPort` 发给 Python。
   - HTTP 适配在 `HttpAgentDispatchAdapter.java` 和 `AgentServiceHttpClient.java`。

3. Python 接收任务并运行。
   - 服务入口：`agent-service/src/agent_service/services/job_runner.py`
   - 统一运行壳：`agent-service/src/agent_service/harness/runner.py`
   - 图构建：`agent-service/src/agent_service/graph/builder.py`

4. Python Agent Workflow。
   - `planner.py` 生成固定三个 Skill 计划。
   - `diagnose.py` 并行执行三个 Diagnosis Skill。
   - `react_loop.py` 在单 Skill 内做 bounded ReAct。
   - `evaluator.py` 做 Finding 质量门禁。
   - `synthesizer.py` 保存已有 Finding，并生成最终 callback payload。

5. Python 回调 Java。
   - Python 回调适配：`agent-service/src/agent_service/tools/adapters/analysis_job.py`
   - Java 内部接口：`backend/src/main/java/com/videodiagnosis/interfaces/controller/internal/InternalAnalysisController.java`
   - Java 结果处理：`backend/src/main/java/com/videodiagnosis/application/usecase/HandleAgentResultCase.java`

6. Java 完成任务。
   - 成功：状态进入 `RESULT_PROCESSING -> COMPLETED`。
   - 失败：状态进入 `FAILED`。
   - 重复 callback：直接忽略。
   - 旧 `agentRunId` callback：拒绝。

## Agent Workflow

当前 Python graph 在 `agent-service/src/agent_service/graph/builder.py`：

```text
plan
  -> tools
  -> diagnose
  -> evaluate
  -> synthesize
  -> end
```

设计原则：

- 外层 deterministic：不让模型动态决定全局流程。
- 内层 bounded agentic：只有单个 Skill 证据不足时才进入 ReAct。
- Skill 不是独立 Agent，而是统一抽象的 `Diagnosis Skill`。
- `Evaluator` 不生成新结论，只判断已有 finding 是否结构完整、有 evidence、有置信度。
- `Synthesizer` 只聚合和保存已有 finding，不凭空生成无证据新结论。

## AgentRuntimeState

运行上下文定义在 `agent-service/src/agent_service/graph/state.py` 的 `AgentGraphState`。

关键字段：

- `run_id` / `job_id`
- `plan`
- `current_skill`
- `evidence_refs`
- `knowledge_evidence_refs`
- `findings`
- `evidence_gaps`
- `tool_results`
- `evaluation_results`
- `iteration_count`
- `react_iterations_by_skill`
- `status`
- `step_traces`
- `agent_trace`
- `result_version`

这个 state 是 Python 单次 Agent Run 的运行上下文，不是 Java 业务状态。

## 任务状态和进度

Java 业务状态在 `AnalysisJob` 中：

- `CREATED`
- `PENDING`
- `PREPROCESSING`
- `EVIDENCE_READY`
- `WAITING_AGENT`
- `AGENT_RUNNING`
- `RESULT_PROCESSING`
- `RETRYING`
- `COMPLETED`
- `FAILED`

Python 执行阶段通过 `report_stage` 上报给 Java，典型 stage：

- `PLANNING`
- `HOOK_ANALYSIS`
- `STRUCTURE_RHYTHM_ANALYSIS`
- `VALUE_DELIVERY_ANALYSIS`
- `EVALUATING`
- `SYNTHESIZING`
- `COMPLETED`

Java `AnalysisProgressService` 把进度写入 Redis key `analysis:job:{jobId}:progress`。这只是查询加速和用户体验，不改变 MySQL 事实状态。

## 幂等与旧回调防护

关键代码：

- `AnalysisJob.canAcceptAgentResult`
- `HandleAgentResultCase.execute`
- `RedisIdempotencyRepository`
- `AgentCallbackRecordRepository`
- `AgentCallbackRecordJpaEntity`

机制：

- `agentRunId`：Java dispatch 时生成，Python 必须原样带回。
- `resultVersion`：Python 当前固定回传 `1`，Java 也支持根据历史版本推导。
- Redis：快速判断 `(agentRunId, resultVersion)` 是否处理过。
- DB callback record：最终防线，避免 Redis 丢失后重复入库。
- stale callback：如果 callback 的 `agentRunId` 不是当前 job 的 `currentAgentRunId`，Java 拒绝。

面试注意：

- 不要说 Redis 是最终幂等保障。
- 不要说 `@Version` 是 CAS；它是 JPA 乐观锁。

## Agent Trace

Python 内部 step trace 在 `agent-service/src/agent_service/graph/runtime.py`。

Java 查询接口：

```text
GET /internal/v1/analysis/jobs/{jobId}/agent-runs/{agentRunId}/trace
```

Trace 字段：

- `runId`
- `stepType`
- `skillCode`
- `toolName`
- `evidenceRefs`
- `latencyMs`
- `status`
- `shortSummary`

限制：

- 不记录 chain-of-thought。
- 只记录执行路径、工具、证据引用和简短摘要。

