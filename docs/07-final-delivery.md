# 最终交付清单

## 1. 项目结论

这套短视频对比诊断 MVP 已经打通了主链路，可以完成：

- 视频上传
- 自动抽帧
- 自动 ASR
- 分析任务创建
- 任务状态查询
- 任务结果查询
- 核心三维度收口
- 结果建议卡片
- 幂等与重试
- 基础持久化

## 2. 已完成的功能

1. 视频上传
2. 自动抽帧
3. ASR 转写
4. 分析任务创建
5. 任务状态查询
6. 任务结果查询
7. 核心三维度收口
8. 结果建议卡片
9. 数据库表和持久化收口
10. 幂等、重试和异常收口

## 3. 可直接调用的接口

- `POST /api/v1/videos/upload`
- `POST /api/v1/videos`
- `GET /api/v1/videos/{videoId}`
- `GET /api/v1/videos/{videoId}/features`
- `GET /api/v1/videos/{videoId}/asr`
- `POST /api/v1/analysis/jobs`
- `GET /api/v1/analysis/jobs/{jobId}`
- `GET /api/v1/analysis/jobs/{jobId}/result`
- `GET /api/v1/health`

## 4. 数据库表

- `video_asset`
- `analysis_job`
- `video_feature`
- `finding`
- `coverage_state`
- `skill_definition`

## 5. 代码结构

### 后端主目录

- `backend/src/main/java/com/videodiagnosis/interface`
- `backend/src/main/java/com/videodiagnosis/application`
- `backend/src/main/java/com/videodiagnosis/domain`
- `backend/src/main/java/com/videodiagnosis/infrastructure`
- `backend/src/main/java/com/videodiagnosis/types`

### 静态前端

- `backend/src/main/resources/static/index.html`

## 6. 启动方式

### 方式一：本机启动

1. 启动 MySQL、Redis、MinIO
2. 启动后端
3. 打开 `http://localhost:8080/index.html`

### 方式二：Docker 启动

1. 执行 `docker compose up -d --build`
2. 打开 `http://localhost:8080/index.html`

## 7. 当前 MVP 边界

- 只做 3 个核心维度：
  - `HOOK`
  - `STRUCTURE_RHYTHM`
  - `VALUE_DELIVERY`
- 不做复杂模型训练
- 不做平台抓取
- 不做全量可视化工作台

## 8. 下一步建议

1. 接入真实 FFmpeg 抽帧
2. 接入真实 ASR 服务
3. 把分析规则逐步细化
4. 补一版简单任务列表页
