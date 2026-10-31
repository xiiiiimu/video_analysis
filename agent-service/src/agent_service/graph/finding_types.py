"""
诊断结论分类表（quality rules v2）。

``finding_type`` 必须取自这里，便于统计、评测和前端归类；改进清单只收 polarity=GAP 的结论。
eval 的 mock 评测集也使用同一份分类表判断"预埋问题是否被找到"。
"""

from __future__ import annotations

from typing import Any

# polarity：结论相对参考视频的方向
GAP = "GAP"            # 目标比参考差，需要改进
STRENGTH = "STRENGTH"  # 目标比参考好，保持即可，不进入改进清单
PARITY = "PARITY"      # 两者相当，没有显著差距
POLARITIES = (GAP, STRENGTH, PARITY)

ISSUE_TYPES: dict[str, dict[str, Any]] = {
  "hook_no_value_promise": {"dimension": "HOOK", "label": "开场没有价值承诺", "keywords": ["价值", "收益", "承诺", "好处", "预期", "主题"]},
  "hook_slow_start": {"dimension": "HOOK", "label": "开场铺垫过长/前几秒没有信息", "keywords": ["铺垫", "空镜", "沉默", "无信息", "进入主题", "慢", "迟迟"]},
  "hook_weak_visual_text": {"dimension": "HOOK", "label": "开场缺少屏幕文字强化", "keywords": ["屏幕文字", "字幕", "标题", "文字"]},
  "pacing_too_dense": {"dimension": "STRUCTURE_RHYTHM", "label": "镜头切换过密", "keywords": ["频繁", "过密", "密集", "过快", "切换过多"]},
  "pacing_too_slow": {"dimension": "STRUCTURE_RHYTHM", "label": "节奏拖沓/长时间无变化", "keywords": ["拖沓", "单调", "缺少切换", "长时间", "过慢", "节奏慢", "一镜到底"]},
  "structure_unclear": {"dimension": "STRUCTURE_RHYTHM", "label": "缺少段落/步骤标记", "keywords": ["步骤", "段落", "层次", "分段", "第一步"]},
  "value_late": {"dimension": "VALUE_DELIVERY", "label": "收益出现太晚", "keywords": ["太晚", "较晚", "延迟", "迟", "才出现", "才提到", "秒后"]},
  "value_unclear": {"dimension": "VALUE_DELIVERY", "label": "收益表述模糊", "keywords": ["模糊", "不明确", "不清晰", "笼统"]},
  "no_cta": {"dimension": "VALUE_DELIVERY", "label": "结尾没有行动号召", "keywords": ["行动号召", "CTA", "引导关注", "结尾没有", "缺少结尾"]},
  "no_proof": {"dimension": "VALUE_DELIVERY", "label": "没有结果证明", "keywords": ["证明", "前后对比", "效果展示", "数据", "没有展示结果"]},
}

# GAP 以外的结论使用的类型
NON_GAP_TYPES = {"strength", "parity", "evidence_gap"}
# 不在分类表里但允许的兜底类型（会在评测里单独统计）
OTHER_TYPE = "other"

# 判断"开场"相关矛盾时的开场窗口（秒）
OPENING_SECONDS = 5.0


def types_for_dimension(dimension: str) -> list[str]:
  return [key for key, meta in ISSUE_TYPES.items() if meta["dimension"] == dimension]


def is_known_type(dimension: str, finding_type: str, polarity: str) -> bool:
  if polarity != GAP:
    return finding_type in NON_GAP_TYPES or finding_type in ISSUE_TYPES or finding_type == OTHER_TYPE
  return finding_type in types_for_dimension(dimension) or finding_type == OTHER_TYPE


def taxonomy_prompt_lines() -> str:
  lines = []
  for dimension in ("HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY"):
    items = "、".join(f"{key}（{ISSUE_TYPES[key]['label']}）" for key in types_for_dimension(dimension))
    lines.append(f"- {dimension}：{items}")
  return "\n".join(lines)
