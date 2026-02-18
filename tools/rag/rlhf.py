from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.rag.shieldcortex import shield


DEFAULT_PREFS_PATH = Path(".rag/prefs.jsonl")


@dataclass
class PreferenceItem:
    id: str
    ts: float
    prompt: str
    chosen: str
    rejected: str
    prompt_redacted: str
    chosen_redacted: str
    rejected_redacted: str
    tags: List[str]
    meta: Dict[str, Any]


def append_preference(item: PreferenceItem, *, prefs_path: Path = DEFAULT_PREFS_PATH) -> None:
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    with prefs_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(item), ensure_ascii=True) + "\n")


def add_preference(
    *,
    prompt: str,
    chosen: str,
    rejected: str,
    tags: Optional[List[str]] = None,
    meta: Optional[Dict[str, Any]] = None,
    prefs_path: Path = DEFAULT_PREFS_PATH,
) -> PreferenceItem:
    pr, _ = shield(prompt)
    ch, _ = shield(chosen)
    rj, _ = shield(rejected)
    item = PreferenceItem(
        id=str(uuid.uuid4()),
        ts=time.time(),
        prompt=prompt,
        chosen=chosen,
        rejected=rejected,
        prompt_redacted=pr,
        chosen_redacted=ch,
        rejected_redacted=rj,
        tags=tags or [],
        meta=meta or {},
    )
    append_preference(item, prefs_path=prefs_path)
    return item


def iter_preferences(*, prefs_path: Path = DEFAULT_PREFS_PATH) -> List[PreferenceItem]:
    if not prefs_path.exists():
        return []
    out: List[PreferenceItem] = []
    with prefs_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out.append(PreferenceItem(**rec))
    return out

