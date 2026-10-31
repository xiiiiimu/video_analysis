# 遗留代码说明（Legacy Code Note）

> 面向后续维护人员：说明哪些类已废弃、为何废弃、以及当前正式业务流转路径。

## 1. 背景

项目在「四阶段改造」后，诊断推理已从 **Java 进程内同步编排** 迁移至 **Python agent-service 异步链路**：

- Java：DDD 业务、持久化、权限、媒体处理、任务状态机
- agent-service：LangGraph 推理 + Harness 护栏 + LLM 调用
- 二者通过 HTTP 解耦：Java 提交任务 → agent 回调 `/internal/**`

**domain 层未引入任何 Agent/LLM 依赖**，状态流转仍通过 `AnalysisJob` 领域方法完成。

---

## 2. 已废弃类（@Deprecated，保留源码）

| 类 | 包路径 | 废弃原因 |
|---|---|---|
| `ExecuteDiagnosisCase` | `application.usecase` | 原同步诊断入口，内部调用 `AnalysisJobWorkflow`，会阻塞 Java 线程并完成全流程 |
| `AnalysisJobWorkflow` | `application.workflow` | 原 Java 内存编排：预处理 → 诊断 → 修订，含 Java 侧模型占位调用 |
| `ModelClientAdapter` | `infrastructure.client` | 原 Java 内 LLM 占位适配器，LLM 已迁移至 agent-service |

> **注意**：以上类 **未删除**，仅供历史比对与迁移参考。**新业务禁止调用**。

### 2.1 `ExecuteDiagnosisCase`

```java
// 历史路径（已废弃）
createJob → ExecuteDiagnosisCase.execute(jobId)
         → AnalysisJobWorkflow.execute(jobId)  // 同步、阻塞
```

问题：

- Java 进程内等待推理完成，无法独立扩缩容 Agent
- 与「domain 无 Agent 感知」的长期目标冲突（编排层耦合了模型时序）

### 2.2 `AnalysisJobWorkflow`

原职责：

1. `PreprocessWorkflow` 预处理
2. `DiagnosisWorkflow` 领域诊断
3. `RevisionPlanWorkflow` + `ModelClientAdapter` 生成修订建议

现职责已拆分：

- 预处理/媒体：仍可在 Java 保留（按产品演进）
- **推理与修订草案**：agent-service LangGraph + Harness
- **结果落库**：`HandleAgentResultCase` 接收回调

---

## 3. 当前正式业务流转路径

```
[前端]
  POST /api/v1/analysis/jobs
       │
       ▼
[Java Interface]  AnalysisCommandController
       │
       ▼
[Java Application]
  CreateAnalysisJobCase        → PENDING 落库（MySQL）
  StartAgentDiagnosisCase      → RUNNING 落库 + HTTP 提交 agent（不等待）
       │
       │  POST http://agent-service:8090/api/v1/agent/jobs/submit
       ▼
[agent-service]
  HarnessRunner → LangGraph → tools/adapters
       │
       │  GET  /internal/v1/analysis/jobs/{id}/context
       │  POST /internal/v1/analysis/jobs/{id}/agent-results
       ▼
[Java Internal API]  InternalAnalysisController
       │
       ▼
[Java Application]  HandleAgentResultCase
       ├─ SUCCESS → markCompleted()
       └─ FAILED  → markFailed(errorMessage)
       │
       ▼
[MySQL 权威数据]

[前端轮询]
  GET /api/v1/analysis/jobs/{id}/result   ← 仅访问 Java，不知道 agent-service 存在
```

### 3.1 关键活跃类（请优先阅读）

| 类 | 职责 |
|---|---|
| `StartAgentDiagnosisCase` | 置 RUNNING + 异步 HTTP 提交 agent |
| `HandleAgentResultCase` | 处理 agent 回调 SUCCESS/FAILED |
| `AgentServiceHttpClient` | 调用 agent-service 提交接口 |
| `InternalAnalysisController` | `/internal/**` 门面，仅转发 |
| `InternalApiAuthFilter` | `X-Internal-Api-Key` 鉴权（无 token → 403） |
| `AnalysisJobTimeoutGuardian` | 扫描超时 RUNNING 任务 → FAILED |

---

## 4. 集成测试

骨架类：`src/test/java/com/videodiagnosis/integration/AnalysisAgentIntegrationTest.java`

| 场景 | 验证点 |
|---|---|
| ① | `StartAgentDiagnosisCase` → `RUNNING` |
| ② | 模拟 agent SUCCESS 回调 → `COMPLETED` |
| ③ | 模拟 agent FAILED 回调 → `FAILED` + `errorMessage` |
| ④ | 无 `X-Internal-Api-Key` → 403 |

测试方案：**MockWebServer** 模拟 agent-service 提交端点 + **MockMvc** 模拟 agent 回调。

运行（需本地 Maven 环境）：

```bash
cd backend
mvn test -Dtest=AnalysisAgentIntegrationTest
```

---

## 5. 维护建议

1. **不要** 在新功能中注入 `ExecuteDiagnosisCase` / `AnalysisJobWorkflow`
2. 扩展 Agent 能力请改 **agent-service**（graph / harness / tools），Java 只增 `/internal/**` 转发接口
3. 若需回放历史同步逻辑，可临时调用废弃类做对比，但 **不得合入主干业务流程**
4. 后续若确认无参考价值，可在 major 版本中删除废弃类，并同步更新本文档

---

## 6. 相关文档

- `docs/09-agent-service-architecture.md` — agent-service 目录与职责边界
- `docs/10-async-agent-verification.md` — docker compose 联调步骤
