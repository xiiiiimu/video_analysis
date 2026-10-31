# 项目总览

## 一句话

这是一个短视频对比诊断 MVP：Java 后端负责业务事实状态和持久化，Python `agent-service` 负责 Agent Workflow、有限 ReAct、RAG 检索和诊断草稿生成，最终通过回调把结果写回 Java。

## 解决的问题

给定目标视频和参考视频，系统尝试从三个维度生成诊断：

- `hook_analysis`：开头 3-5 秒是否快速建立停留理由。
- `structure_rhythm_analysis`：内容结构、段落推进、节奏变化是否清晰。
- `value_delivery_analysis`：观众收益、使用场景、行动建议是否表达明确。

项目重点不是“让模型自由聊天”，而是把诊断流程工程化：

- 任务状态可落库。
- Agent Run 可追踪。
- 回调可幂等。
- Evidence 可引用。
- RAG 检索可评测。
- 失败和超时有降级/恢复边界。

## 当前真实技术栈

Java 后端：

- Spring Boot 3.3.2，Java 21。
- Spring Web、Validation、Actuator。
- Spring Data JPA，MySQL runtime，H2 test。
- Spring Data Redis，用于进度缓存和回调快速去重。
- MinIO SDK，用于对象存储适配。
- MockWebServer + MockMvc + Spring Boot Test 做集成测试。

Python Agent：

- Python 3.11+。
- FastAPI + Uvicorn。
- LangGraph 组织 Agent Workflow。
- LangChain OpenAI 适配 Chat/Embedding。
- `pytest` 做 workflow、RAG、benchmark 测试。
- 内存 BM25/keyword baseline、OpenAI embedding cosine 检索、RRF/weighted RRF benchmark。

## 真实完成度

已经完成：

- Java DDD 分层骨架和核心异步 Agent 链路。
- `AnalysisJob` 状态机、Agent dispatch、timeout recovery、callback 幂等。
- Redis 任务进度缓存，MySQL/JPA 仍是业务事实源。
- Python Agent 主流程：`Planner -> Parallel Diagnosis Skills -> Evaluator -> Synthesizer`。
- 单 Skill 内有限 ReAct：证据不足时调用工具补证，再重新诊断。
- EvidenceRef 模型：视频证据和知识证据统一用引用串关联。
- Agent Trace：保存轻量执行路径，不记录 chain-of-thought。
- RAG benchmark：v0.3 benchmark corpus 34 条，v0.5 dev/test split，最终 test 报告已生成。

没有完成或不应夸大：

- 没有 Kafka/RocketMQ。
- 没有 Elasticsearch、Milvus、PGVector 等外部向量数据库。
- 没有生产级高并发压测。
- 没有分布式事务。
- 没有宣称线上 SLA。
- JPA `@Version` 是乐观锁，不是数据库 CAS。
- Redis 回调 key 是快速重复拦截，最终幂等防线是数据库唯一记录。

## 项目目录

- `backend/`：Java 后端，DDD 分层、任务状态、持久化、内部接口。
- `agent-service/`：Python Agent runtime、工具适配、RAG、benchmark。
- `agent-service/benchmarks/`：Golden Dataset 和 dev/test split。
- `agent-service/benchmark-reports/`：真实 benchmark 输出。
- `docs/interview/`：本次生成的面试交接材料。

## 面试推荐表达

可以这样说：

“我做的是一个短视频诊断 Agent 的工程化 MVP。业务事实状态全部在 Java 后端管理，包括任务、视频资产、证据、Finding、回调幂等和权限；Python 只负责单次 Agent Run 的编排、推理、工具调用和诊断草稿。Agent 外层流程是确定性的，内部只有在单个诊断 Skill 证据不足时允许有限 ReAct，避免整个 workflow 失控。同时我为 RAG 建了人工审核 Golden Dataset、hard negative 指标和 dev/test benchmark，最后用真实 OpenAI embedding 跑了 held-out test，并保留了没有超预期的真实结果。”

