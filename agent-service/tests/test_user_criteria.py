"""用户上传评分标准：拆分归类、交给对应专家、逐条回应检查、补充分析节点、报告输出。"""

from __future__ import annotations

import json
from typing import Any

import pytest

from agent_service.config import get_settings
from agent_service.eval.quality_benchmark import aggregate, run_case
from agent_service.eval.quality_cases import build_cases
from agent_service.graph.criteria import (
  MAX_CRITERIA,
  build_criteria_report,
  criteria_input,
  parse_user_criteria,
  render_report_markdown,
)
from agent_service.graph.nodes.evaluator import _criteria_issues
from agent_service.graph.supplementary import _grounded_notes, needs_supplementary

CASES = {case.case_id: case for case in build_cases()}


def test_split_handles_numbering_headings_and_semicolons() -> None:
  text = "开场：\n1. 开头3秒说出卖点；不要先自我介绍\n结构：\n- 每一步配字幕\n\n其他：\n（1）不能出现竞品名字"
  items = parse_user_criteria(text, use_llm=False)
  assert [item["text"] for item in items] == ["开头3秒说出卖点", "不要先自我介绍", "每一步配字幕", "不能出现竞品名字"]
  assert [item["id"] for item in items] == ["U1", "U2", "U3", "U4"]
  assert [item["dimension"] for item in items] == ["HOOK", "HOOK", "STRUCTURE_RHYTHM", "OTHER"]
  assert all(item["classifiedBy"] == "keywords" for item in items)


def test_split_caps_the_number_of_criteria() -> None:
  items = parse_user_criteria("\n".join(f"{i}. 结尾引导关注第{i}条" for i in range(1, 60)), use_llm=False)
  assert len(items) == MAX_CRITERIA


def test_criteria_input_reads_the_job_snapshot() -> None:
  snapshot = json.dumps({"criteriaText": "结尾引导关注", "supplementaryAnalysis": True}, ensure_ascii=False)
  assert criteria_input({"inputSnapshotJson": snapshot}) == ("结尾引导关注", True)
  assert criteria_input({"inputSnapshotJson": "not json"}) == ("", False)
  assert criteria_input({}) == ("", False)


def test_supplementary_runs_only_for_other_criteria_or_when_requested() -> None:
  hook_only = {"user_criteria": [{"id": "U1", "dimension": "HOOK"}]}
  assert not needs_supplementary(hook_only)
  assert needs_supplementary({**hook_only, "supplementary_analysis": True})
  assert needs_supplementary({"user_criteria": [{"id": "U1", "dimension": "OTHER"}]})


def test_supplementary_notes_without_grounded_quotes_are_dropped() -> None:
  pack = CASES["c01_hook_no_promise"].evidence_pack()
  notes, dropped = _grounded_notes(
    [
      {"title": "有依据", "observation": "目标开场是寒暄", "quotes": [{"ref": "ASR:T@00:00:00", "text": "大家好，我是小王"}]},
      {"title": "编的", "observation": "背景音乐很吵", "quotes": [{"ref": "ASR:T@00:00:00", "text": "背景音乐太吵了"}]},
    ],
    pack,
  )
  assert [note["title"] for note in notes] == ["有依据"] and dropped == 1


@pytest.mark.quality_v2
def test_evaluator_requires_every_assigned_criterion_to_be_answered() -> None:
  issues = _criteria_issues({"skill_key": "hook_analysis", "missing_criteria_ids": ["U2"]})
  assert len(issues) == 1 and "U2" in issues[0][2]
  assert _criteria_issues({"skill_key": "hook_analysis", "missing_criteria_ids": []}) == []


def test_report_marks_unanswered_criteria_as_not_covered() -> None:
  criteria = parse_user_criteria("1. 开头3秒说出卖点\n2. 不能出现竞品名字", use_llm=False)
  findings = [{"skill_key": "hook_analysis", "dimension": "HOOK", "outcome": "FINDING", "polarity": "GAP",
               "observation": "开场寒暄", "criteria_verdicts": [{"id": "U1", "verdict": "NOT_MET", "reason": "前 6 秒是寒暄"}]}]
  report = build_criteria_report(criteria, findings, None)
  assert [(row["id"], row["verdictLabel"]) for row in report] == [("U1", "不满足"), ("U2", "未覆盖")]
  markdown = render_report_markdown({"summary": "总结", "criteria": criteria, "criteriaReport": report}, findings)
  assert "## 解析出的评分标准" in markdown and "## 逐条对照" in markdown and "未覆盖 1" in markdown


