from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MemAlignResult:
    score: float
    reasons: List[str]


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score_record(
    *,
    vector_sim: float,
    fts_rank: Optional[float],
    importance: float,
    recency_days: Optional[float],
) -> MemAlignResult:
    """Combine signals into a single retrieval score.

    - vector_sim: cosine similarity (0..1-ish)
    - fts_rank: optional rank proxy (0..1 where higher is better)
    - importance: (0..1)
    - recency_days: optional days since event; newer gets a small boost
    """
    reasons: List[str] = []

    vs = _clamp(vector_sim)
    reasons.append(f"vector_sim={vs:.3f}")

    fr = _clamp(fts_rank) if fts_rank is not None else 0.0
    if fts_rank is not None:
        reasons.append(f"fts_rank={fr:.3f}")

    imp = _clamp(importance)
    reasons.append(f"importance={imp:.2f}")

    rec = 0.0
    if recency_days is not None and recency_days >= 0:
        # Half-life-ish: small boost for very recent items.
        rec = math.exp(-recency_days / 14.0) * 0.15
        reasons.append(f"recency_boost={rec:.3f} (days={recency_days:.1f})")

    # Hybrid weighting: vector + fts with an importance floor.
    base = 0.60 * vs + 0.25 * fr + 0.15 * imp
    total = _clamp(base + rec)
    return MemAlignResult(score=total, reasons=reasons)

