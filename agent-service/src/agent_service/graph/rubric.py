"""
诊断评分点（RAG）。

设计：每个维度专家在下结论之前，先从知识库检索本维度的评分点（判定重点 + 边界），
评分点随证据一起交给模型；模型的每条结论必须在 ``rubric_refs`` 里注明依据了哪几条评分点，
系统校验这些引用确实是本次检索到的（Evaluator 不通过会打回）。

检索 query 用"维度关注点 + 目标视频本身的特征"拼成，让检索结果随视频变化：
开场说了什么、镜头是否长期不变 / 切换很碎、口播里有没有收益和结果。
"""

from __future__ import annotations

import json
import re
from typing import Any

from agent_service.graph.evidence_timeline import (
  ocr_items,
  opening_text,
  scene_stats,
  transcript_segments,
)

_DIMENSION_FOCUS = {
  "hook_analysis": "开头 首屏 停留 承诺",
  "structure_rhythm_analysis": "结构 段落 节奏 推进",
  "value_delivery_analysis": "价值 收益 结果",
}
_STEP_MARKER = re.compile(r"第[一二三四五六七八九十\d]+[步点个]|首先|其次|最后")
_QUERY_TEXT_CHARS = 400
# 视频特征信号：缺什么，就把对应评分点的说法加进 query，让检索结果随视频变化
_CTA = re.compile(r"关注|收藏|评论|点赞|下期|私信|链接|转发|试试|去做")
_PROOF = re.compile(r"\d|[一二两三四五六七八九十百千万]+(?:分钟|秒|天|周|个月|年|块|元|斤|公斤|厘米|倍|件)|前后|对比|之前|以前|→|->")
_OPENING_BENEFIT = re.compile(r"让你|学会|省|告别|不再|变|快速|秒|分钟|技巧|方法|招")
# 开场的写法特征 → 对应评分点的说法（反直觉 / 边界类评分点要靠这些信号才检索得到）
_HOOK_SIGNALS: list[tuple[re.Pattern[str], str]] = [
  (re.compile(r"我是|大家好|做了.{0,4}年"), "自我介绍 身份 权威 背书 铺垫"),
  (re.compile(r"[?？]|为什么|居然|竟然|没想到|看到最后|很多人不知道|你知道"), "悬念 好奇 反常识 反差 看到最后"),
  (re.compile(r"们[，,!！]|看过来|必看|适合.{0,6}的人"), "点名 目标人群 谁需要看 人群标签"),
  (re.compile(r"\d+\s*(?:W|瓦|档|升|毫安|寸)|参数|功能|配置|负离子|温控"), "功能 参数 成分 堆砌 用户连接"),
  (re.compile(r"前后|对比|→|修图前|使用前"), "首屏 结果 前后对比 效果变化 视觉证据"),
  (re.compile(r"差点|被.{0,6}(?:批评|骂|开除)|焦虑|崩溃|突然|翻车"), "冲突 情绪张力 悬念 收益后置"),
]
_VALUE_SIGNALS: list[tuple[re.Pattern[str], str]] = [
  (re.compile(r"参数|容量|预设|支持|循环|配置|功能"), "功能 参数 成分 流程 用户为什么需要"),
  (re.compile(r"效果.{0,4}好|都说好|很推荐|很实用|超级好"), "空泛 效果很好 很实用 不可验证 对象 场景"),
]


def _texts(video: dict[str, Any]) -> str:
  speech = " ".join(str(item.get("text") or "") for item in transcript_segments(video))
  screen = " ".join(str(item.get("text") or "") for item in ocr_items(video))
  return f"{speech} {screen}".strip()


def rubric_query(skill_key: str, evidence_pack: dict[str, Any]) -> str:
  target = evidence_pack.get("targetEvidence") or {}
  parts = [_DIMENSION_FOCUS.get(skill_key, "")]
  if skill_key == "hook_analysis":
    opening = opening_text(target, seconds=5.0)
    if not opening:
      parts.append("开头 没有 信息 铺垫 收益后置 冲突 悬念 张力")
    elif not _OPENING_BENEFIT.search(opening):
      parts.append("泛泛开场 对象 问题 收益 痛点 铺垫")
    parts.extend(words for pattern, words in _HOOK_SIGNALS if pattern.search(opening))
    parts.append(opening[:_QUERY_TEXT_CHARS])
  elif skill_key == "structure_rhythm_analysis":
    stats = scene_stats(target, "T") or {}
    longest = float(((stats.get("longestShot") or {}).get("seconds")) or 0)
    if longest >= 15:
      parts.append("镜头 长期不变 静态 画面 信息密度")
    if int(stats.get("shotsUnder2s") or 0) >= 5:
      parts.append("切换 频繁 节奏 变化")
    text = _texts(target)
    parts.append("步骤 列表 数字 标记 层级" if _STEP_MARKER.search(text) else "过渡 段落 跳跃")
    parts.append(text[:_QUERY_TEXT_CHARS])
  else:
    text = _texts(target)
    ending = _ending_text(target)
    if not _CTA.search(ending):
      parts.append("行动号召 CTA 结尾 下一步 匹配 前文")
    if not _PROOF.search(text):
      parts.append("证据 案例 数据 反馈 对比 支撑 价值主张 可验证")
    if not _OPENING_BENEFIT.search(opening_text(target, seconds=5.0)):
      parts.append("收益 具体化 观众获得 场景")
    parts.extend(words for pattern, words in _VALUE_SIGNALS if pattern.search(text))
    parts.append(text[:_QUERY_TEXT_CHARS])
  return " ".join(part for part in parts if part).strip()


def _ending_text(video: dict[str, Any], seconds: float = 15.0) -> str:
  segments = transcript_segments(video)
  screen = ocr_items(video)
  ends = [float(item.get("endSeconds") or item.get("startSeconds") or 0) for item in [*segments, *screen]]
  if not ends:
    return ""
  cutoff = max(ends) - seconds
  rows = [item for item in [*segments, *screen] if float(item.get("startSeconds") or 0) >= cutoff]
  return " ".join(str(item.get("text") or "") for item in rows)


def job_category(job_context: dict[str, Any]) -> str:
  """任务品类（创建任务时传入）：决定哪些品类专属评分点（私有规范）生效。"""
  raw = job_context.get("inputSnapshotJson") or {}
  if isinstance(raw, str):
    try:
      raw = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
      raw = {}
  return str((raw if isinstance(raw, dict) else {}).get("category") or job_context.get("category") or "").strip()


def rubric_items(observations: list[dict[str, Any]]) -> list[dict[str, str]]:
  """从检索观察里取出评分点（去重，保持检索顺序）。"""
  items: list[dict[str, str]] = []
  seen: set[str] = set()
  for observation in observations:
    payload = observation.get("payload") or {}
    for item in payload.get("items") or [] if isinstance(payload, dict) else []:
      ref = str(item.get("evidenceRef") or "")
      if not ref or ref in seen:
        continue
      seen.add(ref)
      items.append({
        "ref": ref,
        "type": str(item.get("knowledgeType") or ""),
        "title": str(item.get("title") or ""),
        "content": str(item.get("content") or ""),
      })
  return items
