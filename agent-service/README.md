# agent-service

独立 Python Agent 服务：LangGraph 图编排 + Agent Harness 运行壳。

- **禁止**直接访问 MySQL / MinIO
- 所有业务读写通过 Java backend `/internal/**` HTTP 接口
- Harness 负责护栏、拦截、审计；LangGraph 仅保存推理草稿 State

详见 `docs/09-agent-service-architecture.md`。

## Specialist Agent Runtime Boundary

当前 Agent Runtime 采用受控 Specialist Multi-Agent，而不是自由聊天式多 Agent：

- **Agent = Executor**：`HookDiagnosisAgent`、`StructureDiagnosisAgent`、`ValueDiagnosisAgent` 只执行各自 descriptor 中声明的 role、goal、capabilities、allowed_tools、skill_binding、knowledge_namespaces 与 output contract。
- **Skill = HOW**：三个诊断 SOP 外置到 `skills/<skill_id>/skill.md`，由 `SkillLoader` 在 AgentRun 启动时加载并生成 immutable snapshot，包含 `skill_id/version/content_hash`。
- **Tool = ACTION**：工具只用于获取 video evidence、knowledge retrieval 和已有 Java internal API 能力；Specialist 不能调用不在 allowed_tools 中的工具。
- **Knowledge = WHAT**：领域规则、pattern、正反例、case 仍在 knowledge corpus 中，通过现有 RAG Retriever 按需查询；Skill 不内嵌完整 corpus。
- **Supervisor = Routing Only**：`CentralSupervisor` 只接收结构化 `HandoffRequest`，通过 `CapabilityRegistry` 做 capability 到 Specialist 的路由，不生成 Finding、不分析视频、不调用业务 Tool。
- **Structured handoff only**：Specialist 不能直接与另一个 Specialist 自由聊天，跨 Specialist 协作必须走 `Specialist -> Evaluator -> Supervisor -> Target Specialist`。
- **Bounded replanning**：全局 `max_global_replans` 和 `max_agent_handoffs` 由 Harness 初始化到 AgentRun state，防止无限循环。
- **Skill update semantics**：Skill 在 AgentRun 开始时 snapshot；运行中磁盘文件变化不影响当前 Run，只影响后续 Run。
- **Independent versions**：Skill snapshot 记录 `skill_id/version/hash`；Knowledge 继续使用现有 corpus/version 机制，两者独立演进。
- **Java remains System of Record**：Java callback contract、业务状态、数据库 schema、Redis 结构不因 Specialist Runtime 改造而改变。

## Harness 结构（2026-10 改造）

Harness 分为运行时（`harness/runner.py`，事件与三个统一入口）、插件（`harness/plugins/`、`harness/interventions.py`）
和组装层（`harness/factory.py`、`services/harness_setup.py`）。业务代码通过 `create_diagnosis_harness(tools)` 获取 harness。
详见 `docs/13-harness-refactor.md`。
