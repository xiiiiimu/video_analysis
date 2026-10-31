# Video Diagnosis Agent 面试交接阅读顺序

这套文档用于秋招面试前快速复盘当前仓库的真实实现，不是对外宣传稿。阅读时建议始终带着一个边界：Java 是业务事实源，Python `agent-service` 是单次 Agent Run 的编排、推理、工具调用和诊断草稿生成。

## 推荐顺序

1. `01_PROJECT_OVERVIEW.md`
   - 先建立项目一句话、业务问题、MVP 范围、技术栈和可诚实表达的完成度。
2. `02_ARCHITECTURE_AND_FLOW.md`
   - 再看 Java + Python 的端到端链路、状态边界、回调幂等、Redis 进度和 Agent Trace。
3. `03_CORE_CODE_WALKTHROUGH.md`
   - 面试时最容易被追问“你具体写了什么”，这一份按核心类和函数讲代码。
4. `04_RAG_AND_AGENT_EXPERIMENTS.md`
   - 复盘 RAG benchmark、v0.3/v0.5 数据集、Embedding 接入、最终 test 真实结果。
5. `05_INTERVIEW_QA.md`
   - 直接用于背问答，包含追问版回答和不能夸大的点。
6. `06_RESUME_AND_STORY.md`
   - 最后提炼成简历 bullet、项目讲述稿和 STAR 故事。

## 面试主线

- 项目不是“做了一个大模型玩具”，而是把短视频诊断拆成可落库、可回调、可追踪、可评测的工程闭环。
- Java 后端采用 DDD 分层，负责 `AnalysisJob`、视频资产、证据、Finding、任务状态、回调幂等、权限和查询。
- Python `agent-service` 采用 deterministic outer workflow + bounded agentic inner loop：外层固定流程，单个 Skill 内有限 ReAct。
- Evidence 是一等公民：Finding 通过 `EvidenceRef` 指向 ASR/Frame/OCR/Metadata/Knowledge，不复制大量原文。
- RAG 不是只做 demo：有 v0.3 benchmark corpus、人工 VERIFIED Golden Dataset、dev/test split、hard negative 指标和真实 benchmark 报告。
- 当前真实短板也要坦诚：没有上生产级向量库，没有 MQ，没有高并发压测，没有完整前端产品化，没有真实线上 SLA。

## 快速面试版本

如果只有 15 分钟，按这个顺序看：

1. `01_PROJECT_OVERVIEW.md` 的“一句话”和“项目边界”。
2. `02_ARCHITECTURE_AND_FLOW.md` 的“端到端调用链”和“状态边界”。
3. `04_RAG_AND_AGENT_EXPERIMENTS.md` 的“最终 held-out test 结果”和“实验结论”。
4. `05_INTERVIEW_QA.md` 的前 10 个高频问题。

