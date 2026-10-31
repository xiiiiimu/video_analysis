# Harness 改造说明（参考 Strands Agents）

本次改造把 `agent-service/src/agent_service/harness` 从“包在 LangGraph 外面的一组工具类”改成了
“运行时（机制）+ 插件（策略）+ 组装层”三层结构。外部契约不变：Java 回调格式、`/internal/**` 接口、
LangGraph 外层流程、Skill 快照、Supervisor / handoff 都没有改。

## 1. 分层

```
services/harness_setup.py      组合根：诊断服务用哪张图、哪些业务规则
        │
harness/factory.py             组装层：解析 → 组装 → 构造（build_harness）
harness/defaults.py            默认限额、默认插件
        │
harness/runner.py              运行时：run 生命周期 + 三个统一入口
harness/events.py / hooks.py   生命周期事件 + Hook 注册表
        │
harness/plugins/*              策略：审计、限额/取消、模型重试
harness/interventions.py       决策型策略：Proceed / Deny / Guide / Transform
```

harness 目录下不再导入任何 `graph` / `skills` 业务模块；业务规则放在 `graph/policies.py`，
初始 state 放在 `graph/initial_state.py`，由 `DiagnosisGraph.initial_state()` 提供给 harness。

## 2. 三个统一入口

| 入口 | 谁调用 | 发出的事件 | 计数 |
|---|---|---|---|
| `run_node` | `graph/builder.py` 用 `harness_node()` 自动包装每个节点 | BeforeNode / AfterNode | 图步数 |
| `call_tool` | ReAct 循环、tool_executor、synthesizer | BeforeToolCall / AfterToolCall | 轮次 |
| `call_model` | `llm/diagnosis_llm.py` 通过 `harness.context.call_model` | BeforeModelCall / AfterModelCall | 模型调用次数、token |

另有 `call_infra`：进度上报这类流程副作用，不计预算，只发 `InfraCallEvent` 供审计。

## 3. 事件与可写字段

| 事件 | 可写字段 | 作用 |
|---|---|---|
| BeforeToolCall | `cancel_tool`、`tool_args` | 取消工具调用 / 修改参数 |
| AfterToolCall | `result`、`retry` | 改写结果 / 重试工具 |
| BeforeModelCall | `cancel`、`messages` | 取消模型调用 / 追加消息 |
| AfterModelCall | `retry`、`messages` | 重试模型（可带反馈） |

其它字段只读，写了会直接报 `AttributeError`。After 类事件的回调反向执行（洋葱模型）。

## 4. 默认插件

| 插件 | 做什么 |
|---|---|
| `audit` | 订阅所有事件，单行 JSON 审计日志的唯一出口（事件名与 docs/12 保持一致，新增 model_call_* / infra_call / intervention_applied） |
| `limits` | 节点前检查图步数、工具前检查轮次、模型前检查 token；超出或超时时 `ctx.request_stop()` 并抛 `StopRun` |
| `model-retry` | 限流 / 超时 / 5xx 时指数退避重试模型调用 |
| `interventions` | 内置 `OutputFormatGuard`（JSON 不合法时带反馈重试，最多 2 次），诊断服务额外挂 `SpecialistToolPolicy`、`JobIdPinning` |

`build_harness(..., builtin_plugins=["limits"])` 可以按名字关掉内置插件，方便做消融实验。

## 5. 停止原因

`HarnessRunResult` 新增 `stop_reason` 和 `usage`，`status` 保持原有取值：

| stop_reason | status | 说明 |
|---|---|---|
| completed | success | 正常结束 |
| cancelled | timeout | 超时（定时器设置取消信号，各检查点退出） |
| limit_turns / limit_tokens / limit_steps | guardrail_blocked | 预算用完 |
| error | failed | 意外异常（日志里有完整堆栈） |

预算用完和超时时，`output` 是最后一个完整节点之后的 state，不再是空 dict。
`StopRun` 继承 `BaseException`，业务代码里的 `except Exception` 拦不住它。

## 6. 修掉的问题

1. 超时永远不触发（旧 `time_limit` 提交的是 `lambda: None`）。
2. token 上限无效（`token_usage` 从未累加）。
3. 审计事件重复输出（实时一次 + 结束时 flush 一次）。
4. 3 个 Specialist 并行时计数没有加锁。
5. 进度上报走 `call_tool`，每次都消耗轮次和图步数。
6. 节点要手动调用 `on_graph_step`，漏调就不准。
7. `http_client` ↔ `java_result` 循环导入：任何 import `job_runner` / `api.routes` 的地方都会报 ImportError（HTTP 服务无法启动）。
8. POST（保存假设）在超时 / 5xx 时会重试，可能写入重复数据；现在只在连接失败时重试。
9. 熔断器每个 job 新建一次，实际永远不会打开；现在按 base_url 进程级共享，4xx 不计入。
10. 一个依赖线程调度顺序的测试（`test_evaluator_retry_reuses_prior_knowledge_observations_under_turn_budget`）改为比较集合。

## 7. 删除的文件

`harness/guardrails.py`、`harness/limits.py`、`harness/memory.py`（从未被使用）、`harness/tool_interceptor.py`、
`tools/adapters/resilience.py`（未被使用的重复实现）。其职责已分别迁移到 `plugins/limits.py`、
`interventions.py`、`graph/policies.py`。

## 8. 写一个新插件

```python
from agent_service.harness import Plugin, hook
from agent_service.harness.events import AfterToolCallEvent


class SlowToolAlert(Plugin):
  name = "slow-tool-alert"

  @hook
  def check(self, event: AfterToolCallEvent) -> None:
    ...  # 运行期状态放 event.ctx.plugin_state，不要放 self


harness = create_diagnosis_harness(tools, plugins=[SlowToolAlert()])
```

需要“放行 / 拒绝 / 引导 / 改写”这类决策时，写 `InterventionHandler` 而不是直接改事件，
多个规则的结论会被统一仲裁（Deny 短路、Guide 合并）。
