# 面试问答

## 1. 这个项目一句话怎么介绍？

这是一个短视频对比诊断 Agent MVP。Java 后端负责业务事实状态、任务流转、证据、Finding、持久化、回调幂等和权限；Python `agent-service` 负责单次 Agent Run 的编排、推理、工具调用、RAG 检索和诊断草稿生成。

## 2. 为什么要 Java + Python 双服务？

Java 更适合承载稳定业务系统，例如任务状态、事务、持久化、权限和内部接口。Python 更适合快速迭代 Agent Workflow、LangGraph、RAG 和模型调用。两者用 HTTP 内部接口连接，边界清楚：Java 是 System of Record，Python 是 Agent Runtime。

## 3. DDD 分层体现在哪里？

Java 后端按接口层、应用层、领域层、基础设施层组织。比如 `AnalysisJob` 是领域实体，`DispatchAgentCase` 和 `HandleAgentResultCase` 是应用用例，`AnalysisJobRepository` 是领域仓储接口，JPA/Redis/HTTP client 在基础设施层。

## 4. 你怎么保证 Agent 不把业务状态搞乱？

Python 的 `AgentGraphState` 只保存单次 Agent Run 的运行上下文，例如 plan、findings、evidence refs、tool results、step traces。真实业务状态在 Java 的 `AnalysisJob` 和数据库中。Python 只能通过内部接口保存 hypothesis、上报进度、回调结果，不能直接改数据库状态。

## 5. Agent Workflow 是什么？

外层是确定性流程：`Planner -> Parallel Diagnosis Skills -> Evaluator -> Synthesizer`。三个 Skill 是 `hook_analysis`、`structure_rhythm_analysis`、`value_delivery_analysis`。只有单个 Skill 证据不足时，内部才做有限 ReAct。

## 6. 为什么不做多 Agent / Supervisor / Debate？

MVP 阶段更重要的是可控性和可解释链路。视频诊断的三个维度可以并行，但不需要设计成彼此独立的 Agent。外层固定流程减少不可控分支，内层 ReAct 只在证据不足时触发，便于测试和回调。

## 7. ReAct 怎么做的？

ReAct 在 `DiagnosisReActLoop` 内。流程是 Reason 判断证据是否足够，如果不够就根据 evidence type 通过 `tool_resolver` 找工具，执行后拿 Observation，再重新诊断。它有 `max_react_iterations` 限制，避免无限循环。

## 8. Evidence 怎么设计？

Finding 不复制大量视频帧或长文本，而是通过 `evidence_refs` 和 `knowledge_evidence_refs` 指向证据。比如 `ASR:target`、`OCR:target`、`METADATA:target`、`KNOWLEDGE:xxx`。这样 Java 可以保存业务结果，Python trace 也能说明结论来自哪里。

## 9. Redis 在项目中做什么？

Redis 做两件轻量事情：任务进度缓存和 callback 快速去重。进度 key 是 `analysis:job:{jobId}:progress`，用于快速查询当前 stage。Redis 不作为业务事实源，MySQL/JPA 里的 `AnalysisJob` 才是准的。

## 10. 回调幂等怎么保证？

Python callback 会带 `agentRunId` 和 `resultVersion`。Java 先查 Redis 快速拦截，再查 DB callback record 兜底。处理成功后写 DB record 和 Redis key。旧 `agentRunId` 回调会被拒绝，重复 `(agentRunId, resultVersion)` 会被忽略。

## 11. `@Version` 是不是 CAS？

不是。`@Version` 是 JPA 乐观锁，用来避免并发更新覆盖。它不是数据库层面的 CAS 指令，也不是分布式锁。

## 12. Agent Trace 记录什么？

记录轻量执行路径：`runId`、`stepType`、`skillCode`、`toolName`、`evidenceRefs`、`latencyMs`、`status`、`shortSummary`。不记录 chain-of-thought，只记录可审计的执行摘要。

## 13. RAG 为什么要 benchmark？

早期小 corpus 下 Recall@5 很容易虚高，不能证明检索能力。所以后面构建了 v0.3 benchmark corpus、hard negative、人工 VERIFIED Golden Query、dev/test split，并且只用 held-out test 报正式结果。

