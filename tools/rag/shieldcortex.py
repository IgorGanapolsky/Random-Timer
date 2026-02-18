from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class ShieldIssue:
    kind: str
    detail: str


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github_token", re.compile(r"\bgh[pous]_[A-Za-z0-9_]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b")),
    ("generic_secret", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*[^\\s]{6,}")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----")),
]


def scan(text: str) -> List[ShieldIssue]:
    issues: List[ShieldIssue] = []
    for kind, pat in _PATTERNS:
        if pat.search(text or ""):
            issues.append(ShieldIssue(kind=kind, detail=f"matched:{kind}"))
    return issues


def redact(text: str) -> str:
    """Best-effort redaction to avoid indexing secrets."""
    out = text or ""
    out = _PATTERNS[0][1].sub("[REDACTED_GITHUB_TOKEN]", out)
    out = _PATTERNS[1][1].sub("[REDACTED_OPENAI_KEY]", out)
    out = _PATTERNS[2][1].sub("[REDACTED_GOOGLE_API_KEY]", out)
    out = _PATTERNS[3][1].sub("[REDACTED_SECRET]", out)
    out = _PATTERNS[4][1].sub("[REDACTED_PRIVATE_KEY_BLOCK]", out)
    return out


def shield(text: str) -> Tuple[str, List[ShieldIssue]]:
    redacted = redact(text)
    return redacted, scan(text)

