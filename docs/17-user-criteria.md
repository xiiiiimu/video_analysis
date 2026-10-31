# 17. 用户评分标准 + 补充分析节点 + 内置评分点 md 化

## 用户怎么用

上传评分标准 txt + 目标视频 + 参考视频创建任务（视频先按原来的方式上传，拿到 videoId）：

```
curl.exe -F targetVideoId=<目标videoId> -F referenceVideoIds=<参考videoId> -F "criteria=@标准.txt" -F supplementaryAnalysis=false http://localhost:8080/api/v1/analysis/jobs/with-criteria
```

- txt 任意格式：每行一条、带编号、`开场：` 这类小标题、一行里用分号隔开都可以；UTF-8（记事本默认的带 BOM 也行），最多 2 万字、40 条。
- 也可以走原来的 JSON 接口 `POST /api/v1/analysis/jobs`，加字段 `criteriaText`、`supplementaryAnalysis`。
- `supplementaryAnalysis=true`：额外给一份整体补充分析；默认 false，只处理三个专家之外的标准。
- 结果：`GET /api/v1/analysis/jobs/{jobId}/report` 直接返回 Markdown 报告；结构化数据在 `/synthesis` 的
  `criteria`（解析出的标准）、`criteriaReport`（逐条对照）、`supplementary`（补充分析）。
- 同样两个视频换一套标准会生成新任务（标准原文计入任务去重键）。

## 系统里发生了什么

```
标准原文（inputSnapshot.criteriaText）
  → 拆分 + 归类 + 检查口径：模型一次完成（用户可能写的是一整段话）。text 要求逐字截取用户原文，
          不在原文里的标 verbatim=false；维度写错的条目用关键词兜底；模型失败或 mock 时整体退回
          规则拆分（按行 / 编号 / 分号）+ 关键词归类（splitBy / classifiedBy 字段标明来源）
  → 三个专家：各自只拿到分给自己的标准 + 检索到的内置评分点；必须在 criteria_verdicts 逐条回应
          （满足 / 不满足 / 无法判断 + 时间点和原文）；漏了 → Evaluator 打回
  → 补充分析节点（三个专家通过后运行，能看到他们的结论）：
          OTHER 类标准逐条回应；勾选整体补充分析时再给最多 3 条专家没覆盖的观察（必须有可核对的原文，否则丢弃）
  → 合成：解析出的标准 + 逐条对照表 + Markdown 报告；没有任何节点回应的标准标"未覆盖"，不静默丢掉
```

- **优先级**：用户标准 > 内置评分点。冲突时以用户为准（提示词明确要求）。
- **改进优先级和总结**：不满足的用户标准排在改进优先级最前面（改法用判断节点给出的 suggestion），三个维度的差距顺延；
  总结开头写"你的 N 条标准：满足 x 条，不满足 y 条（Ux …），无法判断 z 条"。第一次真实任务里，价值传递整体强于参考，
  "结尾必须引导关注"没满足，总结却写"没有需要优先改进的问题"——这一条就是为修这个矛盾。
- **隔离**：用户标准只属于本任务，不写入公共知识库，不影响其他用户。
- **补充分析的结论不进入改进优先级、不作为 Finding 落库**，只在报告的"补充分析"部分。
- **系统知道自己看不到什么**：能分析的只有口播转写、屏幕文字、镜头切换，看不到画面内容、听不到背景音乐。
  解析时每条标准标 observability：full（完整可查）/ partial（如"不能出现竞品"，口播字幕能查、画面 logo 查不到）/
  none（如"背景音乐要轻快"）。partial 的检查口径注明"画面 / 音频部分无法检查"，节点只依据口播和字幕判断并在依据里写明，
  报告里结果标"（仅依据口播和字幕）"；none 不交给任何节点，直接标"无法判断"并说明原因，避免把查不到说成"满足"。
- **改进优先级只写改法**，依据在逐条对照表里，不重复。
- **不需要用户确认解析结果**：报告第一部分就是"解析出的评分标准"（原文、归属、检查口径），用户能看到系统是怎么理解的。

## 内置评分点改成 md

`agent-service/knowledge/rubric/{hook,structure_rhythm,value_delivery}.md`，每条是一个 `## 标题` 小节：

```markdown
## 空泛悬念吊胃口
- id: hook-bad-case-empty-suspense-v1
- type: 反例            # 模式 / 规则 / 好例 / 反例 / 平台规则 / 品类最佳实践
- tags: hook, bad-case, empty-suspense

开头只说"看到最后""很多人不知道"……判定重点是悬念没有可判断的内容承诺。
```

- docker-compose 把 `agent-service/knowledge` 挂载进容器，不用重新 build：每个任务开始时重新读取 md，改完新任务就生效。
- 建议改完执行 `docker compose restart agent-service`：启动时校验格式，缺 id / type 写错 / 没正文 / id 重复都会直接报错，指出文件和行号。
- 迁移只换了存放位置：测试保证 md 内容与检索评测的 v0.3 冻结快照完全一致；检索评测继续用冻结快照，数字可复现。
  如果以后删掉或改了被 Golden Query 标注的 id，`test_rubric_loader` 会提示。

## 评测

新增 criteria 组（cc1、cc2，复用基础组证据包 + 用户标准），指标都带分子 / 分母：
拆分条数正确的样本占比、归属维度正确率、逐条结果正确率、有回应的占比（应为 100%）。

```
docker compose exec agent-service python -m agent_service.eval.quality_benchmark --rules v2 --repeat 2 --cases criteria
```
