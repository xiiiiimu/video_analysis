# Agent-Service 架构与目录说明

## 1. 完整目录树

```
e:\video\
├── agent-service/                          # 独立 Python Agent 服务（根级）
│   ├── Dockerfile
│   ├── README.md
│   ├── pyproject.toml
│   ├── .env.example
│   └── src/
│       └── agent_service/
│           ├── __init__.py
│           ├── main.py                     # 入口：Harness 包装 LangGraph 运行
│           ├── config.py                   # 环境配置（禁止 DB/MinIO 连接项）
│           ├── api/
│           │   ├── __init__.py
│           │   └── routes.py               # FastAPI：接收 Java 触发 / 健康检查
│           ├── harness/                    # Agent Harness 运行壳（外层治理）
│           │   ├── __init__.py
│           │   ├── runner.py               # 任务生命周期、invoke graph
│           │   ├── tool_interceptor.py     # ★ 统一工具拦截 + 护栏
│           │   ├── guardrails.py           # 轮次/token 上限
│           │   ├── memory.py               # 会话草稿记忆（非权威数据）
│           │   ├── audit.py                # 可观测审计日志
│           │   ├── limits.py               # 跨平台超时熔断
│           │   └── types.py
│           ├── graph/                      # LangGraph 图编排
│           │   ├── __init__.py
│           │   ├── state.py                # Agent 临时 State（仅推理草稿）
│           │   ├── builder.py              # 编译 StateGraph
│           │   ├── nodes/
│           │   │   ├── __init__.py
│           │   │   ├── planner.py          # 规划推理节点
│           │   │   ├── reasoner.py         # 中间推理节点
│           │   │   └── tool_router.py      # 工具调度节点
│           │   └── edges/
│           │       ├── __init__.py
│           │       └── conditions.py     # 条件边路由
│           ├── tools/                      # 工具适配层（HTTP → Java /internal）
│           │   ├── __init__.py
│           │   ├── base.py
│           │   ├── registry.py
│           │   └── adapters/
│           │       ├── __init__.py
│           │       ├── http_client.py      # JavaBackendHttpClient
│           │       └── analysis_job.py     # 任务上下文 / 结果回写
│           └── llm/
│               ├── __init__.py
│               ├── provider.py             # ChatOpenAI 封装
│               └── prompts/
│                   ├── __init__.py
│                   └── diagnosis.py        # prompt 模板
├── backend/                                # Java SpringBoot DDD（不变更 domain）
│   └── src/main/java/com/videodiagnosis/
│       ├── interfaces/controller/internal/ # ★ 新增内部接口
│       │   └── InternalAnalysisController.java
│       ├── application/
│       │   ├── service/InternalAnalysisFacadeService.java
│       │   └── usecase/RecordAgentDraftCase.java
│       └── infrastructure/client/
│           └── ModelClientAdapter.java     # @Deprecated，LLM 迁移至 Python
└── docker-compose.yml                      # 新增 agent-service 服务
```

## 2. 职责边界

| 层级 | 职责 | 禁止 |
|------|------|------|
| Java domain | 业务规则、实体、仓储接口 | AI/LangGraph/Agent 依赖 |
| Java application | 用例编排、事务、状态流转 | 直接调 LLM |
| Java interface/internal | 内部 HTTP 转发 | 重复写业务逻辑 |
| Python Harness | 生命周期、护栏、拦截、审计 | 写 prompt / 业务 node |
| Python LangGraph | 图编排、推理草稿 State | 存权威业务实体 |
| Python tools/adapters | HTTP 参数转换 | 业务规则、直连 DB |

## 3. 完整任务数据流

