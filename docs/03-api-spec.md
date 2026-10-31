# 短视频对比诊断 MVP 接口文档

## 1. 约定

- 所有接口返回统一 JSON
- 异步任务通过 `jobId` 查询
- 上传文件可直接走对象存储，接口只负责登记

统一响应格式：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "traceId": "xxx"
}
```

## 2. 接口分组

按 DDD 和常见分层习惯，接口层建议按用例分组，而不是按数据库表分组。

- `AnalysisCommandController`
- `AnalysisQueryController`
- `VideoCommandController`
- `HealthQueryController`

## 3. Command 接口

### 3.1 创建分析任务

`POST /api/v1/analysis/jobs`

用途：
- 创建一次短视频对比诊断任务
- 同一组输入重复提交时，会返回同一个任务，不会重复创建

请求示例：

```json
{
  "targetVideoId": "vid_target_001",
  "referenceVideoIds": ["vid_ref_001", "vid_ref_002"],
  "targetTitle": "xxx",
  "targetDescription": "xxx",
  "referenceTitles": ["xxx", "xxx"],
  "referenceDescriptions": ["xxx", "xxx"],
  "options": {
    "enableCoverAnalysis": true,
    "enablePerformanceAnalysis": false
  }
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "jobId": "job_001",
    "status": "PENDING"
  },
  "error": null,
  "traceId": "trace_001"
}
```

### 3.2 注册视频资产

`POST /api/v1/videos`

用途：
- 登记一个视频资产

请求示例：

```json
{
  "role": "target",
  "fileUrl": "s3://bucket/target.mp4",
  "title": "xxx",
  "description": "xxx",
  "coverUrl": "s3://bucket/cover.jpg"
}
```

### 3.3 上传视频并自动抽帧

`POST /api/v1/videos/upload`

用途：
- 直接上传视频到对象存储
- 上传完成后自动抽帧并落库

请求方式：
- `multipart/form-data`

字段：
- `file`：视频文件
- `role`：`target` 或 `reference`
- `title`：可选
- `description`：可选
- `coverUrl`：可选

返回示例：

```json
{
  "success": true,
  "data": {
    "videoId": "vid_001",
    "objectName": "videos/target/xxx.mp4",
    "fileUrl": "http://localhost:9000/video-assets/videos/target/xxx.mp4",
    "title": "xxx",
    "status": "PROCESSED"
  },
  "error": null,
  "traceId": "trace_004"
}
```

## 4. Query 接口

### 4.1 查询任务状态

`GET /api/v1/analysis/jobs/{jobId}`

返回示例：

```json
{
  "success": true,
  "data": {
    "jobId": "job_001",
    "status": "ANALYZING",
    "progress": 62,
    "currentStage": "ASR",
    "errorMessage": null,
    "startedAt": "2026-08-29T12:00:00",
    "finishedAt": null
  },
  "error": null,
  "traceId": "trace_002"
}
```

### 4.2 查询任务结果

`GET /api/v1/analysis/jobs/{jobId}/result`

用途：
- 查看一次分析任务的最终结果
- 包含核心发现、覆盖情况、缺失输入和修改建议
- 当前 MVP 只输出 3 个核心维度：
  - `HOOK`
  - `STRUCTURE_RHYTHM`
  - `VALUE_DELIVERY`

返回示例：

```json
{
  "success": true,
  "data": {
    "jobId": "job_001",
    "status": "COMPLETED",
    "coreDimensions": ["HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY"],
    "summary": [
      {
        "dimension": "hook",
        "priority": "P0",
        "observation": "Target 开场 10 秒后才出现核心信息",
        "evidence": {
          "target": ["00:00:10-00:00:14"],
          "reference": ["00:00:03-00:00:06"]
        },
        "suggestedAction": "把结果前置到 5 秒内"
      }
    ],
    "recommendations": [
      {
        "dimension": "HOOK",
        "priority": "P0",
        "title": "Target 开场 10 秒后才出现核心信息",
        "action": "把最强信息前置到前 5 秒内",
        "confidence": 0.86
      }
    ],
    "coverageStates": [
      {
        "dimension": "HOOK",
        "state": "checked",
        "reason": "MVP core dimension covered"
      }
    ],
    "missingInputs": [],
    "revisionPlan": [
      "HOOK: Move the strongest information earlier."
    ]
  },
  "error": null,
  "traceId": "trace_003"
}
```

### 4.3 查询视频详情

`GET /api/v1/videos/{videoId}`

用途：
- 查看视频元数据和处理状态

### 4.4 查询视频抽帧结果

`GET /api/v1/videos/{videoId}/features`

用途：
- 查看自动抽帧结果
- 前端可直接用来展示关键帧预览

返回示例：

```json
{
  "success": true,
  "data": {
    "videoId": "vid_001",
    "featureId": "feature_001",
    "featureVersion": "0.1.0",
    "keyframeCount": 3,
    "keyframes": ["00:00:01-00:00:02", "00:00:05-00:00:06"],
    "sceneJson": "{\"scenes\":[{\"start\":\"00:00:00\",\"end\":\"00:00:05\"}]}",
    "ocrJson": "{\"ocr\":[]}",
    "transcriptText": "Transcript xxx xxx file.mp4 Start with the main point early and keep value explicit.",
    "transcriptLength": 84,
    "status": "EXTRACTED",
    "createdAt": "2026-08-28T12:00:00"
  },
  "error": null,
  "traceId": "trace_005"
}
```

### 4.5 查询视频 ASR

`GET /api/v1/videos/{videoId}/asr`

用途：
- 查看自动转写文本
- 前端可直接展示字幕和文案草稿

返回示例：

```json
{
  "success": true,
  "data": {
    "videoId": "vid_001",
    "featureId": "feature_001",
    "transcriptText": "Transcript xxx xxx file.mp4 Start with the main point early and keep value explicit.",
    "transcriptLength": 84,
    "wordCount": 12,
    "status": "TRANSCRIBED",
    "createdAt": "2026-08-28T12:00:00"
  },
  "error": null,
  "traceId": "trace_006"
}
```

### 4.6 健康检查

`GET /api/v1/health`

用途：
- 检查服务可用性

## 5. 状态枚举

### 5.1 任务状态
- `PENDING`
- `PREPROCESSING`
- `ANALYZING`
- `COMPLETED`
- `FAILED`

### 5.2 视频状态
- `UPLOADING`
- `READY`
- `PROCESSING`
- `PROCESSED`
- `FAILED`

## 6. 错误码建议

- `40001` 参数缺失
- `40002` 视频不存在
- `40003` 参考视频不足
- `50001` 预处理失败
- `50002` ASR 失败
- `50003` 模型调用失败
- `50004` 结果解析失败

## 7. 接口原则

- 所有耗时操作异步化
- 所有请求都要有 `traceId`
- 创建任务接口必须幂等
- 结果接口可重复查询
- 内部失败会自动重试 3 次
- 参数错误和内部错误会分别返回不同的 HTTP 状态

## 8. 和 DDD 的对应关系

- Command 接口负责写操作入口
- Query 接口负责读操作入口
- 接口层只做协议转换，不做领域判断
