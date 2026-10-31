from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from agent_service.knowledge import default_video_diagnosis_corpus, load_benchmark_corpus
from agent_service.retrieval.benchmark import (
  GoldenQueryCase,
  load_query_dataset,
)
from agent_service.retrieval.hybrid import InMemoryHybridKnowledgeRetriever
from agent_service.retrieval.models import KnowledgeEvidence, KnowledgeQuery

ReviewInput = Callable[[str], str]

DEFAULT_OUTPUT_NAME = "retrieval_golden_verified.v0.3.json"
VALID_DIFFICULTIES: set[str] = {"EXACT", "SEMANTIC", "MIXED", "EASY", "MEDIUM", "HARD", "ADVERSARIAL"}


def build_review_rows(
  cases: list[GoldenQueryCase],
  corpus: list[KnowledgeEvidence] | None = None,
) -> list[dict[str, object]]:
  corpus = corpus or default_video_diagnosis_corpus()
  corpus_by_id = {item.id: item for item in corpus}
  retriever = InMemoryHybridKnowledgeRetriever(corpus)
  return [_build_review_row(case, corpus_by_id, retriever) for case in cases]


def review_dataset(
  cases: list[GoldenQueryCase],
  *,
  input_func: ReviewInput = input,
  output_func: Callable[[str], None] = print,
  corpus: list[KnowledgeEvidence] | None = None,
) -> list[GoldenQueryCase]:
  rows = build_review_rows(cases, corpus)
  reviewed: list[GoldenQueryCase] = []
  total = len(cases)
  for index, case in enumerate(cases, start=1):
    row = rows[index - 1]
    output_func(_render_case(row, index=index, total=total))
    action = _ask_action(input_func)
    if action == "v":
      reviewed.append(replace(case, annotation_status="VERIFIED"))
    elif action == "r":
      reviewed.append(replace(case, annotation_status="REJECTED"))
    elif action == "e":
      reviewed.append(_edit_case(case, input_func=input_func, output_func=output_func))
    else:
      reviewed.append(case)
  return reviewed


def write_review_dataset(
  cases: list[GoldenQueryCase],
  output_path: str | Path,
  *,
  dataset_version: str = "video-diagnosis-rag-verified-v0.3",
) -> Path:
  target = Path(output_path)
  target.parent.mkdir(parents=True, exist_ok=True)
  payload = {
    "datasetVersion": dataset_version,
    "annotationPolicy": "Only samples explicitly marked by a human reviewer with action `v` should be VERIFIED.",
    "cases": [_case_to_external_dict(case) for case in cases],
    "reviewStats": review_stats(cases),
  }
  target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
  return target


def review_stats(cases: list[GoldenQueryCase]) -> dict[str, object]:
  verified_cases = [case for case in cases if case.annotation_status == "VERIFIED"]
  return {
    "VERIFIED": sum(1 for case in cases if case.annotation_status == "VERIFIED"),
    "REJECTED": sum(1 for case in cases if case.annotation_status == "REJECTED"),
    "PENDING": sum(1 for case in cases if case.annotation_status == "PENDING_REVIEW"),
    "verifiedBySkill": _count_by(verified_cases, "skill_code"),
    "verifiedByDifficulty": _count_by(verified_cases, "difficulty"),
  }