```
[1] 用户请求
    POST /api/v1/analysis/jobs
         │
         ▼
[2] Java Interface 层
    AnalysisCommandController
         │
         ▼
[3] Java Application 层
    AnalysisCommandService
    → CreateAnalysisJobCase（落库 MySQL，domain 无 Agent 感知）
    → ExecuteDiagnosisCase（异步触发）
         │
         ├─(过渡期) AnalysisJobWorkflow 本地编排
         │
         └─(目标态) HTTP 调用 agent-service
              POST http://agent-service:8090/api/v1/agent/runs
                   │
                   ▼
[4] Python agent-service
    FastAPI routes.run_agent()
         │
         ▼
[5] HarnessRunner.run(task_id, payload)
    ├─ 初始化 HarnessContext（轮次/token/审计）
    ├─ ToolInterceptor 注册白名单工具
    ├─ MemoryManager 管理会话草稿
    └─ compiled_graph.invoke(initial_state)
              │
              ▼
[6] LangGraph 图流转（仅草稿 State）
    plan_node → tool_router_node → reason_node → tool_router_node → END
    State 字段：job_id, draft_messages, draft_observations, next_action, done
    ❗ 不存 Finding / VideoAsset / AnalysisJob 实体
              │
              ▼
[7] tool_router_node 通过 Harness.call_tool()
    → ToolInterceptor.before_call()  // 护栏统一在此
    → tools/adapters/analysis_job.py
    → JavaBackendHttpClient
              │
              ▼
[8] Java /internal/** 接口
    InternalAnalysisController
    → InternalAnalysisFacadeService（仅转发）
    → AnalysisQueryService / RecordAgentDraftCase
    → Repository → MySQL（权威数据落库）
              │
              ▼
[9] Agent 完成，Harness 返回 HarnessRunResult
    status / turns / audit_events
              │
              ▼
[10] Java 更新任务状态，用户轮询
     GET /api/v1/analysis/jobs/{jobId}/result
```

## 4. Java 侧最小改动说明

### 4.1 新增 internal 包

路径：`com.videodiagnosis.interfaces.controller.internal`

示例接口：

- `GET  /internal/v1/analysis/jobs/{jobId}/context` — agent 拉取任务上下文
- `POST /internal/v1/analysis/jobs/{jobId}/agent-results` — agent 回写推理草稿

鉴权：请求头 `X-Internal-Api-Key`，配置项 `app.internal.api-key`。

### 4.2 复用已有 application 用例

`InternalAnalysisFacadeService` 只做转发：

```java
// 查询：复用 AnalysisQueryService.getJob()
AnalysisJob job = analysisQueryService.getJob(jobId);

// 回写：复用 RecordAgentDraftCase（application/usecase）
recordAgentDraftCase.execute(jobId, draftObservations);
```

**原则**：Internal Controller → FacadeService → 已有 Case/Service → Domain Repository，不在 interface 层写业务。

### 4.3 infrastructure/client LLM 迁移提示

`ModelClientAdapter` 已标记 `@Deprecated`：

- 原职责：`inferObservation()` / `summarizeFindings()` 本地 LLM 占位
- 迁移方向：由 Python agent-service 承担 LLM 调用
- 过渡期：`RevisionPlanWorkflow` / `BuildResultCase` 仍引用此类，后续改为 HTTP 调 agent-service 或删除

## 5. Docker 网络

| 服务 | 容器名 | 端口 | 互联 |
|------|--------|------|------|
| app | video-app | 8080 | mysql, redis, minio |
| agent-service | video-agent-service | 8090 | app (JAVA_BACKEND_BASE_URL=http://app:8080) |

启动：

```bash
docker compose up -d --build
```

## 6. 本地开发

```bash
# Python agent-service
cd agent-service
pip install -e .
cp .env.example .env
python -m agent_service.main

# Harness 演示模式（不启 HTTP）
RUN_HARNESS_DEMO=1 python -m agent_service.main
```

## 7. pyproject.toml 基础依赖

```toml
dependencies = [
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "httpx>=0.27.0",
    "pydantic>=2.8.0",
    "python-dotenv>=1.0.0",
]
```

（另含 fastapi / uvicorn 用于 HTTP 服务骨架。）

## 8. 禁止行为检查清单

- [x] 未修改 Java domain 实体与业务规则
- [x] Python 无 MySQL / MinIO 连接配置
- [x] Harness 护栏集中在 `tool_interceptor.py`，node 内无护栏
- [x] LangGraph State 仅草稿字段，权威数据走 Java
