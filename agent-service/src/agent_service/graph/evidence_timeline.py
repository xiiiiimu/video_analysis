"""
v0.2 时间轴证据：把 Java 返回的 timelineJson / ocrJson / sceneJson 整理成按时间组织的视图。

Java 侧（VideoFeatureExtractor）从 v0.2 起分析前 120 秒：开场每秒一帧、之后每 3 秒一帧、
外加镜头切换帧，并提供带时间戳的语音转写。这里负责三件事：

1. ``build_video_view``：给模型的紧凑视图（时间点 + 文字分段），按维度裁剪时间窗口；
2. ``evidence_refs_for_video``：所有可以被引用的证据条目，用于校验模型是否编造引用；
3. ``has_text_evidence``：是否真的有文字证据（旧实现把 ``{"ocr":[]}`` 这种空 JSON 也当作有文字）。

引用格式（alias：目标视频为 T，参考视频依次为 R1、R2 ...）：
- ``FRAME:T@00:01:03``  某个关键帧
- ``OCR:T@00:00:06``    某段屏幕文字（时间为该段起点）
- ``ASR:T@00:00:12``    某段口播转写（时间为该段起点）
- ``SCENE:T#3``         第 3 个镜头
- ``ASR:<videoAssetId>`` / ``OCR:<videoAssetId>`` / ``METADATA:<videoAssetId>`` / ``FRAME:<videoAssetId>``
  视频级引用，与旧版本兼容。

没有 timelineJson 的旧数据（featureVersion 0.1.0）走 legacy 视图，行为与改造前一致。
"""

from __future__ import annotations

import json
import re
from typing import Any

TARGET_ALIAS = "T"


def reference_alias(index: int) -> str:
  return f"R{index + 1}"


def parse_json_field(value: Any) -> Any:
  if isinstance(value, (dict, list)):
    return value
  if not isinstance(value, str) or not value.strip():
    return None
  try:
    return json.loads(value)
  except (json.JSONDecodeError, ValueError):
    return None


def parse_timeline(video: dict[str, Any]) -> dict[str, Any] | None:
  timeline = parse_json_field(video.get("timelineJson"))
  return timeline if isinstance(timeline, dict) else None


def ocr_items(video: dict[str, Any]) -> list[dict[str, Any]]:
  parsed = parse_json_field(video.get("ocrJson"))
  if isinstance(parsed, dict):
    return [item for item in parsed.get("ocr") or [] if isinstance(item, dict) and str(item.get("text") or "").strip()]
  return []


def transcript_segments(video: dict[str, Any]) -> list[dict[str, Any]]:
  timeline = parse_timeline(video) or {}
  transcript = timeline.get("transcript") or {}
  return [item for item in transcript.get("segments") or [] if isinstance(item, dict) and str(item.get("text") or "").strip()]


def scene_items(video: dict[str, Any]) -> list[dict[str, Any]]:
  parsed = parse_json_field(video.get("sceneJson"))
  if isinstance(parsed, dict):
    return [item for item in parsed.get("scenes") or [] if isinstance(item, dict)]
  return []


def has_text_evidence(video: dict[str, Any]) -> bool:
  """转写或屏幕文字里至少有一条非空内容。"""
  if str(video.get("transcriptText") or "").strip():
    return True
  raw_ocr = video.get("ocrJson")
  parsed = parse_json_field(raw_ocr)
  if parsed is None:
    # 非 JSON 的纯文本 OCR（测试 / 旧数据）：非空即视为有文字
    return bool(str(raw_ocr or "").strip())
  return bool(ocr_items(video))


def _seconds(item: dict[str, Any], key: str, fallback_key: str) -> float:
  value = item.get(key)
  if isinstance(value, (int, float)):
    return float(value)
  return _parse_timestamp(str(item.get(fallback_key) or ""))


def _parse_timestamp(text: str) -> float:
  parts = text.strip().split(":")
  try:
    numbers = [float(part) for part in parts]
  except ValueError:
    return 0.0
  total = 0.0
  for number in numbers:
    total = total * 60 + number
  return total