@pytest.mark.rag
@pytest.mark.quality_v2
def test_end_to_end_criteria_reach_the_right_nodes_and_the_report(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setenv("LLM_MOCK", "1")
  get_settings.cache_clear()
  from agent_service.llm import diagnosis_llm

  payloads: list[dict[str, Any]] = []
  original = diagnosis_llm._build_user_payload

  def spy(dimension: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = original(dimension, *args, **kwargs)
    payloads.append(payload)
    return payload

  monkeypatch.setattr(diagnosis_llm, "_build_user_payload", spy)
  run = run_case(CASES["cc2_criteria_overall"])

  assert run["status"] == "success"
  # 每个专家只拿到分给自己的标准
  by_dimension = {payload["dimension"]: payload for payload in payloads}
  assert [item["id"] for item in by_dimension["HOOK"]["userCriteria"]] == ["U1"]
  assert [item["id"] for item in by_dimension["STRUCTURE_RHYTHM"]["userCriteria"]] == ["U2"]
  assert "userCriteria" not in by_dimension["VALUE_DELIVERY"]
  synthesis = run["synthesis"]
  assert [item["dimension"] for item in synthesis["criteria"]] == ["HOOK", "STRUCTURE_RHYTHM", "OTHER"]
  assert synthesis["supplementary"]["mode"] == "overall"
  assert synthesis["supplementary"]["criteriaIds"] == ["U3"]
  assert all(row["verdictLabel"] != "未覆盖" for row in synthesis["criteriaReport"])
  assert "## 逐条对照" in synthesis["reportMarkdown"]
  summary = aggregate([run])
  assert summary["criteriaSplitAccuracy"] == 1.0 and summary["criteriaDimensionAccuracy"] == 1.0
  assert summary["criteriaCoverage"] == 1.0


@pytest.mark.quality_v2
def test_jobs_without_criteria_are_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setenv("LLM_MOCK", "1")
  get_settings.cache_clear()
  run = run_case(CASES["c01_hook_no_promise"])
  assert run["status"] == "success"
  assert run["synthesis"]["criteria"] == [] and run["synthesis"]["supplementary"] == {}
  assert "解析出的评分标准" not in run["synthesis"]["reportMarkdown"]


class _Resp:
  def __init__(self, content: str) -> None:
    self.content = content


def test_llm_splits_free_text_and_bad_rows_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
  """用户写的是一整段话：由模型拆分 + 归类；维度写错的条目用关键词兜底，原文不在用户文字里的标记 verbatim=False。"""
  from agent_service.graph.criteria import parse_with_llm

  text = "我希望开头三秒就讲清楚卖点，中间别拖沓，最后一定要引导大家去直播间，还有千万别提竞品。"
  answer = {"items": [
    {"text": "开头三秒就讲清楚卖点", "dimension": "HOOK", "check": "前 3 秒口播或字幕说出卖点"},
    {"text": "中间别拖沓", "dimension": "STRUCTURE_RHYTHM", "check": "中段没有长时间无信息"},
    {"text": "最后一定要引导大家去直播间", "dimension": "价值", "check": "结尾引导去直播间"},
    {"text": "不要提及任何竞争对手", "dimension": "OTHER", "check": "全片不出现竞品名"},
    {"text": "", "dimension": "OTHER"},
  ]}
  items = parse_with_llm(text, lambda messages: _Resp(json.dumps(answer, ensure_ascii=False)))
  assert [item["dimension"] for item in items] == ["HOOK", "STRUCTURE_RHYTHM", "VALUE_DELIVERY", "OTHER"]
  assert [item["classifiedBy"] for item in items] == ["llm", "llm", "keywords", "llm"]
  assert [item["verbatim"] for item in items] == [True, True, True, False]


def test_llm_parse_failure_falls_back_to_rules(monkeypatch: pytest.MonkeyPatch) -> None:
  class Broken:
    def invoke(self, messages: Any) -> Any:
      raise RuntimeError("boom")

  monkeypatch.setattr("agent_service.llm.provider.get_chat_model", lambda: Broken())
  items = parse_user_criteria("1. 开头3秒说出卖点\n2. 结尾引导关注", use_llm=True)
  assert [item["splitBy"] for item in items] == ["rules", "rules"]
  assert [item["id"] for item in items] == ["U1", "U2"]


def test_unmet_user_criteria_come_first_and_summary_states_them() -> None:
  """真实任务：价值传递整体强于参考（判为优势），但用户标准"结尾必须引导关注"没满足，总结却写"没有需要优先改进的问题"。"""
  from agent_service.graph.criteria import apply_criteria_to_synthesis
  from agent_service.graph.synthesis import assign_priorities

  report = [
    {"id": "U1", "text": "开头3秒说出收益", "check": "c1", "dimension": "HOOK", "verdict": "MET", "reason": "r", "suggestion": ""},
    {"id": "U2", "text": "结尾必须引导关注", "check": "结尾出现关注引导", "dimension": "VALUE_DELIVERY", "verdict": "NOT_MET",
     "reason": "第 88.9 秒直接结束", "suggestion": "第 86 秒补一句'关注我'并配字幕"},
    {"id": "U3", "text": "不能出现竞品", "check": "c3", "dimension": "OTHER", "verdict": "UNKNOWN", "reason": "r", "suggestion": ""},
  ]
  base = {"summary": "目标视频在已诊断的维度上不弱于参考视频，没有需要优先改进的问题。", "priorities": [], "mergedActions": []}
  synthesis = apply_criteria_to_synthesis(base, report)
  assert synthesis["summary"].startswith("你的 3 条标准：满足 1 条，不满足 1 条（U2 结尾必须引导关注），无法判断 1 条")
  assert "没有需要优先改进的问题" not in synthesis["summary"]
  assert synthesis["priorities"][0]["criterionId"] == "U2" and synthesis["priorities"][0]["rank"] == 1
  assert synthesis["priorities"][0]["suggestedAction"] == "第 86 秒补一句'关注我'并配字幕"
  assert synthesis["criteriaSummary"] == {"total": 3, "met": 1, "notMet": 1, "unknown": 1}

  # 有维度差距时：用户标准排第 1，维度差距顺延为第 2（Java 侧优先级 P1）
  with_gap = {"summary": "s", "priorities": [{"rank": 1, "skillKey": "structure_rhythm_analysis", "dimension": "STRUCTURE_RHYTHM",
                                               "suggestedAction": "a"}], "mergedActions": ["a"]}
  merged = apply_criteria_to_synthesis(with_gap, report)
  assert [item["rank"] for item in merged["priorities"]] == [1, 2]
  finding = {"skill_key": "structure_rhythm_analysis", "dimension": "STRUCTURE_RHYTHM"}
  assert assign_priorities([finding], merged)[0]["priority"] == "P1"
  markdown = render_report_markdown({**merged, "criteria": [], "criteriaReport": report}, [])
  assert "1. 【你的标准 U2】第 86 秒补一句'关注我'并配字幕" in markdown


def test_criteria_needing_visuals_or_audio_are_marked_and_not_overclaimed() -> None:
  """系统看不到画面、听不到背景音乐：部分可查的标注局限，完全不可查的不交给节点，直接标"无法判断"。"""
  from agent_service.graph.criteria import (
    NONE_REASON,
    criteria_for_dimension,
    criterion_payload,
    parse_with_llm,
  )

  answer = {"items": [
    {"text": "不能出现竞品", "dimension": "OTHER", "check": "口播和字幕不出现竞品名", "observability": "partial"},
    {"text": "背景音乐要轻快", "dimension": "OTHER", "check": "背景音乐节奏轻快", "observability": "none"},
    {"text": "结尾引导关注", "dimension": "VALUE_DELIVERY", "check": "结尾口播或字幕引导关注"},
  ]}
  raw = parse_with_llm("不能出现竞品；背景音乐要轻快；结尾引导关注", lambda messages: _Resp(json.dumps(answer, ensure_ascii=False)))
  assert [item["observability"] for item in raw] == ["partial", "none", "full"]

  # 走完整入口（含补全检查口径的局限说明）：用规则兜底时，涉及 logo 的标准保守标为 partial
  rules = parse_user_criteria("1. 不能出现竞品的logo\n2. 结尾引导关注", use_llm=False)
  assert rules[0]["observability"] == "partial" and rules[0]["check"].endswith("（画面 / 音频部分无法检查）")
  assert "limitation" in criterion_payload(rules[0]) and "limitation" not in criterion_payload(rules[1])

  criteria = [{**item, "id": f"U{i}", "dimensionLabel": "", "observabilityLabel": ""} for i, item in enumerate(raw, start=1)]
  assert [item["id"] for item in criteria_for_dimension(criteria, "OTHER")] == ["U1"]  # U2 不交给补充节点
  assert not needs_supplementary({"user_criteria": [criteria[1]]})
  report = build_criteria_report(criteria, [], {"verdicts": [{"id": "U1", "verdict": "MET", "reason": "口播字幕未出现，画面未检查"}]})
  assert report[1]["verdict"] == "UNKNOWN" and report[1]["reason"] == NONE_REASON
  markdown = render_report_markdown({"criteria": criteria, "criteriaReport": report}, [])
  assert "满足（仅依据口播和字幕）" in markdown and "无法检查（需要看画面或听音频）" in markdown
