"""
诊断质量 mock 评测集（v1）。

每个样本是一份构造出来的证据包（与 Java /evidence 接口返回的结构一致，含 v0.2 timelineJson），
并预埋已知问题。agent 看不到画面，它的输入本来就是文字时间轴，所以 mock 证据包可以直接测
"诊断逻辑"——但测不了 OCR / ASR / 镜头检测本身的质量，也不代表在真实视频上的准确率。

字段：
- ``expected``：预埋的问题，系统应当报为 GAP（维度 + 问题类型）；
- ``forbidden``：不应当报为 GAP 的问题（目标其实做得好 / 证据不支持 / 超出分析窗口）；
- ``strength_dims``：目标明显优于参考的维度，不应当以 GAP 出现在改进清单里；
- ``accept``：预埋问题的等价说法（例如"节奏不均"报成过密或过慢都算找到）；
- ``group``：``base``（c01~c19，前四轮迭代用）/ ``hard``（c20 起，规则定型后新增，用来比较模型）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from agent_service.graph.finding_types import ISSUE_TYPES

DIMENSIONS = ("HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY")


@dataclass
class QualityCase:
  case_id: str
  description: str
  target: dict[str, Any]
  references: list[dict[str, Any]]
  expected: list[str] = field(default_factory=list)
  forbidden: list[str] = field(default_factory=list)
  strength_dims: list[str] = field(default_factory=list)
  title: str = ""
  accept: dict[str, list[str]] = field(default_factory=dict)
  group: str = "base"
  # criteria 组：用户上传的评分标准原文、是否勾选整体补充分析、每条标准期望的（归属维度, 结果）
  criteria_text: str = ""
  supplementary: bool = False
  expected_criteria: list[tuple[str, str]] = field(default_factory=list)
  # rag 组：任务品类（决定私有评分点是否生效）、这道题依赖的评分点 id（用来统计检索有没有把它找出来）
  category: str = ""
  depends_on: list[str] = field(default_factory=list)

  def evidence_pack(self) -> dict[str, Any]:
    return {"jobId": self.case_id, "targetEvidence": self.target, "referenceEvidence": self.references}


# ---------- 证据包构造 ----------


def _ts(seconds: float) -> str:
  total = int(max(0, seconds))
  return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def video(
  asset_id: str,
  *,
  duration: float,
  speech: list[tuple[float, float, str]] | None = None,
  screen: list[tuple[float, float, str]] | None = None,
  cuts: list[float] | None = None,
  window: float = 120.0,
  speech_status: str = "ok",
) -> dict[str, Any]:
  """按 Java VideoFeatureExtractor v0.2 的输出格式构造一个视频的证据。"""
  analyzed = min(duration, window)
  cuts = sorted(c for c in (cuts or []) if 0 < c < analyzed)
  times = [t for t in (0, 1, 2, 3, 4) if t < analyzed]
  t = 5.0
  while t < analyzed:
    times.append(t)
    t += 3
  for cut in cuts:
    at = round(cut + 0.3, 1)
    if all(abs(at - existing) >= 1.0 for existing in times):
      times.append(at)
  end = max(0.0, analyzed - 0.5)
  if all(abs(end - existing) >= 0.5 for existing in times):
    times.append(end)
  times = sorted(times)[:60]
  keyframes = [
    {
      "index": i + 1,
      "time": _ts(sec),
      "seconds": sec,
      "reason": "hook" if sec < 5 else ("end" if sec == end else ("scene" if any(abs(sec - c - 0.3) < 0.05 for c in cuts) else "interval")),
      "url": f"http://minio/frames/{asset_id}/frame-{i + 1:03d}.jpg",
    }
    for i, sec in enumerate(times)
  ]
  bounds = [0.0, *cuts, analyzed]
  scenes = [
    {
      "index": i + 1,
      "start": _ts(bounds[i]),
      "end": _ts(bounds[i + 1]),
      "startSeconds": bounds[i],
      "endSeconds": bounds[i + 1],
      "durationSeconds": round(bounds[i + 1] - bounds[i], 1),
    }
    for i in range(len(bounds) - 1)
  ]
  speech_rows = [
    {"start": _ts(s), "end": _ts(e), "startSeconds": s, "endSeconds": e, "text": text}
    for s, e, text in (speech or [])
    if s < analyzed
  ] if speech_status == "ok" else []
  ocr_rows = [
    {"frameIndex": i + 1, "time": _ts(s), "end": _ts(e), "timeRange": f"{_ts(s)}-{_ts(e)}", "startSeconds": s, "endSeconds": e, "text": text}
    for i, (s, e, text) in enumerate(screen or [])
    if s < analyzed
  ]
  timeline = {
    "version": "0.2.0",
    "durationSeconds": duration,
    "analyzedSeconds": analyzed,
    "truncated": duration > window,
    "sceneChangeCount": len(cuts),
    "keyframes": keyframes,
    "transcript": {"status": speech_status, "model": "whisper-1", "segments": speech_rows},
  }
  return {
    "videoAssetId": asset_id,
    "transcriptText": " ".join(row["text"] for row in speech_rows),
    "keyframes": [item["url"] for item in keyframes],
    "sceneJson": json.dumps(
      {"detected": True, "durationSeconds": duration, "analyzedSeconds": analyzed, "sceneCount": len(scenes), "scenes": scenes},
      ensure_ascii=False,
    ),
    "ocrJson": json.dumps({"ocr": ocr_rows}, ensure_ascii=False),
    "timelineJson": json.dumps(timeline, ensure_ascii=False),
  }


def every(step: float, until: float, start: float | None = None) -> list[float]:
  out = []
  t = start if start is not None else step
  while t < until:
    out.append(round(t, 1))
    t += step
  return out


# ---------- 共享片段：早餐教程题材 ----------

_GOOD_HOOK_SPEECH = (0.5, 3.5, "三个技巧，让你的早餐五分钟就能做好")
_GOOD_HOOK_SCREEN = (0.0, 4.0, "5分钟早餐 3个技巧")
_STEPS_SPEECH = [
  (12, 18, "第一步，前一天晚上把鸡蛋煮好放冰箱"),
  (30, 37, "第二步，燕麦用牛奶提前泡一晚"),
  (50, 57, "第三步，面包机定时，早上起来直接拿"),
]
_STEPS_SCREEN = [(12, 20, "第一步 提前煮蛋"), (30, 38, "第二步 隔夜燕麦"), (50, 58, "第三步 面包机定时")]
_RESULT_SPEECH = (65, 72, "这样做之后我每天早上只花五分钟，比以前省了二十分钟")
_RESULT_SCREEN = (65, 73, "以前25分钟 → 现在5分钟")
_CTA_SPEECH = (80, 85, "觉得有用就关注我，下期教你做便当")
_NORMAL_CUTS = every(6, 88)


def _reference_good(asset_id: str = "ref-good", **overrides: Any) -> dict[str, Any]:
  params: dict[str, Any] = {
    "duration": 88,
    "speech": [_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
    "screen": [_GOOD_HOOK_SCREEN, *_STEPS_SCREEN, _RESULT_SCREEN],
    "cuts": _NORMAL_CUTS,
  }
  params.update(overrides)
  return video(asset_id, **params)


# ---------- 样本 ----------


def build_cases() -> list[QualityCase]:
  cases: list[QualityCase] = []

  cases.append(QualityCase(
    "c01_hook_no_promise",
    "目标开场 6 秒是寒暄，没有任何价值承诺；参考第 0.5 秒就承诺'五分钟做好早餐'。",
    target=video("t01", duration=88, cuts=_NORMAL_CUTS,
                 speech=[(0.5, 6, "大家好，我是小王，今天天气不错，我们来聊聊早餐"), *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[(0, 6, "小王的日常"), *_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["hook_no_value_promise"],
    forbidden=["no_cta", "pacing_too_dense", "pacing_too_slow"],
  ))

  cases.append(QualityCase(
    "c02_hook_slow_start",
    "目标前 6 秒是没有口播、没有字幕的空镜，第 6 秒才开始说话。",
    target=video("t02", duration=90, cuts=[6, *every(6, 90, start=12)],
                 speech=[(6.5, 10, "三个技巧，让你的早餐五分钟就能做好"), *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[(6, 10, "5分钟早餐 3个技巧"), *_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["hook_slow_start"],
    forbidden=["no_cta", "value_unclear"],
  ))

  cases.append(QualityCase(
    "c03_value_late",
    "目标开场只说'今天分享一些早餐心得'，具体收益（省二十分钟）直到第 70 秒才出现。",
    target=video("t03", duration=88, cuts=_NORMAL_CUTS,
                 speech=[(0.5, 4, "今天分享一些我做早餐的心得"), (15, 25, "我平时会提前准备一些东西"), (40, 50, "比如鸡蛋燕麦面包这些"),
                         (70, 77, "这样每天早上只要五分钟，能省二十分钟"), _CTA_SPEECH],
                 screen=[(0, 4, "早餐心得"), (70, 77, "省20分钟")]),
    references=[_reference_good()],
    expected=["value_late"],
    forbidden=["no_cta"],
  ))

  cases.append(QualityCase(
    "c04_no_cta",
    "目标内容完整，但结尾直接结束，没有任何关注/下一步引导；参考结尾有明确行动号召。",
    target=video("t04", duration=86, cuts=_NORMAL_CUTS,
                 speech=[_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, _RESULT_SPEECH, (80, 84, "好了，今天就到这里")],
                 screen=[_GOOD_HOOK_SCREEN, *_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["no_cta"],
    forbidden=["hook_no_value_promise", "hook_slow_start", "value_late"],
  ))

  cases.append(QualityCase(
    "c05_no_proof",
    "目标说'效果非常好'，但从头到尾没有展示结果；参考有'25分钟→5分钟'的前后对比。",
    target=video("t05", duration=80, cuts=every(6, 80),
                 speech=[_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, (65, 70, "用了这三个方法效果非常好"), (74, 79, "觉得有用就关注我")],
                 screen=[_GOOD_HOOK_SCREEN, *_STEPS_SCREEN]),
    references=[_reference_good()],
    expected=["no_proof"],
    forbidden=["no_cta", "hook_no_value_promise"],
  ))

  cases.append(QualityCase(
    "c06_pacing_dense",
    "目标平均 1.8 秒切一次镜头（48 个镜头/88 秒），参考约 6 秒一次。",
    target=video("t06", duration=88, cuts=every(1.8, 88),
                 speech=[_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[_GOOD_HOOK_SCREEN, *_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["pacing_too_dense"],
    forbidden=["pacing_too_slow", "no_cta", "hook_no_value_promise"],
  ))

  cases.append(QualityCase(
    "c07_pacing_slow",
    "目标前 75 秒一镜到底没有任何切换，参考约 6 秒切一次。",
    target=video("t07", duration=88, cuts=[75, 82],
                 speech=[_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[_GOOD_HOOK_SCREEN, *_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["pacing_too_slow"],
    forbidden=["pacing_too_dense", "no_cta"],
  ))

  cases.append(QualityCase(
    "c08_structure_unclear",
    "目标讲了同样三件事，但没有'第一步/第二步'这类口播或字幕标记，内容混在一起。",
    target=video("t08", duration=88, cuts=_NORMAL_CUTS,
                 speech=[_GOOD_HOOK_SPEECH, (12, 40, "鸡蛋可以前一天煮好然后燕麦也可以泡着其实面包机也能定时都挺方便的"),
                         _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[_GOOD_HOOK_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["structure_unclear"],
    forbidden=["no_cta", "hook_no_value_promise"],
  ))

  cases.append(QualityCase(
    "c09_strength_hook",
    "目标开场比参考强：目标第 0.5 秒就承诺收益并配大字幕，参考开场是寒暄。其它维度两者相当。",
    target=_reference_good("t09"),
    references=[video("r09", duration=88, cuts=_NORMAL_CUTS,
                      speech=[(0.5, 6, "大家好，今天聊聊早餐"), *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                      screen=[*_STEPS_SCREEN, _RESULT_SCREEN])],
    forbidden=["hook_no_value_promise", "hook_slow_start", "hook_weak_visual_text", "no_cta"],
    strength_dims=["HOOK"],
  ))

  cases.append(QualityCase(
    "c10_strength_value",
    "目标收益表达、结果证明、结尾引导都比参考完整；参考收益模糊且没有结尾引导。",
    target=_reference_good("t10"),
    references=[video("r10", duration=80, cuts=_NORMAL_CUTS,
                      speech=[(0.5, 4, "早餐其实可以很简单"), (20, 40, "准备一些东西就行"), (70, 78, "就这样吧")],
                      screen=[(0, 4, "简单早餐")])],
    forbidden=["value_late", "value_unclear", "no_cta", "no_proof"],
    strength_dims=["VALUE_DELIVERY"],
  ))

  cases.append(QualityCase(
    "c11_contradiction_bait",
    "目标开场口播已经明确承诺收益，只是开场没有屏幕文字；参考开场有大字幕。"
    "正确判断是'开场缺屏幕文字强化'，而不是'开场没有价值承诺'，价值传递也不应判为收益太晚。",
    target=video("t11", duration=88, cuts=_NORMAL_CUTS,
                 speech=[_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[*_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good()],
    expected=["hook_weak_visual_text"],
    forbidden=["hook_no_value_promise", "value_late", "value_unclear"],
  ))

  cases.append(QualityCase(
    "c12_asr_failed",
    "目标语音转写失败（speechStatus=failed），只有屏幕文字；收益文字第 40 秒才出现。不应引用或臆测口播内容。",
    target=video("t12", duration=88, cuts=_NORMAL_CUTS, speech_status="failed",
                 screen=[(0, 4, "早餐分享"), (40, 48, "每天省20分钟"), (80, 86, "关注我")]),
    references=[_reference_good()],
    expected=["value_late"],
    forbidden=["no_cta"],
  ))

  cases.append(QualityCase(
    "c13_truncated_long_video",
    "目标视频 5 分钟，只分析了前 120 秒；开场没有价值承诺。结尾不在分析窗口内，不能断言'没有行动号召'。",
    target=video("t13", duration=300, cuts=every(6, 120),
                 speech=[(0.5, 8, "嗨大家好，最近好忙，今天随便聊聊"), (20, 40, "说到早餐我有一些想法"), (60, 90, "鸡蛋燕麦这些可以提前准备")],
                 screen=[(0, 8, "随便聊聊")]),
    references=[_reference_good()],
    expected=["hook_no_value_promise"],
    forbidden=["no_cta"],
  ))

  cases.append(QualityCase(
    "c14_equal_quality",
    "目标与参考几乎一致（同样的结构、节奏、收益与结尾），不应报出明显问题。",
    target=_reference_good("t14", cuts=every(5.5, 88)),
    references=[_reference_good()],
    forbidden=["hook_no_value_promise", "hook_slow_start", "pacing_too_dense", "pacing_too_slow", "value_late", "no_cta", "no_proof"],
  ))

  cases.append(QualityCase(
    "c15_two_references_dense",
    "两个参考视频节奏都在 5~7 秒切一次，目标 1.5 秒切一次；其它维度相当。",
    target=video("t15", duration=88, cuts=every(1.5, 88),
                 speech=[_GOOD_HOOK_SPEECH, *_STEPS_SPEECH, _RESULT_SPEECH, _CTA_SPEECH],
                 screen=[_GOOD_HOOK_SCREEN, *_STEPS_SCREEN, _RESULT_SCREEN]),
    references=[_reference_good("ref-a"), _reference_good("ref-b", cuts=every(7, 88))],
    expected=["pacing_too_dense"],
    forbidden=["pacing_too_slow", "no_cta"],
  ))

  # ---- 第三轮新增：换话题、换说法，防止提示词只对早餐样本有效 ----
  fitness_cuts = every(5, 75)
  cases.append(QualityCase(
    "c16_fitness_strength_hook",
    "健身话题。目标开场'每天10分钟，三周练出马甲线'，参考开场'大家好，今天跟大家分享一下健身'；其它相当。目标开场是优势。",
    target=video("t16", duration=75, cuts=fitness_cuts,
                 speech=[(0.3, 3.5, "每天10分钟，三周练出马甲线"), (10, 18, "第一个动作卷腹，做二十个"),
                         (30, 38, "第二个动作平板支撑一分钟"), (55, 62, "我练了三周腰围小了五厘米"), (68, 73, "关注我，明天教你练臀")],
                 screen=[(0, 4, "10分钟马甲线"), (55, 62, "腰围 -5cm")]),
    references=[video("r16", duration=75, cuts=fitness_cuts,
                      speech=[(0.3, 4, "大家好，今天跟大家分享一下健身"), (10, 18, "第一个动作卷腹，做二十个"),
                              (30, 38, "第二个动作平板支撑一分钟"), (55, 62, "我练了三周腰围小了五厘米"), (68, 73, "关注我，明天教你练臀")],
                      screen=[(55, 62, "腰围 -5cm")])],
    forbidden=["hook_no_value_promise", "hook_slow_start", "value_late"],
    strength_dims=["HOOK"],
    title="10分钟马甲线",
  ))

  finance_cuts = every(6, 90)
  cases.append(QualityCase(
    "c17_finance_value_late",
    "理财话题。目标开场'聊聊存钱这件事'，'一年多存一万块'到第 50 秒才说；参考第 2 秒就说出这个收益。",
    target=video("t17", duration=90, cuts=finance_cuts,
                 speech=[(0.5, 4, "今天我们来聊聊存钱这件事"), (15, 25, "很多人工资一到手就花光了"),
                         (50, 57, "用这个方法我一年多存了一万块"), (60, 75, "方法就是发工资当天先转走两成"), (84, 89, "收藏起来慢慢看")],
                 screen=[(0, 4, "聊聊存钱"), (50, 57, "一年多存1万")]),
    references=[video("r17", duration=90, cuts=finance_cuts,
                      speech=[(0.5, 4, "这个方法让我一年多存了一万块"), (15, 25, "很多人工资一到手就花光了"),
                              (40, 55, "方法就是发工资当天先转走两成"), (84, 89, "收藏起来慢慢看")],
                      screen=[(0, 4, "一年多存1万"), (40, 55, "工资先转走20%")])],
    expected=["value_late"],
    forbidden=["no_cta", "pacing_too_dense", "pacing_too_slow"],
    title="存钱方法",
  ))

  photo_speech = [(0.4, 3.5, "这一招让你的照片一秒变高级"), (8, 16, "打开相册点编辑"), (20, 30, "把对比度拉低一点"),
                  (40, 50, "再把色温往暖调"), (58, 63, "前后对比一下差别很明显"), (66, 70, "关注我学更多修图")]
  photo_screen = [(0, 4, "一秒变高级"), (58, 63, "修图前 / 修图后")]
  cases.append(QualityCase(
    "c18_photo_same_opening_dense",
    "修图话题。目标与参考开场完全相同，目标平均 1.6 秒切一次镜头，参考约 7 秒一次。开场不应判为差距。",
    target=video("t18", duration=72, cuts=every(1.6, 72), speech=photo_speech, screen=photo_screen),
    references=[video("r18", duration=72, cuts=every(7, 72), speech=photo_speech, screen=photo_screen)],
    expected=["pacing_too_dense"],
    forbidden=["hook_no_value_promise", "hook_slow_start", "hook_weak_visual_text", "value_late"],
    title="照片一秒变高级",
  ))

  english_cuts = every(6, 80)
  cases.append(QualityCase(
    "c19_english_strength_value",
    "英语学习话题。目标开场就说'学会这5个句型，开会发言不再卡壳'并逐个演示，结尾引导关注；"
    "参考第 45 秒才说清能学到什么且没有结尾引导。目标价值传递是优势。",
    target=video("t19", duration=80, cuts=english_cuts,
                 speech=[(0.5, 4, "学会这5个句型，开会发言不再卡壳"), (10, 50, "第一个句型是 I'd like to add 接下来逐个演示"),
                         (55, 65, "我同事用了一周就敢在会上发言了"), (72, 78, "关注我，下期讲邮件句型")],
                 screen=[(0, 4, "5个开会句型"), (55, 65, "一周敢发言")]),
    references=[video("r19", duration=80, cuts=english_cuts,
                      speech=[(0.5, 4, "今天说说英语"), (10, 40, "开会的时候可能会用到一些表达"),
                              (45, 55, "学会这几个句型开会就不会卡壳"), (70, 78, "好了就这些")],
                      screen=[(0, 4, "英语")])],
    forbidden=["value_late", "value_unclear", "no_cta", "no_proof"],
    strength_dims=["VALUE_DELIVERY"],
    title="开会英语句型",
  ))

  cases.extend(build_hard_cases())
  cases.extend(build_criteria_cases(cases))
  cases.extend(build_rag_cases())

  for case in cases:
    alternatives = [alt for alts in case.accept.values() for alt in alts]
    unknown = [item for item in [*case.expected, *case.forbidden, *alternatives] if item not in ISSUE_TYPES]
    if unknown:
      raise ValueError(f"{case.case_id}: unknown issue types {unknown}")
  return cases


# ---------- hard 组（c20 起）：规则定型后新增，话题全部换新 ----------
#
# 前 19 组上 gpt-5.6-luna 已经 100% 命中、0 误报，拉不开模型差距。这一组专门测：
# 细微差距、参考也有同样缺陷（必须真正比较）、证据噪声、一个视频多个问题、多个参考分歧、阈值边界，
# 以及 c23（平均镜头时长接近、但节奏明显不均：暴露了 same_pacing 只看平均值的缺陷，第五轮已修）。


def build_hard_cases() -> list[QualityCase]:
  cases: list[QualityCase] = []

  # c20 收纳：开场两者相同（都没有承诺）；目标收益只有"整齐很多、方便"，参考有具体数字
  closet_cuts = every(6, 84)
  closet_open = (0.5, 4, "今天来收拾一下我的衣柜")
  closet_steps = [(20, 30, "先把所有衣服拿出来分成常穿和不常穿"), (35, 48, "常穿的竖着叠放在中间层"), (52, 62, "不常穿的装进收纳袋放到顶层")]
  cases.append(QualityCase(
    "c20_closet_vague_benefit",
    "收纳话题。开场两者相同（都只说'收拾衣柜'）。参考第 10 秒说'能多放一倍衣服，找衣服从五分钟变成十秒'，"
    "结尾有'原来40件现在80件'；目标同一位置只说'这样会整齐很多，用起来也方便'。差距在收益是否具体。"
    "开场相同，不应判开场差距。",
    target=video("t20", duration=84, cuts=closet_cuts,
                 speech=[closet_open, (10, 16, "这样收拾完会整齐很多，用起来也方便"), *closet_steps,
                         (68, 74, "你看，收完之后是不是清爽多了"), (78, 83, "关注我，下期收拾厨房")],
                 screen=[(0, 4, "收拾衣柜"), (68, 74, "收纳后")]),
    references=[video("r20", duration=84, cuts=closet_cuts,
                      speech=[closet_open, (10, 16, "这个叠法能让衣柜多放一倍衣服，找衣服从五分钟变成十秒"), *closet_steps,
                              (68, 74, "原来只能放四十件，现在能放八十件"), (78, 83, "关注我，下期收拾厨房")],
                      screen=[(0, 4, "收拾衣柜"), (10, 16, "多放一倍"), (68, 74, "40件 → 80件")])],
    expected=["value_unclear"],
    forbidden=["hook_no_value_promise", "hook_slow_start", "value_late", "no_cta", "pacing_too_dense", "pacing_too_slow"],
    title="收拾衣柜",
    group="hard",
  ))

  # c21 跑步：参考结尾也没有行动号召 → no_cta 不是差距；真正的差距在开场
  run_cuts = every(6, 80)
  run_body = [(12, 22, "第一点，步频保持在每分钟一百八十步"), (28, 38, "第二点，落地时脚掌在身体正下方"),
              (45, 55, "第三点，每周跑量增加不超过百分之十"), (60, 68, "我这样练了两个月，膝盖再也没疼过")]
  run_end = (74, 79, "好了，今天就说到这里")
  cases.append(QualityCase(
    "c21_running_both_no_cta",
    "跑步话题。两者结尾都只说'今天就说到这里'，都没有行动号召——这不是目标相对参考的差距。"
    "真正的差距在开场：参考'三个习惯让你跑步不再膝盖疼'，目标是寒暄。",
    target=video("t21", duration=80, cuts=run_cuts,
                 speech=[(0.5, 6, "哈喽大家好，最近天气挺适合跑步的"), *run_body, run_end],
                 screen=[(0, 6, "跑步日常"), (60, 68, "两个月 膝盖不疼")]),
    references=[video("r21", duration=80, cuts=run_cuts,
                      speech=[(0.5, 4, "三个习惯，让你跑步再也不膝盖疼"), *run_body, run_end],
                      screen=[(0, 4, "跑步不伤膝 3个习惯"), (60, 68, "两个月 膝盖不疼")])],
    expected=["hook_no_value_promise"],
    # 第一版把 value_late 也列为"不该报"，是出题错误：目标收益第 60 秒才说，参考第 0.5 秒，收益确实晚
    forbidden=["no_cta", "pacing_too_dense", "pacing_too_slow", "structure_unclear"],
    title="跑步不伤膝",
    group="hard",
  ))

  # c22 编程：目标屏幕文字是大量 OCR 乱码，口播正常；真正的问题是结尾没有行动号召
  code_cuts = every(6, 78)
  code_speech = [(0.5, 4, "五个Python小技巧，让你的代码少写一半"), (10, 20, "第一个，用列表推导式代替for循环"),
                 (25, 35, "第二个，用enumerate同时拿到下标和值"), (40, 50, "第三个，用zip同时遍历两个列表"),
                 (55, 64, "我用这几个技巧把一个两百行的脚本改成了九十行")]
  cases.append(QualityCase(
    "c22_coding_ocr_noise",
    "编程话题。目标的屏幕文字识别结果大量是乱码（代码截图被 OCR 识别坏了），口播完整。"
    "目标结尾直接结束，参考结尾'关注我，下期讲装饰器'。不应引用乱码，也不应因乱码判开场没有承诺。",
    target=video("t22", duration=78, cuts=code_cuts,
                 # 第一版结尾是"代码我放在下面了"，算不算行动号召有争议（v4-pro 2/3 判为有），改成明确没有引导
                 speech=[*code_speech, (70, 76, "好了，这期就到这里")],
                 screen=[(0, 4, "P y七hon 5介 技I5"), (10, 20, "[x f0r x 1n ra nge(1O)] ‖ 囗"), (25, 35, "f0r i, v 1n enumer@te(l1st):"),
                         (40, 50, "z1p(a, b) ~~ |l|"), (55, 64, "2O0行 -> 9O行")]),
    references=[video("r22", duration=78, cuts=code_cuts,
                      speech=[*code_speech, (70, 76, "关注我，下期讲装饰器")],
                      screen=[(0, 4, "Python 5个技巧"), (55, 64, "200行 → 90行")])],
    expected=["no_cta"],
    forbidden=["hook_no_value_promise", "hook_slow_start", "value_late", "pacing_too_dense", "pacing_too_slow"],
    title="Python 小技巧",
    group="hard",
  ))

  # c23 做饭：平均镜头时长与参考只差 ~12%，但节奏明显不均：
  # 前 14 秒 12 个 1.2 秒的碎镜头，接着 40 秒一镜到底。旧 same_pacing 只看平均值，会把正确结论降级。
  cook_speech = [(0.5, 4, "十分钟做一道下饭的番茄炒蛋"), (15, 25, "鸡蛋先炒到半熟盛出来"), (30, 45, "番茄切块炒出汁再放一勺糖"),
                 (50, 58, "鸡蛋倒回去翻炒半分钟"), (65, 72, "就这么简单，十分钟搞定"), (82, 88, "关注我，每天一道家常菜")]
  cook_screen = [(0, 4, "10分钟 番茄炒蛋"), (65, 72, "10分钟搞定")]
  uneven_cuts = [*every(1.2, 14.5), 54, 63, 72, 81]
  cases.append(QualityCase(
    "c23_cooking_uneven_pacing",
    "做饭话题。目标前 14 秒切了 12 个 1.2 秒的碎镜头，随后 40 秒一镜到底，再每 9 秒切一次；"
    "平均镜头约 5.3 秒，参考均匀 6 秒一次（平均只差 12%）。节奏问题真实存在（不均匀），报'过密'或'过慢'都算找到。",
    target=video("t23", duration=90, cuts=uneven_cuts, speech=cook_speech, screen=cook_screen),
    references=[video("r23", duration=90, cuts=every(6, 90), speech=cook_speech, screen=cook_screen)],
    expected=["pacing_too_dense"],
    accept={"pacing_too_dense": ["pacing_too_slow"]},
    forbidden=["hook_no_value_promise", "hook_slow_start", "value_late", "no_cta"],
    title="番茄炒蛋",
    group="hard",
  ))

  # c24 护肤：一个视频两个问题，分别在两个维度
  skin_body = [(10, 20, "第一步，洗完脸先用化妆水拍到吸收"), (28, 38, "第二步，精华只要两滴就够"), (45, 55, "第三步，面霜在手心捂热再上脸")]
  cases.append(QualityCase(
    "c24_skincare_two_issues",
    "护肤话题。目标有两个问题：①前 6 秒是没有口播、没有字幕的空镜；②只说'皮肤变好了很多'，没有任何结果展示。"
    "参考第 0.5 秒承诺'三步让皮肤不再起皮'，结尾有'坚持两周、起皮从每天到零'的前后对比。",
    target=video("t24", duration=80, cuts=[6, *every(6, 80, start=12)],
                 speech=[(6.5, 9.5, "三步让你的皮肤不再起皮"), *skin_body, (60, 66, "用了之后皮肤变好了很多"), (72, 78, "关注我，下期讲防晒")],
                 screen=[(6, 10, "3步告别起皮")]),
    references=[video("r24", duration=80, cuts=every(6, 80),
                      speech=[(0.5, 3.5, "三步让你的皮肤不再起皮"), *skin_body, (60, 66, "坚持两周，从每天起皮到一次都没有"), (72, 78, "关注我，下期讲防晒")],
                      screen=[(0, 4, "3步告别起皮"), (60, 66, "第1天 vs 第14天")])],
    expected=["hook_slow_start", "no_proof"],
    forbidden=["no_cta", "pacing_too_dense", "pacing_too_slow", "structure_unclear"],
    title="三步告别起皮",
    group="hard",
  ))

  # c25 吉他：两个参考分歧，R1 强、R2 弱，目标介于两者之间 → 应以最好的参考为基准
  guitar_cuts = every(6, 90)
  guitar_steps = [(10, 20, "先练C和弦，无名指按五弦三品"), (25, 35, "再练G和弦，注意小指"), (65, 75, "最后把两个和弦连起来弹")]
  cases.append(QualityCase(
    "c25_guitar_divergent_refs",
    "吉他话题。R1 第 1 秒就说'学会这两个和弦，一周弹出第一首歌'；R2 第 60 秒才说；目标第 40 秒才说。"
    "目标比 R2 好、比 R1 差，应以最好的参考 R1 为基准判为收益太晚。",
    target=video("t25", duration=90, cuts=guitar_cuts,
                 speech=[(0.5, 4, "今天来教大家两个吉他和弦"), *guitar_steps[:2], (40, 47, "学会这两个和弦，一周就能弹出第一首歌"),
                         guitar_steps[2], (84, 89, "关注我，下期教扫弦")],
                 screen=[(0, 4, "两个和弦"), (40, 47, "一周弹第一首歌")]),
    references=[
      video("r25a", duration=90, cuts=guitar_cuts,
            speech=[(0.5, 4, "学会这两个和弦，一周就能弹出第一首歌"), *guitar_steps, (84, 89, "关注我，下期教扫弦")],
            screen=[(0, 4, "一周弹第一首歌")]),
      video("r25b", duration=90, cuts=guitar_cuts,
            speech=[(0.5, 4, "今天聊聊吉他"), *guitar_steps[:2], (60, 66, "学会这两个和弦，一周就能弹出第一首歌"),
                    guitar_steps[2], (84, 89, "关注我，下期教扫弦")],
            screen=[(0, 4, "吉他"), (60, 66, "一周弹第一首歌")]),
    ],
    expected=["value_late"],
    forbidden=["no_cta", "pacing_too_dense", "pacing_too_slow"],
    title="吉他两个和弦",
    group="hard",
  ))

  # c26 咖啡：阈值边界，目标收益只比参考晚 2.5 秒（阈值 3 秒）→ 不是 value_late
  coffee_cuts = every(6, 75)
  coffee_body = [(10, 20, "牛奶加热到六十度左右"), (25, 38, "用打奶器打三十秒"), (42, 52, "先倒浓缩再沿杯壁倒奶"),
                 (58, 64, "做出来和店里的一模一样，一杯省二十块"), (68, 73, "关注我，下期教拉花")]
  cases.append(QualityCase(
    "c26_coffee_benefit_boundary",
    "咖啡话题。参考第 0.5 秒说'在家做出咖啡店的拿铁'；目标先说'早上好'，第 3 秒说出同一句（只晚 2.5 秒，阈值 3 秒）。"
    "其余内容完全相同。不应判收益太晚，也不应判开场没有价值承诺。",
    target=video("t26", duration=75, cuts=coffee_cuts,
                 speech=[(0.3, 2.5, "早上好"), (3.0, 6, "这个方法让你在家做出咖啡店的拿铁"), *coffee_body],
                 screen=[(3, 6, "在家做拿铁"), (58, 64, "一杯省20元")]),
    references=[video("r26", duration=75, cuts=coffee_cuts,
                      speech=[(0.5, 3.5, "这个方法让你在家做出咖啡店的拿铁"), *coffee_body],
                      screen=[(0, 4, "在家做拿铁"), (58, 64, "一杯省20元")])],
    forbidden=["value_late", "hook_no_value_promise", "no_cta", "no_proof", "pacing_too_dense", "pacing_too_slow"],
    title="在家做拿铁",
    group="hard",
  ))
  return cases


# ---------- criteria 组：用户上传评分标准 ----------
#
# 复用基础组的证据包，只加上用户标准。测三件事：拆分 + 归属维度对不对、逐条结果对不对、有没有漏回应。


def build_criteria_cases(existing: list[QualityCase]) -> list[QualityCase]:
  by_id = {case.case_id: case for case in existing}
  no_cta = by_id["c04_no_cta"]
  unclear = by_id["c08_structure_unclear"]
  return [
    QualityCase(
      "cc1_criteria_no_cta",
      "c04 的证据包 + 用户标准。目标开场就承诺收益、每一步有字幕标题、没有竞品、但结尾没有行动号召。",
      target=no_cta.target,
      references=no_cta.references,
      expected=list(no_cta.expected),
      forbidden=list(no_cta.forbidden),
      group="criteria",
      criteria_text="1. 开头3秒内要说出观众能得到什么\n2. 结尾必须引导关注\n3. 不能出现竞品品牌的名字\n4. 每一步都要有字幕标题",
      # U3"不能出现竞品品牌的名字"：口播字幕能查、画面 logo 查不到，判"满足（仅依据口播字幕）"或"无法判断"都对
      expected_criteria=[("HOOK", "MET"), ("VALUE_DELIVERY", "NOT_MET"), ("OTHER", "MET|UNKNOWN"), ("STRUCTURE_RHYTHM", "MET")],
    ),
    QualityCase(
      "cc2_criteria_overall",
      "c08 的证据包 + 带小标题的用户标准 + 勾选整体补充分析。目标没有分步标记，也没有提到要求的品牌名。",
      target=unclear.target,
      references=unclear.references,
      expected=list(unclear.expected),
      forbidden=list(unclear.forbidden),
      group="criteria",
      criteria_text="开场：\n- 第一句话就说出能得到的结果\n节奏：\n- 每个步骤要用“第一步、第二步”标出来\n其他：\n- 视频里要提到品牌“小王早餐”",
      supplementary=True,
      expected_criteria=[("HOOK", "MET"), ("STRUCTURE_RHYTHM", "NOT_MET"), ("OTHER", "NOT_MET")],
    ),
  ]


# ---------- rag 组：正确答案依赖知识库里某条具体评分点 ----------
#
# 前面的题预埋的都是通用问题（开场寒暄、结尾没引导……），模型凭常识就能答对，测不出 RAG 的作用。
# 这一组的正确答案依赖：
# - A 类：34 条通用评分点里的边界 / 反直觉规则（例如"权威背书后马上接收益"不算铺垫、"喊人群标签不接收益"不算钩子）；
# - B 类：品类私有规范（knowledge/rubric/private_edu.md，category=知识教程），模型不可能事先知道；
# - 对照：同样的证据不带品类，私有规范不应生效（检验私有规范不会"泄漏"到其它任务）。
# 每题都在 depends_on 里写明依赖的评分点，评测时统计检索有没有把它找出来。

EDU = "知识教程"
_BODY_START = 12.0


def _tutorial(
  asset_id: str,
  opening_speech: list[tuple[float, float, str]],
  opening_screen: list[tuple[float, float, str]],
  steps: list[str],
  result: str,
  ending: str,
  *,
  step_titles: list[str] | None = None,
  cuts: list[float] | None = None,
  extra_screen: list[tuple[float, float, str]] | None = None,
  body_start: float = _BODY_START,
  duration: float = 60,
) -> dict[str, Any]:
  """标准教程视频：开场 → 三段正文 → 结果 → 结尾。除被测环节外，目标和参考保持一致。"""
  speech = list(opening_speech)
  screen = list(opening_screen)
  for index, text in enumerate(steps):
    start = body_start + index * 10
    speech.append((start, start + 7, text))
    if step_titles:
      screen.append((start, start + 7, step_titles[index]))
  speech.append((body_start + 31, body_start + 38, result))
  speech.append((duration - 6, duration - 1.5, ending))
  screen.extend(extra_screen or [])
  return video(asset_id, duration=duration, speech=speech, screen=screen, cuts=cuts if cuts is not None else every(6, duration))


def _dense_subtitles(start: float, end: float, lines: list[str], step: float = 2.5) -> list[tuple[float, float, str]]:
  rows = []
  t = start
  index = 0
  while t < end:
    rows.append((round(t, 1), round(min(t + step, end), 1), lines[index % len(lines)]))
    t += step
    index += 1
  return rows


def build_rag_cases() -> list[QualityCase]:
  cases: list[QualityCase] = []

  def add(case_id: str, description: str, target: dict[str, Any], reference: dict[str, Any], **kwargs: Any) -> None:
    cases.append(QualityCase(case_id, description, target=target, references=[reference], group="rag", **kwargs))

  # ---- A 类：开场钩子 ----
  diet_steps = ["第一步，早餐把白粥换成燕麦", "第二步，午饭先吃菜再吃饭", "第三步，晚饭七点前吃完"]
  diet = {"steps": diet_steps, "result": "我自己照做两周瘦了四斤", "ending": "关注我，下期讲外卖怎么点",
              "step_titles": ["燕麦代替白粥", "先菜后饭", "七点前吃完"]}
  add("r01_authority_then_benefit",
      "目标先用一句身份背书再立刻接收益（2.5 秒内），参考直接说收益。依赖'权威背书快速接收益'：不算铺垫。",
      _tutorial("tr01", [(0.3, 2.3, "做了十年营养师的小林告诉你"), (2.3, 5, "这个吃法让你一周轻松瘦两斤")],
                [(0, 5, "一周瘦两斤")], **diet),
      _tutorial("rr01", [(0.5, 3.5, "这个吃法让你一周轻松瘦两斤")], [(0, 4, "一周瘦两斤")], **diet),
      forbidden=["hook_slow_start", "hook_no_value_promise", "hook_weak_visual_text"],
      depends_on=["hook-good-case-authority-fast-v1"], title="一周瘦两斤")
  add("r02_self_intro_delay",
      "目标前 8 秒都在介绍自己，第 8.5 秒才说收益；参考第 0.5 秒说收益。依赖'自我介绍拖慢开场'（与 r01 成对）。",
      _tutorial("tr02", [(0.5, 4, "大家好，我是小林，做了十年营养师"), (4, 8, "平时很喜欢研究食谱，也经常帮朋友调整饮食"),
                         (8.5, 11, "这个吃法让你一周轻松瘦两斤")], [(0, 8, "营养师小林")], **diet),
      _tutorial("rr02", [(0.5, 3.5, "这个吃法让你一周轻松瘦两斤")], [(0, 4, "一周瘦两斤")], **diet),
      expected=["hook_slow_start"], accept={"hook_slow_start": ["hook_no_value_promise"]},
      depends_on=["hook-pattern-self-intro-delay-v1"], title="一周瘦两斤")

  neck = {"steps": ["第一个动作，下巴往后收十次", "第二个动作，双手抱头向前拉伸", "第三个动作，肩膀向后画圈"],
              "result": "每天做五分钟，我的肩颈酸痛两周就好多了", "ending": "关注我，下期讲腰痛",
              "step_titles": ["收下巴", "抱头拉伸", "肩膀画圈"]}
  add("r03_empty_suspense",
      "目标开场'看到最后你一定会感谢我，很多人都不知道'，没有对象和收益；参考'三个动作让肩颈不再酸痛'。依赖'空泛悬念吊胃口'。",
      _tutorial("tr03", [(0.5, 4, "看到最后你一定会感谢我，很多人都不知道")], [(0, 4, "看到最后")], **neck),
      _tutorial("rr03", [(0.5, 4, "三个动作，让你的肩颈不再酸痛")], [(0, 4, "3个动作 告别肩颈酸痛")], **neck),
      expected=["hook_no_value_promise"], depends_on=["hook-bad-case-empty-suspense-v1"], title="肩颈酸痛")

  sleep = {"steps": ["第一，起床后先拉开窗帘晒五分钟", "第二，下午三点后不喝咖啡", "第三，睡前一小时不看手机"],
               "result": "坚持一周，我早上醒来不再昏昏沉沉", "ending": "关注我，下期讲午睡",
               "step_titles": ["晒太阳", "三点后不喝咖啡", "睡前不看手机"]}
  add("r04_specific_curiosity_gap",
      "目标开场'为什么你睡了八小时还是累？问题不在睡多久'，悬念绑定具体问题；参考直接说收益。依赖'有效好奇缺口'：不算没有承诺。",
      _tutorial("tr04", [(0.5, 4.5, "为什么你睡了八小时还是累？问题根本不在睡多久")], [(0, 4.5, "睡8小时还累？")], **sleep),
      _tutorial("rr04", [(0.5, 4, "三个习惯，让你早上醒来不再累")], [(0, 4, "3个习惯 醒来不累")], **sleep),
      forbidden=["hook_no_value_promise", "hook_slow_start"],
      depends_on=["hook-pattern-curiosity-gap-v1"], title="睡醒还累")

  kids = {"steps": ["第一步，把衣服按顺序摆在床上", "第二步，教他先穿上衣再穿裤子", "第三步，穿好了马上夸他"],
              "result": "练了一周，我家孩子十分钟就能自己穿好", "ending": "关注我，下期讲刷牙",
              "step_titles": ["按顺序摆好", "先上衣后裤子", "马上夸"]}
  add("r05_audience_label_only",
      "目标开场只喊'宝妈们看过来！一定要看！'，没有接问题或收益；参考'宝妈们，这招让孩子十分钟自己穿好衣服'。依赖'点名目标人群'。",
      _tutorial("tr05", [(0.5, 4, "宝妈们看过来！宝妈们一定要看！")], [(0, 4, "宝妈必看")], **kids),
      _tutorial("rr05", [(0.5, 4, "宝妈们，这招让孩子十分钟自己穿好衣服")], [(0, 4, "孩子10分钟自己穿衣")], **kids),
      expected=["hook_no_value_promise"], depends_on=["hook-pattern-target-audience-v1"], title="孩子自己穿衣")

  photo = {"steps": ["第一步，把色温往暖调一点", "第二步，降低高光", "第三步，加一点颗粒"],
               "result": "调完之后照片质感明显不一样", "ending": "关注我，下期讲人像",
               "step_titles": ["色温调暖", "降高光", "加颗粒"]}
  add("r06_first_screen_visual_proof",
      "目标首屏就是'修图前 / 修图后'对比字幕，口播'修图前和修图后，就差这一步'；参考口播承诺'一秒变高级'。依赖'首屏视觉证据抓停留'。",
      _tutorial("tr06", [(0.5, 3.5, "修图前和修图后，就差这一步")], [(0, 4, "修图前 → 修图后")], **photo),
      _tutorial("rr06", [(0.5, 3.5, "这个调色方法让你的照片一秒变高级")], [(0, 4, "一秒变高级")], **photo),
      forbidden=["hook_slow_start", "hook_no_value_promise"],
      depends_on=["hook-good-case-visual-proof-v1"], title="调色")

  dryer = {"steps": ["第一步，先用冷风吹干发根", "第二步，热风顺着毛鳞片往下吹", "第三步，最后冷风定型"],
               "result": "这样吹完头发顺了很多，第二天也不炸", "ending": "关注我，下期讲卷发",
               "step_titles": ["冷风吹发根", "顺着往下吹", "冷风定型"]}
  add("r07_feature_first",
      "目标开场罗列'一千六百瓦、负离子、三档温控、磁吸风嘴'；参考'头发毛躁的人，用它吹五分钟就顺了'。依赖'开头先堆功能'。",
      _tutorial("tr07", [(0.5, 5, "这款吹风机一千六百瓦，负离子，三档温控，还有磁吸风嘴")], [(0, 5, "1600W 负离子 三档温控")], **dryer),
      _tutorial("rr07", [(0.5, 4, "头发毛躁的人，用它吹五分钟就顺了")], [(0, 4, "毛躁 5分钟变顺")], **dryer),
      expected=["hook_no_value_promise"], depends_on=["hook-bad-case-feature-first-v1"], title="吹风机")

  sheet = {"steps": ["第一步，先把表头冻结", "第二步，用条件格式标出异常", "第三步，用数据透视表汇总"],
               "result": "现在一张周报二十分钟就能做完", "ending": "关注我，下期讲图表",
               "step_titles": ["冻结表头", "条件格式", "数据透视表"]}
  add("r08_conflict_then_payoff",
      "目标开场先讲冲突'我差点因为一个表格被老板当众批评'，第 4.5 秒给收益；参考第 0.5 秒给收益。依赖'避免收益后置'：有冲突支撑，开场不算问题。",
      _tutorial("tr08", [(0.5, 4, "我差点因为一个表格被老板当众批评"), (4.5, 7.5, "后来学会这个方法，做表快了一倍")],
                [(0, 4, "差点被老板批评")], **sheet),
      _tutorial("rr08", [(0.5, 3.5, "这个方法让你做表快了一倍")], [(0, 4, "做表快一倍")], **sheet),
      forbidden=["hook_slow_start", "hook_no_value_promise"],
      depends_on=["hook-rule-avoid-late-payoff-v1"], title="做表")

  # ---- A 类：结构节奏 ----
  formula_lines = ["VLOOKUP 查找", "第一个参数：查找值", "第二个参数：区域", "第三个参数：列号", "第四个参数：精确匹配",
                   "常见错误：#N/A", "原因：格式不一致", "解决：统一文本格式", "IFERROR 兜底", "结果：一秒查完"]
  formula = {"steps": ["第一步，选中要查的单元格", "第二步，输入VLOOKUP填四个参数", "第三步，用IFERROR处理查不到的情况"],
                 "result": "以前手动查要半小时，现在一秒查完", "ending": "关注我，下期讲XLOOKUP"}
  add("r09_long_shots_dense_subtitles",
      "目标每个镜头 18 秒，但字幕每 2.5 秒更新一次、口播连续推进；参考 6 秒一切、字幕相同。依赖'信息密度与画面补偿'：不算节奏拖沓。",
      _tutorial("tr09", [(0.5, 4, "一个公式让你一秒查完一千行数据")], [], cuts=[18, 36, 54],
                extra_screen=_dense_subtitles(0, 60, formula_lines), **formula),
      _tutorial("rr09", [(0.5, 4, "一个公式让你一秒查完一千行数据")], [], cuts=every(6, 60),
                extra_screen=_dense_subtitles(0, 60, formula_lines), **formula),
      forbidden=["pacing_too_slow"], depends_on=["structure-rule-density-scene-change-v1"], title="VLOOKUP")
  add("r10_static_talking_head",
      "目标 30 秒一个镜头，全程只有开头一条字幕、没有分段字幕；参考 6 秒一切并有分段字幕。依赖'静态口播无节奏点'（与 r09 成对）。",
      _tutorial("tr10", [(0.5, 4, "一个公式让你一秒查完一千行数据")], [(0, 4, "VLOOKUP")], cuts=[30], **formula),
      _tutorial("rr10", [(0.5, 4, "一个公式让你一秒查完一千行数据")], [(0, 4, "VLOOKUP")], cuts=every(6, 60),
                extra_screen=_dense_subtitles(0, 60, formula_lines), **formula),
      expected=["pacing_too_slow"], depends_on=["structure-bad-case-static-talking-v1"], title="VLOOKUP")

  storage = {"result": "收完之后衣柜多放了一倍衣服", "ending": "关注我，下期收厨房"}
  add("r11_numbered_screen_markers",
      "目标口播没有'第一步'这类词，但屏幕上用'01 / 02 / 03'标出段落；参考口播和字幕都有'第一步'。依赖'节奏标记清晰'：不算结构不清。",
      _tutorial("tr11", [(0.5, 4, "三招让衣柜多放一倍衣服")], [(0, 4, "衣柜扩容")],
                steps=["先把衣服按季节分开", "常穿的竖着叠", "最后每个盒子贴上标签"],
                step_titles=["01 按季节分", "02 竖着叠", "03 贴标签"], **storage),
      _tutorial("rr11", [(0.5, 4, "三招让衣柜多放一倍衣服")], [(0, 4, "衣柜扩容")],
                steps=["第一步，先把衣服按季节分开", "第二步，常穿的竖着叠", "第三步，每个盒子贴上标签"],
                step_titles=["第一步 按季节分", "第二步 竖着叠", "第三步 贴标签"], **storage),
      forbidden=["structure_unclear"], depends_on=["structure-good-case-rhythm-marker-v1"], title="衣柜")

  money = {"result": "这样坚持一年，我多存了一万块", "ending": "关注我，下期讲基金"}
  add("r12_topic_jump",
      "目标正文在'焦虑 → App 功能 → 大学往事 → 存钱方法 → App 功能'之间来回跳，没有过渡；参考'首先 / 然后 / 最后'顺序推进。依赖'主题跳跃缺少过渡'。",
      _tutorial("tr12", [(0.5, 4, "这个方法让我一年多存一万块")], [(0, 4, "一年多存一万")],
                steps=["工资一到手就花光真的很焦虑", "这个记账App可以自动分类账单", "我大学的时候其实也不会理财"],
                extra_screen=[], **money),
      _tutorial("rr12", [(0.5, 4, "这个方法让我一年多存一万块")], [(0, 4, "一年多存一万")],
                steps=["首先，工资到手当天先转走两成", "然后，用记账App看清钱花在哪", "最后，每月底把剩下的钱也存起来"],
                step_titles=["先存两成", "看清花销", "月底再存"], **money),
      expected=["structure_unclear"], depends_on=["structure-bad-case-topic-jump-v1"], title="存钱")

  # ---- A 类：价值传递 ----
  fryer_open = [(0.5, 4, "这款空气炸锅我用了一个月")]
  add("r13_features_without_benefit",
      "目标正文只罗列'五升容量、八个预设菜单、热风循环、可拆洗内胆'，没说对用户有什么用；参考讲'早上十分钟做好不油腻的早餐、少用八成油'。依赖'只讲功能不讲收益'。",
      _tutorial("tr13", fryer_open, [(0, 4, "空气炸锅测评")],
                steps=["它是五升大容量，有八个预设菜单", "三百六十度热风循环，还有可拆洗内胆", "支持预约定时和APP控制"],
                result="整体参数在同价位里算很高的", ending="关注我，下期测烤箱"),
      _tutorial("rr13", fryer_open, [(0, 4, "空气炸锅测评")],
                steps=["早上放进鸡翅，十分钟就能出锅", "比油炸少用八成油，吃着不腻", "内胆能拆下来直接洗，两分钟搞定"],
                result="我现在每天早餐都用它，比以前省了二十分钟", ending="关注我，下期测烤箱"),
      expected=["value_unclear"], depends_on=["value-bad-case-feature-without-benefit-v1"], title="空气炸锅")
  cream = {"steps": ["洗完脸先拍爽肤水", "取黄豆大小的面霜", "从脸颊往外推开"], "ending": "关注我，下期讲防晒"}
  add("r14_vague_claim_no_proof",
      "目标结果只说'效果超级好，所有人都说好用'；参考'用了两周，水分测试从30%到45%，起皮从每天到零'。依赖'空泛价值主张'。",
      _tutorial("tr14", [(0.5, 4, "这款面霜让干皮不再起皮")], [(0, 4, "干皮救星")], result="用了之后效果超级好，所有人都说好用", **cream),
      _tutorial("rr14", [(0.5, 4, "这款面霜让干皮不再起皮")], [(0, 4, "干皮救星")],
                result="用了两周，水分测试从百分之三十到四十五，起皮从每天到一次都没有", **cream),
      expected=["no_proof"], accept={"no_proof": ["value_unclear"]},
      depends_on=["value-bad-case-vague-claim-v1"], title="面霜")
  words = {"steps": ["第一步，把单词按词根分组", "第二步，每组只背五个", "第三步，第二天先复习再背新的"],
               "ending": "关注我，下期讲听力"}
  add("r15_no_use_scenario",
      "目标收益只说'这个方法很实用，大家可以试一试'；参考'早上赶地铁那十分钟用它背单词，一个月多背六百个'。依赖'场景化价值'。",
      _tutorial("tr15", [(0.5, 4, "分享一个背单词的方法")], [(0, 4, "背单词方法")], result="这个方法很实用，大家可以试一试", **words),
      _tutorial("rr15", [(0.5, 4, "分享一个背单词的方法")], [(0, 4, "背单词方法")],
                result="早上赶地铁那十分钟用它背单词，一个月能多背六百个", **words),
      expected=["value_unclear"], depends_on=["value-pattern-use-scenario-v1"], title="背单词")

  # ---- B 类：知识教程私有规范（category=知识教程）----
  edu = {"steps": ["第一个公式，SUMIF按条件求和", "第二个公式，COUNTIF按条件计数", "第三个公式，IFERROR处理错误"],
             "step_titles": ["SUMIF", "COUNTIF", "IFERROR"], "result": "学会之后做一张月报从一小时缩短到二十分钟"}
  cta_edu = "评论区扣“公式”，我把模板发给你"
  add("r16_edu_title_after_2s",
      "知识教程。目标口播第 0.5 秒说出收益，但标题字幕第 3.5 秒才出现；参考标题字幕第 0 秒出现。私有规范：2 秒内必须出标题字幕。（两者标题用词不同，避免触发'开场文字相同'硬规则）",
      _tutorial("tr16", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(3.5, 6, "月报提速")], ending=cta_edu, **edu),
      _tutorial("rr16", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      expected=["hook_weak_visual_text"], category=EDU, depends_on=["private-edu-hook-title-2s-v1"], title="三个公式")
  add("r17_no_category_title_after_2s",
      "与 r16 证据完全相同但不带品类：私有规范不应生效，标题第 3.5 秒出现不算问题（检验私有规范不会泄漏到其它任务）。",
      _tutorial("tr17", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(3.5, 6, "月报提速")], ending=cta_edu, **edu),
      _tutorial("rr17", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      forbidden=["hook_weak_visual_text"], title="三个公式")
  add("r18_edu_question_opening",
      "知识教程。目标第一句是反问'你知道为什么你做表总是那么慢吗？'；参考直接陈述收益。私有规范：第一句不能用反问（优先于通用的'有效好奇缺口'）。",
      _tutorial("tr18", [(0.5, 4, "你知道为什么你做表总是那么慢吗？"), (4, 6.5, "因为你没用这三个公式")],
                [(0, 2, "做表为什么慢？")], ending=cta_edu, **edu),
      _tutorial("rr18", [(0.5, 3.5, "这三个公式让你做月报快三倍")], [(0, 2, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      expected=["hook_no_value_promise"], category=EDU, depends_on=["private-edu-hook-no-question-v1"], title="三个公式")
  edu_lines = ["SUMIF", "条件区域", "求和区域", "COUNTIF", "计数条件", "IFERROR", "兜底返回空", "月报模板", "一小时→二十分钟"]
  add("r19_edu_shots_over_8s",
      "知识教程。目标每个镜头 10 秒、参考 7 秒，两者字幕都每 2.5 秒更新。通用规则看会认为有字幕补偿；私有规范：单镜头超过 8 秒即节奏过慢。",
      _tutorial("tr19", [(0.5, 3, "学会这三个公式，做月报快三倍")], [], cuts=every(10, 60), ending=cta_edu,
                extra_screen=_dense_subtitles(0, 60, edu_lines), **edu),
      _tutorial("rr19", [(0.5, 3, "学会这三个公式，做月报快三倍")], [], cuts=every(7, 60), ending=cta_edu,
                extra_screen=_dense_subtitles(0, 60, edu_lines), **edu),
      expected=["pacing_too_slow"], category=EDU, depends_on=["private-edu-structure-shot-8s-v1"], title="三个公式")
  add("r20_edu_follow_only_cta",
      "知识教程。目标结尾'关注我，下期见'；参考结尾'评论区扣公式领模板'。通用看两者都有行动号召；私有规范：只说关注不算有效行动号召。",
      _tutorial("tr20", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending="关注我，下期见", **edu),
      _tutorial("rr20", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      expected=["no_cta"], category=EDU, depends_on=["private-edu-value-cta-keyword-v1"], title="三个公式")
  add("r21_no_category_follow_only_cta",
      "与 r20 证据完全相同但不带品类：'关注我，下期见'就是正常的行动号召，不应判 no_cta。",
      _tutorial("tr21", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending="关注我，下期见", **edu),
      _tutorial("rr21", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      forbidden=["no_cta"], title="三个公式")
  add("r22_edu_benefit_without_number",
      "知识教程。目标收益只说'做表更轻松、更高效'，参考'从一小时缩短到二十分钟'。私有规范：收益必须带数字。",
      _tutorial("tr22", [(0.5, 3, "学会这三个公式，做表更轻松")], [(0, 3, "3个公式 做表更轻松")], ending=cta_edu,
                steps=edu["steps"], step_titles=edu["step_titles"], result="学会之后做月报变得高效多了"),
      _tutorial("rr22", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 3, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      expected=["value_unclear"], category=EDU, depends_on=["private-edu-value-number-v1"], title="三个公式")
  add("r23_edu_all_rules_met",
      "知识教程。目标满足全部私有规范（0 秒标题、直接陈述、6 秒一切、量化收益、评论区关键词），参考同样满足。私有规范不应制造误报。",
      _tutorial("tr23", [(0.5, 3, "学会这三个公式，做月报快三倍")], [(0, 2, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      _tutorial("rr23", [(0.5, 3, "这三个公式让你做月报快三倍")], [(0, 2, "3个公式 月报快3倍")], ending=cta_edu, **edu),
      forbidden=["hook_weak_visual_text", "hook_no_value_promise", "pacing_too_slow", "no_cta", "value_unclear"],
      category=EDU, depends_on=["private-edu-hook-title-2s-v1", "private-edu-value-cta-keyword-v1"], title="三个公式")
  return cases
