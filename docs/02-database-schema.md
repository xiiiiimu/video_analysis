# 短视频对比诊断 MVP 数据库表设计

## 1. 设计目标

- 支持上传视频
- 支持异步任务
- 支持任务状态流转
- 支持多视频对比
- 支持证据回指
- 支持版本快照

## 2. 领域对象到表的映射

- `VideoAsset` -> `video_asset`
- `AnalysisJob` -> `analysis_job`
- `VideoFeature` -> `video_feature`
- `SkillDefinition` -> `skill_definition`
- `SkillRun` -> `skill_run`
- `Finding` -> `finding`
- `CoverageState` -> `coverage_state`

## 3. 核心表

### 3.1 `video_asset`
存视频原始信息。

字段建议：
- `id`
- `owner_id`
- `role`，取值 `target` / `reference`
- `title`
- `description`
- `cover_url`
- `file_url`
- `file_size`
- `duration_ms`
- `mime_type`
- `status`
- `created_at`
- `updated_at`

### 3.2 `analysis_job`
一次分析任务。

字段建议：
- `id`
- `job_key`
- `target_video_id`
- `status`
- `input_snapshot_json`
- `skill_version_snapshot_json`
- `progress`
- `error_code`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`
- `updated_at`

### 3.3 `video_feature`
每个视频的预处理结果。

字段建议：
- `id`
- `video_asset_id`
- `transcript_text`
- `transcript_json`
- `keyframe_json`
- `scene_json`
- `ocr_json`
- `metadata_json`
- `feature_version`
- `created_at`
- `updated_at`

### 3.4 `skill_definition`
技能定义。

字段建议：
- `id`
- `skill_key`
- `version`
- `name`
- `coverage_dimension`
- `tool_allowlist_json`
- `rubric_json`
- `output_schema_json`
- `budget_json`
- `enabled`
- `created_at`
- `updated_at`

### 3.5 `skill_run`
一次技能执行记录。

字段建议：
- `id`
- `job_id`
- `skill_definition_id`
- `status`
- `input_snapshot_json`
- `output_json`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`
- `updated_at`

### 3.6 `finding`
最终输出的诊断结论。

字段建议：
- `id`
- `job_id`
- `dimension`
- `priority`
- `status`
- `observation`
- `target_evidence_json`
- `reference_evidence_json`
- `difference_text`
- `hypothesis`
- `confidence`
- `source`
- `counter_evidence`
- `suggested_action`
- `created_at`
- `updated_at`

### 3.7 `coverage_state`
覆盖率状态。

字段建议：
- `id`
- `job_id`
- `dimension`
- `state`，取值 `checked` / `missing` / `unchecked`
- `reason`
- `created_at`
- `updated_at`

## 4. 辅助表

### 4.1 `tool_execution`
工具调用日志。

字段建议：
- `id`
- `job_id`
- `skill_run_id`
- `tool_name`
- `status`
- `input_json`
- `output_json`
- `error_message`
- `started_at`
- `finished_at`

### 4.2 `job_event`
任务事件流。

字段建议：
- `id`
- `job_id`
- `event_type`
- `event_payload_json`
- `created_at`

## 5. 索引建议

- `analysis_job.job_key` 唯一索引
- `analysis_job.status` 普通索引
- `analysis_job.target_video_id` 普通索引
- `video_asset.owner_id` 普通索引
- `video_asset.status` 普通索引
- `skill_run.job_id` 普通索引
- `finding.job_id` 普通索引
- `coverage_state.job_id` 普通索引

## 6. 表设计原则

- 视频原文件和中间文件不要直接放数据库
- 数据库只存元数据和结果
- 大 JSON 字段可以先用文本字段承载
- 后续如果查询复杂，再拆成更细的规范化表

## 7. 和 DDD 的对应关系

- 表不是业务中心
- 表只是领域对象的持久化表达
- 业务规则应保留在领域层