def _in_window(start: float, end: float, window: tuple[float, float] | None) -> bool:
  if window is None:
    return True
  return start < window[1] and end > window[0]


def _clip_text(text: str, limit: int) -> tuple[str, bool]:
  text = " ".join(str(text or "").split())
  if len(text) <= limit:
    return text, False
  return text[:limit] + "…", True


def build_video_view(
  video: dict[str, Any],
  alias: str,
  *,
  window: tuple[float, float] | None,
  max_keyframes: int,
  max_segments: int,
  segment_chars: int,
  truncation: dict[str, Any],
  field_prefix: str,
) -> dict[str, Any] | None:
  """
  时间轴视图；没有 timelineJson 时返回 None，由调用方走 legacy 视图。

  关键帧只给时间点（模型看不到图片，给 URL 只会浪费 token），引用时按 ``FRAME:<alias>@<time>`` 拼。
  """
  timeline = parse_timeline(video)
  if timeline is None:
    return None

  frames = []
  for frame in timeline.get("keyframes") or []:
    if not isinstance(frame, dict):
      continue
    seconds = _seconds(frame, "seconds", "time")
    if _in_window(seconds, seconds + 0.01, window):
      frames.append({"time": str(frame.get("time") or ""), "s": _sec_label(seconds), "reason": str(frame.get("reason") or "")})
  if len(frames) > max_keyframes:
    truncation[f"{field_prefix}.keyframes"] = {"originalCount": len(frames), "keptCount": max_keyframes}
    frames = _even_sample(frames, max_keyframes)

  def segments(items: list[dict[str, Any]], field: str, kind: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    clipped = 0
    for item in items:
      start = _seconds(item, "startSeconds", "time" if "time" in item else "start")
      end = _seconds(item, "endSeconds", "end")
      if not _in_window(start, max(end, start + 0.01), window):
        continue
      text, was_clipped = _clip_text(str(item.get("text") or ""), segment_chars)
      clipped += int(was_clipped)
      start_label = str(item.get("time") or item.get("start") or "")
      # 直接给出可复制的引用 + 秒数：模型曾把 00:01:05 读成"第 5 秒"
      rows.append({"ref": f"{kind}:{alias}@{start_label}", "s": f"{_sec_label(start)}-{_sec_label(max(end, start))}", "text": text})
    if len(rows) > max_segments:
      truncation[f"{field_prefix}.{field}"] = {"originalCount": len(rows), "keptCount": max_segments}
      rows = _even_sample(rows, max_segments)
    if clipped:
      truncation.setdefault(f"{field_prefix}.{field}.textClipped", {"segments": clipped, "charLimit": segment_chars})
    return rows

  scenes = []
  for scene in scene_items(video):
    start = _seconds(scene, "startSeconds", "start")
    end = _seconds(scene, "endSeconds", "end")
    if _in_window(start, max(end, start + 0.01), window):
      scenes.append(
        {
          "ref": f"SCENE:{alias}#{scene.get('index')}",
          "s": f"{_sec_label(start)}-{_sec_label(end)}",
          "len": scene.get("durationSeconds"),
        }
      )

  transcript = timeline.get("transcript") or {}
  view = {
    "alias": alias,
    "videoAssetId": video.get("videoAssetId"),
    "coverage": {
      "durationSeconds": timeline.get("durationSeconds"),
      "analyzedSeconds": timeline.get("analyzedSeconds"),
      "truncated": bool(timeline.get("truncated")),
      "window": list(window) if window else None,
    },
    "keyframeTimes": frames,
    "sceneStats": scene_stats(video, alias, window),
    "scenes": scenes,
    "screenText": segments(ocr_items(video), "screenText", "OCR"),
    "speech": segments(transcript_segments(video), "speech", "ASR"),
    "speechStatus": transcript.get("status") or "unknown",
  }
  if timeline.get("truncated"):
    truncation.setdefault(
      f"{field_prefix}.coverage",
      {"analyzedSeconds": timeline.get("analyzedSeconds"), "durationSeconds": timeline.get("durationSeconds")},
    )
  return view


def _sec_label(seconds: float) -> str:
  value = round(float(seconds), 1)
  return f"{int(value)}" if value == int(value) else f"{value}"


def scene_stats(video: dict[str, Any], alias: str, window: tuple[float, float] | None = None) -> dict[str, Any] | None:
  """
  镜头统计（系统计算，引用 METADATA:<alias>）。让模型直接比较数字，不用自己从几十个镜头里数：
  镜头数、平均 / 中位 / 最长镜头时长、2 秒以内的短镜头数、每 30 秒的切换次数。
  """
  rows = []
  for scene in scene_items(video):
    start = _seconds(scene, "startSeconds", "start")
    end = _seconds(scene, "endSeconds", "end")
    if _in_window(start, max(end, start + 0.01), window):
      rows.append((start, max(end, start), scene.get("index")))
  if not rows:
    return None
  durations = [end - start for start, end, _ in rows]
  longest = max(rows, key=lambda row: row[1] - row[0])
  span_end = max(end for _, end, _ in rows)
  buckets = []
  bucket_start = rows[0][0] if window else 0.0
  while bucket_start < span_end - 0.01:
    bucket_end = bucket_start + 30
    cuts = sum(1 for start, _, _ in rows[1:] if bucket_start <= start < bucket_end)
    buckets.append({"s": f"{_sec_label(bucket_start)}-{_sec_label(min(bucket_end, span_end))}", "cuts": cuts})
    bucket_start = bucket_end
  ordered = sorted(durations)
  middle = len(ordered) // 2
  median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
  return {
    "ref": f"METADATA:{alias}",
    "shotCount": len(rows),
    "avgShotSeconds": round(sum(durations) / len(durations), 1),
    "medianShotSeconds": round(median, 1),
    "longestShot": {"ref": f"SCENE:{alias}#{longest[2]}", "seconds": round(longest[1] - longest[0], 1)},
    "shotsUnder2s": sum(1 for value in durations if value < 2),
    "cutsPer30s": buckets,
  }


def _even_sample(rows: list[Any], limit: int) -> list[Any]:
  if limit <= 0:
    return []
  if len(rows) <= limit:
    return rows
  stride = len(rows) / limit
  return [rows[min(len(rows) - 1, int(index * stride))] for index in range(limit)]


def evidence_refs_for_video(video: dict[str, Any], alias: str) -> set[str]:
  """该视频所有可以被引用的证据条目（含旧格式）。"""
  asset_id = str(video.get("videoAssetId") or alias)
  refs: set[str] = {f"FRAME:{asset_id}", f"FRAME:{alias}"}
  for frame in video.get("keyframes") or []:
    if isinstance(frame, dict):
      refs.update(str(value) for key, value in frame.items() if key in {"ref", "id", "timestamp", "url", "time"} and value)
    else:
      refs.add(str(frame))
  if str(video.get("transcriptText") or "").strip():
    refs.update({f"ASR:{asset_id}", f"ASR:{alias}"})
  if has_text_evidence(video) and video.get("ocrJson"):
    refs.update({f"OCR:{asset_id}", f"OCR:{alias}"})
  if video.get("sceneJson"):
    refs.update({f"METADATA:{asset_id}", f"METADATA:{alias}"})

  timeline = parse_timeline(video)
  if timeline:
    for frame in timeline.get("keyframes") or []:
      if isinstance(frame, dict) and frame.get("time"):
        refs.add(f"FRAME:{alias}@{frame['time']}")
        refs.add(f"FRAME:{asset_id}@{frame['time']}")
    for item in transcript_segments(video):
      if item.get("start"):
        refs.add(f"ASR:{alias}@{item['start']}")
  for item in ocr_items(video):
    if item.get("time"):
      refs.add(f"OCR:{alias}@{item['time']}")
  for scene in scene_items(video):
    if scene.get("index") is not None:
      refs.add(f"SCENE:{alias}#{scene['index']}")
  return {ref.strip() for ref in refs if ref and ref.strip()}


def video_aliases(evidence_pack: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
  videos: list[tuple[str, dict[str, Any]]] = [(TARGET_ALIAS, evidence_pack.get("targetEvidence") or {})]
  for index, ref in enumerate(evidence_pack.get("referenceEvidence") or []):
    videos.append((reference_alias(index), ref or {}))
  return videos


def window_for_dimension(dimension: str, hook_window_seconds: int) -> tuple[float, float] | None:
  if dimension == "HOOK":
    return (0.0, float(hook_window_seconds))
  return None


_TIME_REF = re.compile(r"^(FRAME|OCR|ASR):([A-Za-z0-9_-]+)@(\d{1,2}:\d{2}:\d{2})$")
_SCENE_REF = re.compile(r"^SCENE:([A-Za-z0-9_-]+)#(\d+)$")
FRAME_TOLERANCE_SECONDS = 1.5


def is_time_level_ref(ref: str) -> bool:
  return bool(_TIME_REF.match(ref) or _SCENE_REF.match(ref))


def time_ref_is_grounded(ref: str, evidence_pack: dict[str, Any]) -> bool:
  """
  时间级引用必须落在真实证据上（不能用宽松的子串匹配，否则 FRAME:T@00:05:00 会因为包含 "FRAME:T" 被放行）：
  - FRAME：与某个关键帧相差不超过 1.5 秒；
  - OCR / ASR：时间点落在某个分段 [start, end] 内（允许 1 秒误差）；
  - SCENE：镜头序号存在。
  """
  videos = {alias: video for alias, video in video_aliases(evidence_pack)}
  for alias, video in list(videos.items()):
    asset_id = str(video.get("videoAssetId") or "")
    if asset_id:
      videos.setdefault(asset_id, video)

  scene_match = _SCENE_REF.match(ref)
  if scene_match:
    video = videos.get(scene_match.group(1))
    if not video:
      return False
    return any(str(scene.get("index")) == scene_match.group(2) for scene in scene_items(video))

  match = _TIME_REF.match(ref)
  if not match:
    return False
  kind, key, stamp = match.groups()
  video = videos.get(key)
  if not video:
    return False
  at = _parse_timestamp(stamp)
  if kind == "FRAME":
    timeline = parse_timeline(video) or {}
    return any(
      abs(_seconds(frame, "seconds", "time") - at) <= FRAME_TOLERANCE_SECONDS
      for frame in timeline.get("keyframes") or []
      if isinstance(frame, dict)
    )
  items = ocr_items(video) if kind == "OCR" else transcript_segments(video)
  for item in items:
    start = _seconds(item, "startSeconds", "time" if "time" in item else "start")
    end = _seconds(item, "endSeconds", "end")
    if start - 1.0 <= at <= max(end, start) + 1.0:
      return True
  return False


_QUOTE_REF = re.compile(r"^(ASR|OCR):([A-Za-z0-9_-]+)(?:@(\d{1,2}:\d{2}:\d{2}))?$")
MIN_QUOTE_CHARS = 4
QUOTE_TIME_TOLERANCE_SECONDS = 3.0


def normalize_text(text: str) -> str:
  """去掉空白和标点，只保留文字和数字，用于逐字引用比对（OCR / 转写的标点不稳定）。"""
  return re.sub(r"[\W_]+", "", str(text or "")).lower()


def _quote_sources(video: dict[str, Any], kind: str) -> list[tuple[float, float, str]]:
  if kind == "ASR":
    rows = [
      (_seconds(item, "startSeconds", "start"), _seconds(item, "endSeconds", "end"), str(item.get("text") or ""))
      for item in transcript_segments(video)
    ]
    if not rows and str(video.get("transcriptText") or "").strip() and parse_timeline(video) is None:
      rows = [(0.0, 1e9, str(video["transcriptText"]))]  # legacy：没有分段时间
    return rows
  rows = [
    (_seconds(item, "startSeconds", "time"), _seconds(item, "endSeconds", "end"), str(item.get("text") or ""))
    for item in ocr_items(video)
  ]
  raw = video.get("ocrJson")
  if not rows and isinstance(raw, str) and raw.strip() and parse_json_field(raw) is None:
    rows = [(0.0, 1e9, raw)]
  return rows


def ground_quotes(
  quotes: list[dict[str, str]],
  evidence_pack: dict[str, Any],
) -> tuple[list[dict[str, str]], list[str]]:
  """
  校验模型的逐字引用：原文必须真实出现在对应视频的口播 / 屏幕文字里（忽略标点和空白）。
  时间点允许 ±3 秒误差；ref 写错但原文在某个视频里真实存在时，按实际位置修正 ref。
  返回 (校验通过的引用, 问题列表)。
  """
  videos = dict(video_aliases(evidence_pack))
  grounded: list[dict[str, str]] = []
  issues: list[str] = []
  for quote in quotes or []:
    text = str(quote.get("text") or "")
    needle = normalize_text(text)
    if len(needle) < MIN_QUOTE_CHARS:
      issues.append(f"引用过短：「{text}」")
      continue
    ref = str(quote.get("ref") or "")
    match = _QUOTE_REF.match(ref)
    candidates: list[tuple[str, str, dict[str, Any], float | None]] = []
    if match and match.group(2) in videos:
      at = _parse_timestamp(match.group(3)) if match.group(3) else None
      candidates.append((match.group(1), match.group(2), videos[match.group(2)], at))
    for alias, video in videos.items():
      for kind in ("ASR", "OCR"):
        if not (match and match.group(1) == kind and match.group(2) == alias):
          candidates.append((kind, alias, video, None))

    found = None
    for kind, alias, video, at in candidates:
      for start, end, segment in _quote_sources(video, kind):
        if at is not None and not (start - QUOTE_TIME_TOLERANCE_SECONDS <= at <= max(end, start) + QUOTE_TIME_TOLERANCE_SECONDS):
          continue
        if needle in normalize_text(segment):
          stamp = _format_ts(start) if start < 1e8 else ""
          found = {"ref": f"{kind}:{alias}@{stamp}" if stamp else f"{kind}:{alias}", "text": text}
          break
      if found:
        break
    if found:
      if ref and found["ref"] != ref:
        issues.append(f"引用位置已修正：{ref} → {found['ref']}")
      grounded.append(found)
    else:
      issues.append(f"原文在证据中找不到：「{text}」（{ref or '无 ref'}）")
  return grounded, issues


def opening_quotes(quotes: list[dict[str, str]], alias: str = TARGET_ALIAS, opening_seconds: float = 5.0) -> list[dict[str, str]]:
  """落在目标视频开场窗口内的引用。"""
  rows = []
  for quote in quotes or []:
    match = _QUOTE_REF.match(str(quote.get("ref") or ""))
    if match and match.group(2) == alias and match.group(3) and _parse_timestamp(match.group(3)) <= opening_seconds:
      rows.append(quote)
  return rows


def _format_ts(seconds: float) -> str:
  total = int(max(0, seconds))
  return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def opening_text(video: dict[str, Any], seconds: float = 5.0, channels: tuple[str, ...] = ("speech", "screen")) -> str:
  """开场 N 秒内的口播 / 屏幕文字（规整后），用于判断目标与参考的开场是否实质相同。"""
  parts: list[str] = []
  if "speech" in channels:
    for item in transcript_segments(video):
      if _seconds(item, "startSeconds", "start") < seconds:
        parts.append(str(item.get("text") or ""))
  if "screen" in channels:
    for item in ocr_items(video):
      if _seconds(item, "startSeconds", "time") < seconds:
        parts.append(str(item.get("text") or ""))
  return normalize_text("".join(parts))


def text_similarity(left: str, right: str) -> float:
  from difflib import SequenceMatcher

  if not left or not right:
    return 0.0
  return SequenceMatcher(None, left, right).ratio()


def video_by_alias(evidence_pack: dict[str, Any], alias: str) -> dict[str, Any] | None:
  return dict(video_aliases(evidence_pack)).get(alias)
