# 短视频对比诊断 Agent 系统

面向短视频内容优化的 Java + Python 双服务项目。输入目标视频、参考视频与可选的用户自定义评分标准，从开场钩子、结构节奏、价值传递三个维度生成带原文证据的诊断与改进建议。

## 主要能力

- **多模态证据**：FFmpeg 镜头检测与抽帧、并行 OCR、Whisper 分段转写，构建默认 120 秒分析窗口的证据时间轴。
- **多 Agent 编排**：Supervisor → 三路并行 Specialist → Evaluator → Synthesizer，支持有界 ReAct、定向打回、重新规划及超限降级。
- **证据治理**：核验原文引用、评分依据及跨维度矛盾，结论绑定证据；信息不足时弃权或降级。
- **上下文管理**：以结构化 State 保存任务草稿、反馈和交接信息；按维度裁剪证据，限制输入长度并显式标记截断。当前不提供跨会话长期记忆。
- **运行治理**：事件与插件驱动的 Harness，统一管理预算、工具权限、取消检查点、模型重试与执行审计。
- **评分规范检索**：BM25 + Embedding 混合检索、RRF 排序，支持评分依据追溯和用户自定义标准。
- **异步可靠性**：任务状态机、退避重试、超时回收、新旧运行隔离、回调幂等与跨服务日志追踪。

## 架构与目录

Java 是业务事实源，负责任务、证据和结果持久化；Python 负责单次 Agent 运行，通过 Java internal API 读写业务数据，不直接访问 MySQL 或 MinIO。

```text
浏览器 → Spring Boot → MySQL / Redis / MinIO
                  ↕ 内部 HTTP 接口与结果回调
              FastAPI + LangGraph
                  ├─ Specialist × 3
                  ├─ Evaluator / Synthesizer
                  └─ Harness / Skills / RAG
```

| 路径 | 内容 |
| --- | --- |
| backend/ | Java 后端及最小联调页面 |
| agent-service/src/ | Python Agent、运行治理与检索代码 |
| agent-service/skills/ | 专家诊断 SOP |
| agent-service/knowledge/ | 评分规范与知识库 |
| agent-service/tests/ | Python 测试 |
| benchmark-reports/ | 已保存的评测报告 |
| docs/ | 架构、设计与验证文档 |
| docker-compose.yml | 本地多服务部署 |

## 快速启动

准备 Git、Docker Desktop（启用 Docker Compose）。容器构建会安装所需运行依赖；本地开发需 Java 21、Maven、Python 3.11+，媒体处理还需 FFmpeg 与 Tesseract。

```powershell
git clone https://github.com/xiiiiimu/video_analysis.git
Set-Location video_analysis
Copy-Item .env.example .env
notepad .env
```

在根目录 `.env` 中修改内部接口密钥、数据库与对象存储密码，并配置模型服务：

- 使用 DeepSeek 时填写 `DEEPSEEK_API_KEY`；也可使用 `CHAT_API_KEY`、`CHAT_MODEL`、`CHAT_BASE_URL` 配置兼容接口。
- Whisper 转写单独配置 `ASR_API_KEY` 或有效的 `OPENAI_API_KEY`。DeepSeek 密钥不能用于 OpenAI 转写。
- `LLM_MOCK=1` 可用于模拟模型诊断，不代表真实模型效果，也不会模拟整个媒体处理链路。
- Python 独立运行的更多配置见 `agent-service/.env.example`。Docker 模式仅会传入 Compose 声明的变量，新增配置需同步检查 `docker-compose.yml`。

```powershell
docker compose up -d --build
docker compose ps
```

默认入口：

- 联调页面：http://localhost:8080/index.html
- 后端健康检查：http://localhost:8080/api/v1/health
- MinIO 控制台：http://localhost:9001

上传目标视频、参考视频及可选的评分标准 TXT，创建诊断任务后查询状态与结果。端口可在 `.env` 中调整。

```powershell
# 查看日志
docker compose logs --tail 100 app agent-service
# 停止服务并保留数据
docker compose stop
```

## 测试与质量评测

```powershell
# Java 测试（本机需 Java 21 与 Maven）
mvn -f backend/pom.xml test

# Python 测试（本机开发环境）
Set-Location agent-service
python -m pip install -e ".[dev]"
python -m pytest
Set-Location ..

# 真实模型质量评测：需要密钥，会产生模型调用费用
docker compose exec agent-service python -m agent_service.eval.quality_benchmark --rules v1,v2 --repeat 2
docker compose exec agent-service python -m agent_service.eval.quality_benchmark --rules v2 --repeat 3 --cases hard
docker compose cp agent-service:/tmp/quality-reports ./benchmark-reports/quality
```

切换模型时需更新配置并重建对应服务容器；具体评测条件与结果以报告为准。

### 已记录结果与适用范围

- 构造证据集：26 组证据包，同模型、同题集各运行 2 次，v1 → v2 的预埋问题命中为 **32/42 → 41/42**，误报为 **79/172 → 0/172**。这是规则判分的诊断逻辑评测，不代表真实视频总体准确率，匹配口径见报告。
- 单次端到端实测（2026-10-30，北京时间）：目标视频 88.9 秒、参考视频 85.4 秒、4 条自定义标准；目标上传与预处理 69.8 秒、参考上传与预处理 47.1 秒、建任务至完成 45.1 秒，总计 **162.1 秒**，不是多次中位数。
- 该次模型调用共 4 次、54,065 token，模型费用按小时账单分摊估算约 **¥0.08**；转写费用按时长和单价估算约 **¥0.12**，总计约 **¥0.20**，未逐任务核账。

## 设计文档

- [Agent 服务架构](docs/09-agent-service-architecture.md)
- [Harness 重构](docs/13-harness-refactor.md)
- [编排设计](docs/14-orchestration-refactor.md)
- [诊断质量](docs/16-diagnosis-quality.md)
- [用户评分标准](docs/17-user-criteria.md)
- [Java 可靠性与日志追踪](docs/18-java-reliability-and-tracing.md)

## 上传文件约定

`.gitignore` 排除真实环境配置、密钥文件、本地视频音频、构建产物、缓存、改造备份及误放在根目录的 Python 安装文件。保留源码、脱敏配置示例、知识库、测试和评测报告。提交前请检查报告及文档中是否含私人视频文案或其他不适合公开的材料。

本项目是本地开发与验证项目；耗时和费用随视频、模型与运行环境变化。
