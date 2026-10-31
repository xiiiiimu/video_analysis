# 核心代码走读

## 1. Java 任务状态核心

文件：`backend/src/main/java/com/videodiagnosis/domain/entity/AnalysisJob.java`

这个类是业务事实状态的核心。重点方法：

- `initializeCreated`：初始化 `CREATED`。
- `waitForAgent`：进入 `WAITING_AGENT`，等待 worker dispatch。
- `markAgentRunning`：绑定 `agentRunId`，设置 timeout，进入 `AGENT_RUNNING`。
- `startResultProcessing`：Agent 成功回调后进入结果处理。
- `complete`：记录 `lastProcessedAgentRunId` 和 `lastResultVersion`，状态变成 `COMPLETED`。
- `retry`：失败或超时后进入 `RETRYING`，清空当前 `currentAgentRunId`。
- `canAcceptAgentResult`：检查当前状态、超时、`agentRunId`、`resultVersion`。

面试讲法：

“我把状态流转尽量放在领域实体里，不让 Controller 随便改状态。比如 stale callback、已完成任务回调、超时回调这些都要通过 `AnalysisJob` 的状态约束。”

## 2. Agent Dispatch

文件：`backend/src/main/java/com/videodiagnosis/application/usecase/DispatchAgentCase.java`

关键流程：

- 查询可调度任务：`analysisJobRepository.findDispatchableJobs`。
- 每个任务生成 UUID 作为 `agentRunId`。
- 调用 `job.markAgentRunning`。
- 保存 job。
- Redis 更新 `AGENT_RUNNING` 进度。
- 通过 `agentDispatchPort.dispatch(jobId, agentRunId)` 提交 Python。
- dispatch 失败则按 `RetryPolicy` 进入 `RETRYING` 或 `FAILED`。

配套基础设施：

- `backend/src/main/java/com/videodiagnosis/application/port/AgentDispatchPort.java`
- `backend/src/main/java/com/videodiagnosis/infrastructure/agent/HttpAgentDispatchAdapter.java`
- `backend/src/main/java/com/videodiagnosis/infrastructure/client/AgentServiceHttpClient.java`

## 3. Callback 处理

文件：`backend/src/main/java/com/videodiagnosis/application/usecase/HandleAgentResultCase.java`

关键点：

- 先规范化 `agentRunId` 和 `resultVersion`。
- 先查 Redis 和 DB callback record，重复则直接返回。
- 已终态任务收到回调，只写快速去重并忽略。
- stale `agentRunId` 直接抛 `BAD_REQUEST`。
- `SUCCESS` 时保存草稿观察和 agent trace，进入 `COMPLETED`。
- 非 SUCCESS 时进入 `FAILED`。
- 成功处理后同时写 DB callback record 和 Redis key。

这套设计解决：

- Python 重试导致重复回调。
- Java 业务重试后旧 AgentRun 晚到。
- Redis 不可靠时仍能靠数据库记录兜底。

## 4. Redis 进度

文件：`backend/src/main/java/com/videodiagnosis/application/service/AnalysisProgressService.java`

职责：

- 写入 `AnalysisProgressSnapshot`。
- Redis 不可用时直接返回，不影响业务。
- `COMPLETED` / `FAILED` TTL 30 分钟，运行中 TTL 10 分钟。
- `fromJob` 可以从 MySQL job 生成进度快照。

面试边界：

“Redis 这里只是用户查询进度的缓存，不是业务事实源。任务真实状态仍然看 `AnalysisJob` 持久化。”

## 5. 内部接口

文件：`backend/src/main/java/com/videodiagnosis/interfaces/controller/internal/InternalAnalysisController.java`

接口：

- `GET /internal/v1/analysis/jobs/{jobId}/context`
- `GET /internal/v1/analysis/jobs/{jobId}/evidence`
- `GET /internal/v1/analysis/jobs/{jobId}/agent-runs/{agentRunId}/trace`
- `POST /internal/v1/analysis/jobs/{jobId}/hypotheses`
- `POST /internal/v1/analysis/jobs/{jobId}/agent-results`
- `POST /internal/v1/analysis/jobs/{jobId}/agent-progress`

内部权限：

- `backend/src/main/java/com/videodiagnosis/interfaces/security/InternalApiAuthFilter.java`
- 测试验证无 `X-Internal-Api-Key` 返回 403。

## 6. Python HarnessRunner

文件：`agent-service/src/agent_service/harness/runner.py`

职责：

- 构造初始 `AgentGraphState`。
- 注入 `run_id/job_id/result_version`。
- 统一 timeout、graph step 限制、turn/token 限制。
- 工具调用统一走 `ToolInterceptor`。
- 审计日志由 `AuditLogger` 记录。

重要实现：

- `run_id = input_payload.get("agent_run_id") or self._trace_id`
- `result_version = 1`
- `_graph.invoke(initial_state, config=config)`

## 7. Python Agent Graph

文件：`agent-service/src/agent_service/graph/builder.py`

节点：

- `plan`
- `tools`
- `diagnose`
- `evaluate`
- `synthesize`

这是 deterministic outer workflow。模型不控制全局流程。

## 8. Planner

文件：`agent-service/src/agent_service/graph/nodes/planner.py`

固定输出三个 Skill：

- `hook_analysis`
- `structure_rhythm_analysis`
- `value_delivery_analysis`

不做 Triage，不让模型决定是否跳过某个业务维度。

## 9. Parallel Diagnosis Skills

文件：`agent-service/src/agent_service/graph/nodes/diagnose.py`

关键实现：

- 多 Skill 时用 `ThreadPoolExecutor` 并行执行。
- 每个 Skill 独立创建 `DiagnosisReActLoop`。
- 单个 Skill 失败会记录在 `skill_execution_status` 和 `error`，不直接污染其他 Skill 的结果。
- 收集 `evidence_refs`、`knowledge_evidence_refs`、`tool_observations`、`retrieval_traces`。

## 10. Local ReAct

文件：`agent-service/src/agent_service/graph/react_loop.py`

ReAct 只在单 Skill 内出现：

```text
Diagnose/Reason
  -> Need Tool
  -> Resolve Tool
  -> Execute Tool
  -> Observation
  -> Re-diagnose
```

限制：

- 最大迭代来自 `settings.max_react_iterations`。
- 工具由 `tool_resolver.py` 确定性映射。
- RAG 工具失败时可降级为 video evidence only。
- 非知识类工具失败时当前 Skill 可失败。

## 11. Evaluator

文件：`agent-service/src/agent_service/graph/nodes/evaluator.py`

检查：

- Finding 数量是否覆盖 plan。
- `observation`、`suggested_action` 是否完整。
- `confidence` 是否超过 `0.6`。
- 是否有 `evidence_refs`。
- 是否只有知识证据而缺少视频证据。
- 是否存在简单冲突。
- 是否还有 evidence gaps。

真实代码中的 decision 是：

- `PASS`
- `RETRY_SKILL`
- `FAILED`

早期设计中提到的 `NEED_MORE_EVIDENCE` 在当前代码里被收敛到 Skill 内 ReAct，不作为外层 evaluator decision。

## 12. Synthesizer

文件：`agent-service/src/agent_service/graph/nodes/synthesizer.py`

职责：

- 遍历 state 中已有 findings。
- 调用 `save_diagnosis_hypothesis` 保存到 Java。
- 生成 `agent_trace`。
- 上报 `SYNTHESIZING` 和 `COMPLETED`。

边界：

- 不生成新的无证据 finding。
- 只汇总已有 Skill 输出。

