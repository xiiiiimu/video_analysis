# Agent 诊断业务实现说明

## 1. LangGraph 诊断流程

```
plan → tools(fetch_context) → tools(fetch_evidence)
     → diagnose(HOOK) → diagnose(STRUCTURE_RHYTHM) → diagnose(VALUE_DELIVERY)
     → tools(save_hypotheses) → END
```

| 节点 | 职责 |
|------|------|
| `planner.py` | 规划三核心维度，写 `pending_dimensions` 草稿 |
| `tool_executor.py` | 调度 Java 工具：上下文 / 证据 / 保存假设 |
| `diagnose.py` | 按维度调用 LLM（或 mock），写 `draft_hypotheses` 草稿 |

**State 约束**：仅存 `draft_hypotheses`、`evidence_pack` 引用片段，不存 Finding 实体。

## 2. Prompt 模板

路径：`llm/prompts/diagnosis.py`

- `PLANNER_SYSTEM_PROMPT`：规划器
- `DIMENSION_DIAGNOSIS_SYSTEM_PROMPT`：分维度对比诊断（HOOK / 结构节奏 / 价值传递）

LLM 调用封装：`llm/diagnosis_llm.py`（无 `OPENAI_API_KEY` 时自动 mock）

## 3. Tools / Adapters

| 工具名 | Adapter | Java 内部接口 |
|--------|---------|---------------|
| `get_job_context` | `analysis_job.py` | `GET /internal/v1/analysis/jobs/{id}/context` |
| `get_video_evidence` | `video_evidence.py` | `GET /internal/v1/analysis/jobs/{id}/evidence` |
| `save_diagnosis_hypothesis` | `hypothesis.py` | `POST /internal/v1/analysis/jobs/{id}/hypotheses` |
| `save_agent_draft_result` | `analysis_job.py` | `POST /internal/v1/analysis/jobs/{id}/agent-results` |

`http_client.py`：重试 + 熔断 + `Result<T>` 解包。

## 4. Harness 审计日志

`harness/audit.py` 输出单行 JSON：

```json
{"audit":true,"event":"tool_call_started","trace_id":"...","task_id":"...","job_id":"...","timestamp":"..."}
```

对接方式：

- 设置 `AGENT_JSON_LOGS=1` 启用全局 JSON 日志（`observability/logging_setup.py`）
- 日志系统按 `audit=true` 过滤审计事件
- `X-Trace-Id` 与 Java / agent 全链路对齐

审计事件类型：

- `harness_started` / `harness_finished` / `harness_failed` / `harness_timeout` / `harness_guardrail_blocked`
- `graph_step`
- `tool_call_started` / `tool_call_finished` / `tool_call_error`
- HarnessContext 累积事件通过 `flush_context_events` 批量输出

## 5. Java 新增内部接口（application 层转发，domain 无 Agent 依赖）

- `GetJobEvidenceCase` → 返回关键帧、转写、场景/OCR
- `SaveAgentHypothesisCase` → 映射为 Finding 落库
