# 14. 编排层改造（handoff 闭环 / 评估反馈 / 合成 / 批量幂等保存）

承接 `13-harness-refactor.md`。13 解决了“运行时怎么跑”（hooks、插件、限额、取消、重试），
本篇解决“专家之间怎么协作、结论怎么落库”，并把上一轮审查列出的 16 个问题逐条处理。

## 1. 编排流程（改造后）

```
supervisor ──> diagnose(3 专家, 并行) ──> evaluator ──┬─ PASS ──────────> synthesizer ──> END
    ^                                                 ├─ RETRY(带反馈) ─> diagnose
    |                                                 └─ HANDOFF ───────> supervisor
    └──────────────── 一次只路由一个 handoff 请求 ────────────────────────┘
```

### 1.1 Handoff 闭环（原来是“发出去就没了”）

| 阶段 | 谁运行 | 行为 |
|---|---|---|
| 定向调查 `TARGETED_REINVESTIGATION` | 被求助的专家(target) | 只回答问题，答案写入 `handoff_answers`；**不覆盖** target 自己原来的 finding；设置 `pending_integration={source_agent, answer}`，`next_action="diagnose"` |
| 整合 `HANDOFF_INTEGRATION` | 发起求助的专家(source) | 带着答案重跑（prompt 里有 `handoffAnswer`），产出的 finding 合并答案的 `evidence_refs` 并附 `handoff_answer` 记录 |
| 兜底 | evaluator | 预算用完/无法解析的请求进 `dropped_handoffs`；结束时仍为 `NEEDS_CAPABILITY` 的 finding 转为 `ABSTAIN`（`handoff_rejected.reason="handoff_not_resolved"`），run 状态记为 `COMPLETED_WITH_GAPS` |

supervisor 每次只路由一个请求（`request_id="handoff-N"`），其余保留在队列；超预算时不再 FAILED，而是丢弃剩余请求并进入评估。

### 1.2 Evaluator

- **反馈重试**：不合格的专家拿到逐 skill 的 `retry_feedback`，下一轮以 `RETRY_WITH_FEEDBACK` 模式运行，prompt 中带 `evaluatorFeedback`。
- **证据引用校验**：`diagnosis_skill.known_evidence_refs()` 汇总证据包里真实存在的 ref；LLM 编造的 ref 从 finding 中剔除并记到 `invalid_evidence_refs`，evaluator 据此要求重试。
- **冲突检测**：`_OPPOSING_DIRECTIVES` 识别中文相反建议（如“加快/放慢节奏”“缩短/延长开场”），写入合成结果的 `conflicts`。
- **部分完成**：单个专家崩溃(`system_failure`)时能重试就重试，否则只要有其它专家完成就以部分结果 PASS，缺失的专家补 `ABSTAIN` 占位；全部失败才 FAILED。

### 1.3 Synthesizer

- `graph/synthesis.py::build_rule_synthesis`：按 `DIMENSION_WEIGHT`（HOOK 1.0 / VALUE 0.9 / STRUCTURE 0.8）× confidence 排优先级，产出 `summary / priorities / mergedActions / evidenceGaps / conflicts / handoffs`。
- `refine_with_llm`：可选，走 `call_model`（受 harness 限额与重试约束），失败回退到规则结果；`merge_llm_synthesis` 会忽略 LLM 编造的 skill key。
- 只保存 `FINDING` / `ABSTAIN`，通过新接口批量保存（见 §2）；旧版 Java 返回 404/405/500/501 时降级为逐条保存，幂等键 `{run_id}:v{version}:{skill_key}`。

## 2. 新增 Java 接口

### 2.1 `POST /internal/v1/analysis/jobs/{jobId}/diagnosis-results`（内部，需 `X-Internal-Api-Key`）

```json
{
  "jobId": "job-1",
  "agentRunId": "run-7",
  "resultVersion": 1,
  "idempotencyKey": "run-7:v1",
  "findings": [ { "...InternalHypothesisRequest", "skillKey": "hook_analysis", "outcome": "FINDING", "findingType": "..." } ],
  "synthesis": { "summary": "...", "priorities": [] }
}
```

响应：`{"jobId": "job-1", "findingIds": ["..."], "duplicate": false}`

- `@Transactional`：findings 与 `diagnosis_result_record` 一起提交或一起回滚。
- 相同 `idempotencyKey` 再次提交 → 不写库，返回原来的 `findingIds`，`duplicate=true`。
- 路径 jobId 与 body jobId 不一致 → 400。
- ABSTAIN 的 finding 状态为 `agent_abstain`，正常为 `agent`。

单条接口 `POST .../hypotheses` 也支持可选的 `idempotencyKey`，保持向后兼容。

### 2.2 `GET /api/v1/analysis/jobs/{jobId}/synthesis`（对外）

返回该 job 最近一次保存的 synthesis JSON，供前端展示“综合结论 / 优先级”。

### 2.3 数据库

新表 `diagnosis_result_record`（H2/`ddl-auto=update` 会自动建）。MySQL 生产库若关闭了自动建表，需要手工执行：

