from __future__ import annotations

import json
from typing import Any

from agent_service.graph.diagnosis_skill import _invalid_cited_refs, known_evidence_refs
from agent_service.graph.evidence_timeline import has_text_evidence
from agent_service.llm.diagnosis_llm import _build_user_payload


def _ts(seconds: float) -> str:
  total = int(seconds)
  return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def _video(asset_id: str, duration: float = 150.0) -> dict[str, Any]:
  window = min(duration, 120.0)
  times = [0, 1, 2, 3, 4] + [5 + 3 * i for i in range(39)] + [119.5]
  keyframes = [
    {"index": i + 1, "time": _ts(t), "seconds": t, "reason": "hook" if t < 5 else "interval", "url": f"http://minio/f{i}.jpg"}
    for i, t in enumerate(times)
  ]
  ocr = [
    {"frameIndex": 1, "time": "00:00:00", "end": "00:00:03", "startSeconds": 0, "endSeconds": 3, "text": "3个技巧让早餐快一倍"},
    {"frameIndex": 20, "time": "00:01:03", "end": "00:01:09", "startSeconds": 63, "endSeconds": 69, "text": "第二步 提前备料"},
  ]
  scenes = {
    "detected": True,
    "durationSeconds": duration,
    "analyzedSeconds": window,
    "scenes": [
      {"index": 1, "start": "00:00:00", "end": "00:00:07", "startSeconds": 0, "endSeconds": 7.4, "durationSeconds": 7.4},
      {"index": 2, "start": "00:00:07", "end": "00:01:30", "startSeconds": 7.4, "endSeconds": 90, "durationSeconds": 82.6},
      {"index": 3, "start": "00:01:30", "end": "00:02:00", "startSeconds": 90, "endSeconds": 120, "durationSeconds": 30},
    ],
  }
  segments = [
    {"start": "00:00:01", "end": "00:00:04", "startSeconds": 1, "endSeconds": 4, "text": "今天教你三个让早餐快一倍的技巧"},
    {"start": "00:00:40", "end": "00:00:46", "startSeconds": 40, "endSeconds": 46, "text": "第一步把鸡蛋提前煮好"},
  ]
  timeline = {
    "version": "0.2.0",
    "durationSeconds": duration,
    "analyzedSeconds": window,
    "truncated": duration > 120,
    "keyframes": keyframes,
    "transcript": {"status": "ok", "model": "whisper-1", "segments": segments},
  }
  return {
    "videoAssetId": asset_id,
    "transcriptText": " ".join(item["text"] for item in segments),
    "keyframes": [item["url"] for item in keyframes],
    "sceneJson": json.dumps(scenes, ensure_ascii=False),
    "ocrJson": json.dumps({"ocr": ocr}, ensure_ascii=False),
    "timelineJson": json.dumps(timeline, ensure_ascii=False),
  }


def _pack() -> dict[str, Any]:
  return {"targetEvidence": _video("target-1"), "referenceEvidence": [_video("ref-1", duration=90)]}


def test_hook_payload_only_contains_opening_window() -> None:
  payload = _build_user_payload("HOOK", {"jobId": "j"}, _pack())
  target = payload["target"]

  assert target["alias"] == "T"
  assert target["coverage"]["window"] == [0.0, 15.0]
  assert all(frame["time"] <= "00:00:15" for frame in target["keyframeTimes"])
  assert [item["text"] for item in target["screenText"]] == ["3个技巧让早餐快一倍"]
  assert [item["text"] for item in target["speech"]] == ["今天教你三个让早餐快一倍的技巧"]
  assert "url" not in json.dumps(target["keyframeTimes"])  # 模型看不到图片，不发 URL


def test_structure_payload_covers_two_minutes_and_marks_truncation() -> None:
  payload = _build_user_payload("STRUCTURE_RHYTHM", {"jobId": "j"}, _pack())
  target = payload["target"]

  assert target["coverage"]["window"] is None
  assert target["keyframeTimes"][-1]["time"] == "00:01:59"
  assert len(target["scenes"]) == 3
  second = next(item for item in target["screenText"] if item["ref"] == "OCR:T@00:01:03")
  assert second["s"] == "63-69"  # 秒数直接给出，避免模型把 00:01:03 读成第 3 秒
  stats = target["sceneStats"]
  assert stats["ref"] == "METADATA:T" and stats["shotCount"] == 3
  assert stats["longestShot"] == {"ref": "SCENE:T#2", "seconds": 82.6}
  assert [bucket["cuts"] for bucket in stats["cutsPer30s"]] == [1, 0, 0, 1]
  assert payload["truncation"]["target.coverage"] == {"analyzedSeconds": 120.0, "durationSeconds": 150.0}
  assert payload["references"][0]["alias"] == "R1"
  assert "target.coverage" in payload["truncation"] and "references[0].coverage" not in payload["truncation"]


def test_two_minute_payload_stays_compact() -> None:
  payload = _build_user_payload("VALUE_DELIVERY", {"jobId": "j"}, _pack())
  # 2 个视频、每个 45 帧：只发时间点不发 URL，整体控制在 ~10k 字符以内
  assert len(json.dumps(payload, ensure_ascii=False)) < 10000


def test_time_level_refs_are_known_and_invented_ones_rejected() -> None:
  pack = _pack()
  known = known_evidence_refs(pack)

  for ref in ("FRAME:T@00:01:05", "OCR:T@00:01:03", "ASR:T@00:00:40", "SCENE:R1#2", "ASR:target-1", "OCR:ref-1"):
    assert ref in known

  hypothesis = {
    "target_frame_refs": ["FRAME:T@00:01:05", "FRAME:T@00:05:00"],
    "reference_frame_refs": ["SCENE:R1#2"],
    "evidence_refs": ["ASR:T@00:00:40", "SCENE:T#9"],
  }
  assert _invalid_cited_refs(hypothesis, pack, []) == ["FRAME:T@00:05:00", "SCENE:T#9"]


def test_empty_ocr_json_is_not_text_evidence() -> None:
  assert not has_text_evidence({"transcriptText": "", "ocrJson": '{"ocr":[]}'})
  assert has_text_evidence({"transcriptText": "", "ocrJson": "plain ocr text"})
  assert has_text_evidence({"transcriptText": "口播", "ocrJson": '{"ocr":[]}'})


def test_legacy_evidence_without_timeline_keeps_old_shape() -> None:
  legacy = {"videoAssetId": "old", "transcriptText": "hi", "keyframes": ["00:00:00-00:00:05"], "ocrJson": "text", "sceneJson": "{}"}
  payload = _build_user_payload("HOOK", {}, {"targetEvidence": legacy, "referenceEvidence": []})

  assert payload["target"]["keyframes"] == ["00:00:00-00:00:05"]
  assert payload["target"]["transcript"] == "hi"
  assert "00:00:00-00:00:05" in known_evidence_refs({"targetEvidence": legacy})