def print_review_stats(cases: list[GoldenQueryCase], output_func: Callable[[str], None] = print) -> None:
  stats = review_stats(cases)
  output_func("\n审核统计")
  output_func(f"- VERIFIED 数: {stats['VERIFIED']}")
  output_func(f"- REJECTED 数: {stats['REJECTED']}")
  output_func(f"- PENDING 数: {stats['PENDING']}")
  output_func(f"- 每个 skill 的 VERIFIED 数: {json.dumps(stats['verifiedBySkill'], ensure_ascii=False)}")
  output_func(f"- 每个 difficulty 的 VERIFIED 数: {json.dumps(stats['verifiedByDifficulty'], ensure_ascii=False)}")


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Interactively review retrieval golden query candidates.")
  parser.add_argument("--input", required=True, help="Path to retrieval_golden_candidates JSON or JSONL.")
  parser.add_argument("--output", help=f"Output path. Defaults to sibling {DEFAULT_OUTPUT_NAME}.")
  parser.add_argument("--dataset-version", default="video-diagnosis-rag-verified-v0.3")
  parser.add_argument(
    "--corpus-version",
    default="runtime",
    help="Corpus to use for review. Use `v0.3` for the benchmark corpus; default uses runtime MVP corpus.",
  )
  args = parser.parse_args(argv)

  input_path = Path(args.input)
  output_path = Path(args.output) if args.output else input_path.with_name(DEFAULT_OUTPUT_NAME)
  if input_path.resolve() == output_path.resolve():
    raise SystemExit("Output path must be different from input path. The review tool never overwrites the source dataset.")

  corpus = load_review_corpus(args.corpus_version)
  cases = load_query_dataset(input_path)
  dataset_version = read_dataset_version(input_path)
  missing_ids = missing_expected_ids(cases, corpus)
  print_review_startup_summary(
    dataset_version=dataset_version,
    corpus_version=args.corpus_version,
    corpus_size=len(corpus),
    query_count=len(cases),
    missing_ids=missing_ids,
    output_func=lambda message: print(message, flush=True),
  )
  if missing_ids:
    raise SystemExit(
      "Review aborted because expectedKnowledgeIds are missing from the selected corpus: "
      + ", ".join(missing_ids)
    )

  reviewed = review_dataset(cases, corpus=corpus)
  write_review_dataset(reviewed, output_path, dataset_version=args.dataset_version)
  print_review_stats(reviewed)
  print(f"\n已写入: {output_path}")
  return 0


def load_review_corpus(corpus_version: str) -> list[KnowledgeEvidence]:
  if corpus_version in {"", "runtime", "default"}:
    return default_video_diagnosis_corpus()
  return load_benchmark_corpus(corpus_version)


def read_dataset_version(input_path: str | Path) -> str:
  source = Path(input_path)
  if source.suffix.lower() == ".jsonl":
    return "jsonl"
  payload = json.loads(source.read_text(encoding="utf-8"))
  if isinstance(payload, dict):
    return str(payload.get("datasetVersion") or "unknown")
  return "unknown"


def missing_expected_ids(cases: list[GoldenQueryCase], corpus: list[KnowledgeEvidence]) -> list[str]:
  corpus_ids = {item.id for item in corpus}
  missing = {
    knowledge_id
    for case in cases
    for knowledge_id in case.expected_knowledge_ids
    if knowledge_id not in corpus_ids
  }
  return sorted(missing)


def print_review_startup_summary(
  *,
  dataset_version: str,
  corpus_version: str,
  corpus_size: int,
  query_count: int,
  missing_ids: list[str],
  output_func: Callable[[str], None] = print,
) -> None:
  output_func(f"Dataset version: {dataset_version}")
  output_func(f"Corpus version: {corpus_version}")
  output_func(f"Corpus size: {corpus_size}")
  output_func(f"Query count: {query_count}")
  output_func(f"Missing expected IDs: {len(missing_ids)}")
  if missing_ids:
    output_func(f"Missing expected ID list: {json.dumps(missing_ids, ensure_ascii=False)}")


def _build_review_row(
  case: GoldenQueryCase,
  corpus_by_id: dict[str, KnowledgeEvidence],
  retriever: InMemoryHybridKnowledgeRetriever,
) -> dict[str, object]:
  query = KnowledgeQuery(
    query_text=case.query,
    skill_code=case.skill_code,
    knowledge_type=case.knowledge_type,
    category=case.category,
    top_k=5,
  )
  bm25 = retriever.search_bm25(query, limit=5)
  vector = retriever.search_vector(query, limit=5)
  hybrid = retriever.search_hybrid_rrf(query, final_top_k=5)
  return {
    "queryId": case.query_id,
    "skillCode": case.skill_code,
    "difficulty": case.difficulty,
    "query": case.query,
    "expectedKnowledgeIds": case.expected_knowledge_ids,
    "expectedKnowledgeSummaries": [
      _knowledge_summary(corpus_by_id.get(knowledge_id), knowledge_id)
      for knowledge_id in case.expected_knowledge_ids
    ],
    "bm25Top5": [_retrieval_item(item) for item in bm25],
    "vectorTop5": [_retrieval_item(item) for item in vector],
    "hybridTop5": [_retrieval_item(item) for item in hybrid],
  }


