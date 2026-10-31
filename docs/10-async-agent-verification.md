# Agent 异步诊断本地验证

## 阶段 3：docker compose 完整链路

```bash
# 构建启动全部服务
docker compose up -d --build

# 1. 健康检查 agent
curl http://localhost:8090/api/v1/agent/health

# 2. 上传视频（如已有 videoId 可跳过）
curl -X POST http://localhost:8080/api/v1/videos/upload \
  -F "file=@/path/to/video.mp4"

# 3. 调用 Java 对外接口，触发诊断任务（前端只感知 Java）
curl -X POST http://localhost:8080/api/v1/analysis/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "targetVideoId": "<target-video-id>",
    "referenceVideoIds": ["<ref-video-id>"],
    "targetTitle": "demo",
    "targetDescription": "demo",
    "referenceTitles": ["ref"],
    "referenceDescriptions": ["ref"],
    "enableCoverAnalysis": true,
    "enablePerformanceAnalysis": true
  }'

# 4. 轮询查询任务结果（Java 查 MySQL 返回，前端不知道 agent-service）
curl http://localhost:8080/api/v1/analysis/jobs/<jobId>/result
```

## 异步链路说明

```
POST /api/v1/analysis/jobs
  → CreateAnalysisJobCase（PENDING 落库）
  → StartAgentDiagnosisCase（RUNNING 落库）
  → AgentServiceHttpClient.submitJobAsync（不等待）
  → 立即返回 jobId

POST agent-service /api/v1/agent/jobs/submit（202）
  → BackgroundTasks → HarnessRunner.run()
  → LangGraph 推理 + tools 调 Java /internal/**
  → 成功：POST /internal/.../agent-results {status:SUCCESS}
  → 失败：POST /internal/.../agent-results {status:FAILED, errorMessage}

GET /api/v1/analysis/jobs/{id}/result
  → BuildResultCase 读 MySQL 返回
```

## 阶段 4：边界加固清单

- [x] Java `/internal/**`：`InternalApiAuthFilter` + `X-Internal-Api-Key`
- [x] agent-service：trace_id 审计日志，工具调用完整记录
- [x] Harness：`max_turns` / `max_graph_steps` / `timeout` 护栏
- [x] HTTP 客户端：重试 + 熔断（`tools/adapters/http_client.py`）
- [x] docker-compose：`agent-service` 使用 `restart: on-failure`
- [x] Java 超时守护：`AnalysisJobTimeoutGuardian` 扫描 RUNNING 超时任务