```sql
CREATE TABLE diagnosis_result_record (
  id               VARCHAR(255) NOT NULL PRIMARY KEY,
  job_id           VARCHAR(255) NOT NULL,
  agent_run_id     VARCHAR(255),
  result_version   INT,
  idempotency_key  VARCHAR(191) NOT NULL,
  finding_ids_json LONGTEXT,
  synthesis_json   LONGTEXT,
  created_at       DATETIME(6),
  CONSTRAINT uk_diagnosis_result_idempotency UNIQUE (idempotency_key)
);
CREATE INDEX idx_diagnosis_result_job_id ON diagnosis_result_record (job_id);

-- finding 表的长文本字段改为 LONGTEXT（实体已加 @Lob；ddl-auto=update 不会改已存在列的类型）
ALTER TABLE finding
  MODIFY observation             LONGTEXT,
  MODIFY target_evidence_json    LONGTEXT,
  MODIFY reference_evidence_json LONGTEXT,
  MODIFY difference_text         LONGTEXT,
  MODIFY hypothesis_text         LONGTEXT,
  MODIFY counter_evidence        LONGTEXT,
  MODIFY suggested_action        LONGTEXT;
```

> 执行前请对照实体 `DiagnosisResultRecordJpaEntity` / `FindingJpaEntity` 核对列名。

### 2.4 部署顺序

Java 先部署（或同时部署）。Python 先上线也能工作：批量接口不可用时会自动降级为逐条保存，只是拿不到 synthesis 的持久化。

## 3. 上一轮 16 个问题的处理状态

| # | 问题 | 状态 | 说明 |
|---|---|---|---|
| 1 | Docker 内 skills 目录找不到 | ✅ | `SKILLS_DIR` 配置 + Dockerfile `COPY skills` |
| 2 | 没配 key 时静默返回 mock 结果 | ✅ | 仅 `LLM_MOCK=1` 才 mock；无 key 时 job 直接失败并上报 |
| 3 | LLM 无超时 | ✅ | `LLM_TIMEOUT_SECONDS`(60)；provider `max_retries=0`，重试统一交给 harness |
| 4 | token 上限拍脑袋 | ⚠️ 部分 | 默认改为 120000；精确校准需要用真实 key 跑一次消融（见 §4） |
| 5 | 后台任务无队列/无幂等 | ✅ | `JobDispatcher`：有界线程池、按 job_id 去重、队列满返回 429 |
| 6 | agent-service 入站无鉴权 | ✅ | `X-Internal-Api-Key`（hmac 常量时间比较）；Java 端已发送该 header |
| 7 | 工具错误不分类 | ✅ | `FatalToolErrorPlugin`：401/403、熔断、未知工具 → `StopRun`，不再无意义重试 |
| 8 | 文档说 ReAct 但实际是规则 | ✅ | 文档已对齐：专家内 `_reason` 是规则驱动的有界循环，LLM 只在最终诊断调用一次 |
| 9 | 证据截断不可见 | ✅ | `EVIDENCE_TEXT_LIMIT`，payload 带 `truncation` 字段，提示 LLM 证据被截断 |
| 10 | state 过重 | ⏸ 暂缓 | 改 state 结构影响所有节点与 checkpoint 兼容，收益小于风险；先通过截断控制 prompt 体积 |
| 11 | 真实 key 的评测 | ⏸ 需本地 | 云端无真实 key；`test_harness.py` 中的真实 LLM 测试在设置 key 后会自动运行 |
| 12 | Python 解释器装在项目根目录 | ⏸ 需手工 | `.gitignore` 已忽略；请把解释器移出 `E:\video` |
| 13 | 没有 git | ⏸ 需手工 | 已提供根 `.gitignore`，请执行 `git init` |
| 14 | `.env` / 密钥写死在 compose | ✅ | compose 全部改为变量，基础设施端口只绑定 127.0.0.1，提供 `.env.example` |
| 15 | 死代码 | ⏸ 需手工删除 | 见 §5（云端无法删除你机器上的文件） |
| 16 | ruff 不干净 | ✅ | `ruff check src tests` 全部通过 |

另外修复了 Java 侧 `InternalApiAuthFilter` 的密钥比较（改为 `MessageDigest.isEqual` 常量时间比较）。

## 4. token 上限校准方法（#4 / #11）

1. `.env` 配好真实 key，`LLM_MOCK=0`。
2. 跑 10~20 个有代表性的 job（含有参考视频、OCR 文本长的）。
3. 读每次运行审计里的 `tokenUsage`（或 `result.usage`），取 P95 × 1.5 作为 `HARNESS_MAX_TOKENS`。

## 5. 需要手工处理的事项

- 删除已不再使用的旧文件：`observability/trace.py`、`observability/tracing.py`、`graph/nodes/reasoner.py`、`tool_router.py`、`tools/adapters/resilience.py`，以及根目录下的 `hs_err_*.log`。
- 改动前的原始文件备份在 `E:\video\_backup_before_orchestration_refactor\`。
- 本地验证：`cd backend && mvn test`（云端无法访问 Maven Central，Java 仅做过 javac 类型检查）；`cd agent-service && pytest`。
