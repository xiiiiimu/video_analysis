from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


def reciprocal_rank_fusion(
  ranked_lists: Sequence[Sequence[T]],
  key_fn: Callable[[T], str],
  *,
  final_top_k: int,
  rrf_k: int = 60,
) -> list[tuple[T, float]]:
  item_map: dict[str, T] = {}
  score_map: dict[str, float] = {}

  for ranked in ranked_lists:
    for index, item in enumerate(ranked):
      key = key_fn(item)
      item_map.setdefault(key, item)
      score_map[key] = score_map.get(key, 0.0) + 1.0 / (rrf_k + index + 1)

  return [
    (item_map[key], score)
    for key, score in sorted(score_map.items(), key=lambda entry: entry[1], reverse=True)[
      :final_top_k
    ]
  ]