## 14. v0.3 corpus 有什么特点？

v0.3 benchmark corpus 有 34 条 knowledge，三个 Skill 分布是 12/11/11。它包含语义相似但边界不同的 hard negative pair，例如 hook 的“自我介绍拖慢开场”和“权威背书快速接收益”，以及 hook/value 的“首屏视觉证据”和“证据支撑价值主张”。

## 15. 为什么不用向量数据库？

当前 benchmark corpus 只有 34 条，使用内存向量索引足够，重点是验证算法、评测数据和指标。引入 Milvus/PGVector 会增加部署复杂度，但不能实质提升这个阶段的算法验证价值。后续 corpus 扩大后再迁移向量库更合理。

## 16. 最终 benchmark 结果怎样？

Held-out test 20 条 VERIFIED query 上，`HYBRID_BM25_EMBEDDING_RRF_05_05` 最好，`Recall@1 = 0.6000`，`Recall@5 = 0.9000`，`MRR = 0.7363`，`HardNegAboveExpected = 0.1500`。Dev 选出的 `0.7/0.3 Final Weighted Hybrid` 没有超过 0.5/0.5 hybrid，这一点我保留在报告里，没有调 test 集。

## 17. 你怎么解释 dev 选出的参数 test 没赢？

这是正常的 dev/test 波动，尤其 test 只有 20 条。它说明当前数据规模还小，某个权重在 dev 上更优不代表一定泛化。对我来说更重要的是遵守实验纪律：参数在 dev 上选，test 只跑一次，不根据 test miss 回调参。

## 18. 项目里最有工程含量的点是什么？

不是单点模型调用，而是端到端闭环：Java 状态机、异步 dispatch、`agentRunId/resultVersion` 幂等、Redis 进度缓存、Python bounded Agent Workflow、EvidenceRef grounding、Agent Trace 和 RAG benchmark。

## 19. 如果某个 Skill 失败，会影响其他 Skill 吗？

Python 并行执行每个 Skill，每个 Skill 有自己的 ReAct loop 和执行结果。单 Skill 失败会记录状态和 error，Evaluator 再决定 retry 或 fail，不会直接污染其他 Skill 的 findings。

## 20. RAG timeout 怎么处理？

当前设计里知识检索失败会降级为 video evidence only，避免 RAG 服务不可用导致整个 AgentRun 直接失败。但非知识类工具，例如视频证据工具失败，当前 Skill 可能失败，再交给 Evaluator 处理。

## 21. Synthesizer 会不会编新结论？

不会。`synthesizer_node` 只遍历 state 中已有 findings，调用 `save_diagnosis_hypothesis` 保存，并生成 trace。它不做新的 LLM 推理，也不生成无证据结论。

## 22. 真实 ASR/OCR/FFmpeg 做了吗？

项目里有 Java `FfmpegMediaAdapter` 和 Python 工具接口/证据模型，但当前重点是 Agent workflow 与工程闭环。是否已经接入真实 ASR/OCR 要按当前 adapter 实现讲，不能夸大成生产级多媒体处理平台。

## 23. 测试覆盖了什么？

Java 集成测试覆盖 Agent dispatch、callback success/fail、内部鉴权、重试、timeout recovery、重复 callback、stale callback、Agent Trace 查询。Python 测试覆盖 workflow、ReAct、RAG corpus、review CLI、retrieval metrics、embedding provider、benchmark runner 等。

## 24. 项目有哪些不足？

- 当前还不是生产级系统。
- 没有 MQ，dispatch 是 HTTP。
- 没有外部向量数据库。
- Benchmark test 样本只有 20 条，还需要扩大。
- Runtime RAG 默认 corpus 仍是 MVP 6 条。
- 前端和真实视频处理链路还可以继续完善。

## 25. 如果继续做，你会做什么？

优先做三件事：一是扩大人工标注 dataset 和 hard negatives；二是把 runtime corpus 和 benchmark corpus 的知识治理流程打通；三是根据 corpus 规模决定是否引入 PGVector/Milvus，并补充冷启动 embedding latency 和 cache 策略。

