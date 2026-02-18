from __future__ import annotations

import hashlib
import math
import re
from typing import Iterable, List


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def hashed_embedding(text: str, *, dim: int = 256) -> List[float]:
    """Deterministic, dependency-free embedding via feature hashing.

    This is not a semantic model. It's a stable lexical embedding that enables
    vector search locally without external services.
    """
    vec = [0.0] * dim
    for tok in tokenize(text):
        h = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
        # 64-bit -> index + sign
        n = int.from_bytes(h, "big", signed=False)
        idx = n % dim
        sign = -1.0 if (n >> 63) & 1 else 1.0
        vec[idx] += sign

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    sa = 0.0
    sb = 0.0
    dot = 0.0
    for x, y in zip(a, b):
        dot += x * y
        sa += x * x
        sb += y * y
    if sa <= 0 or sb <= 0:
        return 0.0
    return dot / math.sqrt(sa * sb)

