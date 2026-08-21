"""Transparent rank fusion for hybrid retrieval."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def reciprocal_rank_fusion(result_lists: Iterable[Iterable[T]], k: int = 60) -> list[tuple[T, float]]:
    """Fuse ranked lists without comparing incompatible score scales.

    Duplicate items in the same source list keep their first (best) rank.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    scores: dict[T, float] = defaultdict(float)
    for result_list in result_lists:
        seen: set[T] = set()
        for rank, item in enumerate(result_list, start=1):
            if item in seen:
                continue
            seen.add(item)
            scores[item] += 1 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))
