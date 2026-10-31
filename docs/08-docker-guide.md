# Docker 联调说明

## 1. 组件说明

`docker-compose.yml` 会同时启动：

- MySQL
- Redis
- MinIO
- 后端服务
- 后端镜像内置 FFmpeg，用于真实抽帧
- 后端镜像内置 Tesseract OCR，用于识别关键帧里的画面文字

## 2. 一键启动

在 `E:\video` 目录下执行：

```bash
docker compose up -d --build
```

## 3. 启动后访问

- 后端：`http://localhost:8080`
- 前端页：`http://localhost:8080/index.html`
- 健康检查：`http://localhost:8080/api/v1/health`
- MinIO 控制台：`http://localhost:9001`

## 4. 本地联调顺序

1. 先看 `http://localhost:8080/index.html`
2. 上传一个视频
3. 复制返回的 `videoId`
4. 创建分析任务
5. 查询任务状态
6. 查询任务结果

## 5. 常见问题

### 5.1 后端起不来

先确认：

- `3306` 没被别的 MySQL 占用
- `9000` 和 `9001` 没被别的服务占用
- Docker 已经启动
- 如果是本机运行后端，不走 Docker，需要本机能执行 `ffmpeg`、`ffprobe` 和 `tesseract`

### 5.2 页面访问不到接口

默认前端页会使用当前页面同源地址。
如果你不是通过 `http://localhost:8080/index.html` 打开页面，可以手动把后端地址改成：

```text
http://localhost:8080
```

### 5.3 MinIO 资源地址不可访问

确认 MinIO 已启动，并且后端上传配置仍然指向：

- `http://localhost:9000`

## 6. 联调建议

如果你想快速验证主链路，按这个顺序最稳：

1. 上传一个 target 视频
2. 上传一个 reference 视频
3. 创建分析任务
4. 看任务状态从 `PENDING` 走到 `COMPLETED`
5. 看结果页里的 `summary` 和 `recommendations`

## 7. FFmpeg 抽帧说明

当前版本会从 MinIO 下载视频到临时目录，调用 `ffmpeg` 抽出 JPEG 关键帧，再上传回 MinIO。

默认配置：

- 抽帧数量：`5`
- 抽帧间隔：`3` 秒
- 配置项：`app.media.keyframe-count`
- 配置项：`app.media.keyframe-interval-seconds`

## 8. OCR 文字识别说明

当前版本不接真实 ASR，也不会识别视频里的语音。系统会对视频关键帧做 OCR，识别画面中可见的标题、字幕、商品文案、按钮文字等内容，并写入 `ocrJson`。

默认配置：

- OCR 开关：`app.media.ocr-enabled`
- OCR 帧数量：`app.media.ocr-frame-count`
- OCR 帧间隔：`app.media.ocr-frame-interval-seconds`
- OCR 命令路径：`app.media.tesseract-path`
- OCR 语言包：`app.media.tesseract-languages`
