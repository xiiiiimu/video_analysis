# 18. Java 可靠性修复 + 全链路 traceId

按"并发 / 幂等 / 事务 / 容错 / 异步可靠性 / 可观测性"逐项核对后端代码，发现并修复以下问题。每个修复都有回归测试。

## 1. `@Transactional` 同类自调用失效（派发 / 超时回收）

**问题**：`DispatchAgentCase.dispatchReadyJobs()` 直接调用本类的 `dispatchOne()`，`RecoverTimedOutJobCase` 同理。
Spring 事务靠代理实现，同类调用不经过代理，注解根本不生效。凑巧的是，正因为不生效，"先提交 AGENT_RUNNING 再发 HTTP"的顺序反而对；
如果注解真生效，HTTP 调用会被包进事务，agent-service 慢的时候长时间占着数据库连接。

**修复**：删掉误导性的注解，把派发明确拆成三步，每步各是一次短事务（`repository.save` 自带事务，任务表 `@Version` 乐观锁）：

1. 抢占：WAITING_AGENT / RETRYING → AGENT_RUNNING，立即提交；
2. 事务外发 HTTP；
3. 只有失败才回写 RETRYING / FAILED。

**顺带修掉的 3 个连带问题**：

| 场景 | 原来 | 现在 | 测试 |
|---|---|---|---|
| 扫描到之后任务已被别的实例抢走（状态已变） | 状态机异常被当成"派发失败"，把别人的任务改成 RETRYING | 跳过，不发请求、不改任务 | ⑱ |
| HTTP 失败（如读超时）但 Agent 已收到并回调成功 | 对 COMPLETED 任务调 retry() 抛异常 | 只有仍是 AGENT_RUNNING 且 agentRunId 没变才回写 | ⑰ |
| 超时扫描到之后回调先完成了任务 | 抛状态机异常，整批扫描在这一条中断 | 跳过这一条 | ⑲ |

## 2. Redis 去重标记早于数据库提交

**问题**：回调处理在事务里先写 Redis "已处理"。如果之后数据库提交失败，agent-service 重发回调会被 Redis 判成重复直接丢弃，结果丢失。
另外 `HandleAgentResultCase` 只有 7 参数的 `execute` 标了 `@Transactional`，另外两个重载通过 `this` 调用，同样没有事务。
Redis 不可用时的本机兜底是一个永不清理的 Set，进程跑得越久越大。

**修复**：
- Redis 标记改到事务提交之后（`TransactionSynchronization.afterCommit`），回滚不标记；
- `@Transactional` 挪到类上；
- 本机兜底改为带过期时间（6 小时）和条数上限（1 万）的缓存。它只是快速路径，漏判会落到回调记录表 (agent_run_id, result_version) 唯一索引上，不会重复处理。

测试：`RedisIdempotencyRepositoryTest`（提交后才标记、回滚不标记、无事务立即标记、条数上限、过期）。

## 3. 并发重复建任务返回 500

**问题**：建任务先按 job_key 查、查不到再插入，不是原子操作。两个相同请求（重复点击、网关重试）同时到达时，唯一索引只放进一个，另一个直接 500。

**修复**：捕获 `DataIntegrityViolationException` 后回查并返回已存在的任务，两次请求拿到同一个 jobId；回查仍查不到（别的约束冲突）则原样抛出，不吞异常。

测试：`CreateAnalysisJobCaseTest`。

## 4. 全链路 traceId（Java ↔ Python）

**原来**：响应里的 traceId 每次随机生成，只有异常处理器会打出来；Java 和 Python 的日志无法关联。

**现在**：
- Java：`TraceIdFilter`（最先执行）读取 `X-Trace-Id` 请求头，没有或不合法就新生成，写入 MDC（`traceId` + 路径里的 `jobId`），回写响应头；`Result.traceId` 取同一个值。日志格式 `[trace=... job=...]`。
- 一次派发就是一条链路，**traceId = agentRunId**：Java 派发请求头带它，Python 绑定到 ContextVar，每行日志（文本和 JSON 格式）都带 `trace_id` / `job_id`；三个专家在线程池里并行，用 `run_with_trace` 显式带进子线程（执行完恢复原值，避免线程复用串值）；回调 Java 时请求头带回同一个值。
- 外部传入的 traceId 只接受 `[A-Za-z0-9_.:-]{1,64}`，防止通过请求头往日志里注入换行伪造日志行。

测试：Java ⑮（派发请求头 = agentRunId、MDC 已清理）、⑯（回调沿用 traceId、非法值被替换）；Python `test_trace_context.py`（日志字段、线程池传递、不带包装时确实传不过去）。

**真实任务验证**（2026-10-29，89 秒视频 + 4 条用户标准，deepseek-flash）：
`docker compose logs app agent-service | Select-String <agentRunId>` 一条命令拿到两个服务的完整链路：
Java 派发 → Python 接收 → 解析标准 → 三个专家并行检索评分点 + 调模型 → Evaluator → Synthesizer → 写回结果 → 回调。
Agent 阶段约 27 秒，4 次模型调用，50,626 token（输入 38,105 / 输出 12,521）。

## 测试数

Java 34 个：集成测试 19 个（新增 ⑮~⑲）、`RedisIdempotencyRepositoryTest` 5、`CreateAnalysisJobCaseTest` 2、状态机 3、抽帧计划 3、标准文件上传 2。
Python 228 个。

## 仍然没做的（被问到时如实说）

- 派发扫描没有 worker 租约 / `SELECT ... FOR UPDATE SKIP LOCKED`，多实例时靠乐观锁抢占（输的一方跳过）+ 回调幂等兜底；
- 没有 MQ / Outbox，派发是数据库轮询；
- 没有熔断、限流（只有一个下游，靠超时 + 有上限的退避重试 + 超时回收）；
- 没有用户体系，公开接口没有做越权校验（`ownerId` 字段预留）；
- 没有指标和告警（只开了 actuator health）。