def _render_case(row: dict[str, object], *, index: int, total: int) -> str:
  lines = [
    "",
    "=" * 88,
    f"样本 {index}/{total}",
    f"queryId: {row['queryId']}",
    f"skillCode: {row['skillCode']}",
    f"difficulty: {row['difficulty']}",
    f"query: {row['query']}",
    f"expectedKnowledgeIds: {json.dumps(row['expectedKnowledgeIds'], ensure_ascii=False)}",
    "",
    "expected knowledge 原文摘要:",
  ]
  lines.extend(f"- {item}" for item in row["expectedKnowledgeSummaries"])  # type: ignore[index]
  lines.extend(["", "当前 BM25 Top5:"])
  lines.extend(_render_top5(row["bm25Top5"]))  # type: ignore[arg-type]
  lines.extend(["", "当前 Vector Top5:"])
  lines.extend(_render_top5(row["vectorTop5"]))  # type: ignore[arg-type]
  lines.extend(["", "当前 Hybrid Top5:"])
  lines.extend(_render_top5(row["hybridTop5"]))  # type: ignore[arg-type]
  lines.append("")
  return "\n".join(lines)


def _render_top5(items: object) -> list[str]:
  rows = items if isinstance(items, list) else []
  if not rows:
    return ["- 无结果"]
  return [
    f"- {index}. {item['id']} score={item['score']:.6f} title={item['title']}"
    for index, item in enumerate(rows, start=1)
    if isinstance(item, dict)
  ]


def _ask_action(input_func: ReviewInput) -> str:
  while True:
    action = input_func("操作 [v=VERIFIED, r=REJECTED, e=编辑, s=skip]: ").strip().lower()
    if action in {"v", "r", "e", "s", ""}:
      return action or "s"
    print("请输入 v / r / e / s。")


def _edit_case(
  case: GoldenQueryCase,
  *,
  input_func: ReviewInput,
  output_func: Callable[[str], None],
) -> GoldenQueryCase:
  output_func("留空表示保持原值。编辑后状态仍保持原状态；如需 VERIFIED，请在该样本下一轮审核时输入 v。")
  query = input_func(f"query [{case.query}]: ").strip() or case.query
  expected_input = input_func(
    f"expectedKnowledgeIds 逗号分隔 [{','.join(case.expected_knowledge_ids)}]: "
  ).strip()
  expected_ids = case.expected_knowledge_ids if not expected_input else [
    item.strip() for item in expected_input.split(",") if item.strip()
  ]
  difficulty_input = input_func(f"difficulty EXACT/SEMANTIC/MIXED [{case.difficulty}]: ").strip().upper()
  difficulty = case.difficulty
  if difficulty_input:
    if difficulty_input not in VALID_DIFFICULTIES:
      output_func(f"difficulty `{difficulty_input}` 无效，保持原值 `{case.difficulty}`。")
    else:
      difficulty = difficulty_input
  return replace(
    case,
    query=query,
    expected_knowledge_ids=expected_ids,
    difficulty=difficulty,  # type: ignore[arg-type]
  )


def _knowledge_summary(item: KnowledgeEvidence | None, fallback_id: str) -> str:
  if item is None:
    return f"{fallback_id}: 未在当前 corpus 中找到"
  return f"{item.id} | {item.title} | {item.content}"


def _retrieval_item(item: KnowledgeEvidence) -> dict[str, object]:
  return {
    "id": item.id,
    "score": item.score,
    "knowledgeType": item.knowledge_type,
    "title": item.title,
    "summary": item.content,
  }


def _case_to_external_dict(case: GoldenQueryCase) -> dict[str, object]:
  return {
    "queryId": case.query_id,
    "query": case.query,
    "skillCode": case.skill_code,
    "knowledgeType": case.knowledge_type,
    "expectedKnowledgeIds": case.expected_knowledge_ids,
    "acceptableKnowledgeIds": case.acceptable_knowledge_ids,
    "hardNegativeKnowledgeIds": case.hard_negative_knowledge_ids,
    "matchType": case.match_type,
    "difficulty": case.difficulty,
    "hardNegativeScope": case.hard_negative_scope,
    "annotationStatus": case.annotation_status,
    "category": case.category,
    "notes": case.notes,
  }


def _count_by(cases: list[GoldenQueryCase], field_name: str) -> dict[str, int]:
  counts: dict[str, int] = {}
  for case in cases:
    value = str(getattr(case, field_name))
    counts[value] = counts.get(value, 0) + 1
  return dict(sorted(counts.items()))


if __name__ == "__main__":
  raise SystemExit(main())
