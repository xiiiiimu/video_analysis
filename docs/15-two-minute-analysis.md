# 15. 分析窗口扩展到 2 分钟 + 语音转写

改造前系统实际只"看"视频前 15 秒的屏幕文字：关键帧 5 张 × 3 秒、OCR 5 帧 × 3 秒，
语音转写是空实现，场景切分写死为 0~5 秒，LLM 收到的关键帧只是 URL。本次把预处理和证据链路
扩展到前 120 秒，并接入 OpenAI 转写接口。

## 1. 预处理（Java，featureVersion 0.2.0）

`VideoFeatureExtractor` 编排，一个视频只下载一次（旧版同一视频下载 4 次）：

1. `ffprobe`：时长、分辨率、是否有音轨；
2. 场景检测：`ffmpeg ... select='gt(scene,0.3)',showinfo`，缩到 320 宽打分；
3. 采样计划 `FrameSamplingPlan`（纯函数，有单测）：
   - 开场 0~5 秒每秒 1 帧（reason=hook）
   - 之后每 3 秒 1 帧（interval）
   - 镜头切换后 0.3 秒补帧（scene，离已有采样点 ≥1 秒才补）
   - 窗口末尾 1 帧（end）
   - 单视频上限 60 帧；超限时保留全部 hook / end，其余均匀抽稀
4. 并行（默认 4 路）抽帧 + tesseract OCR，同一帧既上传 MinIO 作为关键帧也用于 OCR；
5. 转写：`ffmpeg` 抽单声道 16kHz mp3（2 分钟约 0.5MB）→ `/audio/transcriptions`。

产出字段：

| 字段 | 内容 |
|---|---|
| `keyframes` | 关键帧 URL（按时间排序，兼容旧消费者） |
| `sceneJson` | 真实镜头切分：`scenes[{index,start,end,durationSeconds}]`、`sceneCount`、`avgSceneSeconds` |
| `ocrJson` | `ocr[{time,end,timeRange,startSeconds,endSeconds,text}]`，连续相同字幕合并为一段；时间戳修正为 HH:MM:SS（旧版超过 60 秒会出现 `00:00:63`） |
| `transcriptText` | 转写全文 |
| `timelineJson`（新） | `durationSeconds / analyzedSeconds / truncated`、关键帧时间点与 reason、转写分段与 `status` |

转写失败不会让预处理失败，`timeline.transcript.status` 如实标记：`ok / disabled（没配 key）/ no_audio / failed`。

**顺带修复的 bug**：Agent 链路的特征是在上传视频时提取的（`jobId=AUTO_FRAME`），而 `GetJobEvidenceCase`
只按任务 ID 查特征，所以 agent 实际拿到的一直是空证据。现在按任务查不到时按视频 ID 回退。
旧版本（0.1.0）的特征在下次提取时会自动重新提取。

## 2. 语音转写配置

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `ASR_API_KEY` | 依次回退到 `OPENAI_API_KEY`、`CHAT_API_KEY` | 为空则跳过转写；CHAT 用 DeepSeek 时必须单独填 |
| `ASR_BASE_URL` | `https://api.openai.com/v1` | 任何 OpenAI 兼容的转写服务 |
| `ASR_MODEL` | `whisper-1` | 见下方说明 |
| `ASR_LANGUAGE` | 空（自动识别） | 如 `zh` |

`mode=auto`：whisper 系列用 `verbose_json` 一次拿到分段时间戳；其它模型按 15 秒切片分别转写（chunked），
时间戳精度为切片长度。

> OpenAI 文档标注 `whisper-1` 等转写模型将于 **2027-02-26** 下线，推荐的 `gpt-transcribe` 不返回分段时间戳。
> 届时把 `ASR_MODEL` 改为 `gpt-transcribe`，系统会自动切到 chunked 模式，无需改代码。

## 3. Agent 证据视图（Python）

`graph/evidence_timeline.py` 把时间轴整理成紧凑视图发给模型（不再发关键帧 URL，模型看不到图片）：

```json
{
  "alias": "T",
  "coverage": {"durationSeconds": 150, "analyzedSeconds": 120, "truncated": true, "window": null},
  "keyframeTimes": [{"time": "00:00:00", "reason": "hook"}, ...],
  "scenes": [{"n": 1, "t": "00:00:00-00:00:07", "sec": 7.4}, ...],
  "screenText": [{"t": "00:00:00-00:00:03", "text": "..."}, ...],
  "speech": [{"t": "00:00:01-00:00:04", "text": "..."}, ...],
  "speechStatus": "ok"
}
```

- HOOK 只给前 15 秒（`HOOK_WINDOW_SECONDS`），STRUCTURE_RHYTHM / VALUE_DELIVERY 给完整窗口；
- 上限：每视频关键帧 60、每类分段 60、单段 200 字（`EVIDENCE_MAX_*`），截断写入 `truncation`；
- 旧数据（没有 `timelineJson`）走原来的 legacy 视图。

**引用格式**（T=目标，R1/R2=参考）：`FRAME:T@00:01:03`、`OCR:T@00:00:06`、`ASR:T@00:00:12`、`SCENE:T#3`，
视频级 `ASR:<videoAssetId>` 等仍然有效。时间级引用严格校验：FRAME 需与某关键帧相差 ≤1.5 秒，
OCR / ASR 需落在某个分段内，SCENE 序号需存在；不再走宽松子串匹配（否则 `FRAME:T@00:05:00` 会因包含 `FRAME:T` 被放行）。

另修复：`{"ocr":[]}` 这种空 OCR 结果过去被当成"有文字证据"，现在 `has_text_evidence` 会解析内容判断。

## 4. 成本与耗时（估算）

| 项 | 2 分钟视频 |
|---|---|
| 抽帧 | 约 45 帧，约 4MB 存储 |
| OCR | CPU 每帧 1~2 秒，4 路并行约 20~40 秒 |
| 转写 | whisper-1 约 $0.012 |
| 单次诊断输入 | 约 8~10k token（目标 + 2 个参考） |
| 单任务 token 上限 | `HARNESS_MAX_TOKENS` 默认调到 200000 |

上传接口是同步提取特征的，2 分钟视频上传请求会多等约 1 分钟。

## 5. 升级注意

- 旧版本的特征不会自动迁移：已上传的视频在下次触发提取时重新提取；测试环境可直接 `docker compose down -v` 后重新上传。
- 数据库新增 `video_feature.timeline_json`（LONGTEXT），`ddl-auto=update` 会自动加列。
- 证据格式与引用格式变化后，新旧诊断结果不宜直接对比；消融评测和 token 校准请在本次改造后重新跑。
