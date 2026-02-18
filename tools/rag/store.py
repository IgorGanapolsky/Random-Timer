from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from tools.rag.hash_embed import hashed_embedding
from tools.rag.memalign import score_record
from tools.rag.shieldcortex import shield


DEFAULT_DB_DIR = Path(".rag/lancedb")
DEFAULT_EVENTS_PATH = Path(".rag/events.jsonl")


@dataclass
class MemoryItem:
    id: str
    ts: float
    kind: str
    text: str
    text_redacted: str
    tags: List[str]
    importance: float
    issues: List[Dict[str, str]]
    vector: List[float]
    meta: Dict[str, Any]


def _now() -> float:
    return time.time()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_event(item: MemoryItem, *, events_path: Path = DEFAULT_EVENTS_PATH) -> None:
    _ensure_parent(events_path)
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(item), ensure_ascii=True) + "\n")


def _import_lancedb():
    try:
        import lancedb  # type: ignore
        import pyarrow as pa  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Missing dependencies for LanceDB.\n"
            "Install:\n"
            "  python3 -m pip install lancedb pyarrow\n"
            f"Original error: {e}"
        )
    return lancedb, pa


def _connect(db_dir: Path):
    lancedb, _ = _import_lancedb()
    db_dir.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(db_dir))


def _open_or_create_table(db, *, dim: int) -> Any:
    _, pa = _import_lancedb()

    table_name = "memories"
    names = set(db.table_names())
    if table_name in names:
        return db.open_table(table_name)

    schema = pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("ts", pa.float64()),
            pa.field("kind", pa.string()),
            pa.field("text", pa.string()),
            pa.field("text_redacted", pa.string()),
            pa.field("tags", pa.list_(pa.string())),
            pa.field("importance", pa.float32()),
            pa.field("issues", pa.string()),  # JSON string for portability
            # Lance vector index requires a fixed-size vector type.
            pa.field("vector", pa.list_(pa.float32(), dim)),
            pa.field("meta", pa.string()),  # JSON string
        ]
    )

    tbl = db.create_table(table_name, schema=schema)
    # Best-effort FTS index; older lancedb versions may not support it.
    try:
        tbl.create_fts_index("text_redacted", replace=True)
    except Exception:
        pass
    return tbl


def add_memory(
    *,
    kind: str,
    text: str,
    tags: Optional[List[str]] = None,
    importance: float = 0.5,
    meta: Optional[Dict[str, Any]] = None,
    dim: int = 256,
    db_dir: Path = DEFAULT_DB_DIR,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> MemoryItem:
    redacted, issues = shield(text)
    item = MemoryItem(
        id=str(uuid.uuid4()),
        ts=_now(),
        kind=kind,
        text=text,
        text_redacted=redacted,
        tags=tags or [],
        importance=float(importance),
        issues=[{"kind": i.kind, "detail": i.detail} for i in issues],
        vector=[float(x) for x in hashed_embedding(redacted, dim=dim)],
        meta=meta or {},
    )

    append_event(item, events_path=events_path)

    db = _connect(db_dir)
    tbl = _open_or_create_table(db, dim=dim)
    tbl.add(
        [
            {
                "id": item.id,
                "ts": item.ts,
                "kind": item.kind,
                "text": item.text,
                "text_redacted": item.text_redacted,
                "tags": item.tags,
                "importance": float(item.importance),
                "issues": json.dumps(item.issues, ensure_ascii=True),
                "vector": [float(v) for v in item.vector],
                "meta": json.dumps(item.meta, ensure_ascii=True),
            }
        ]
    )
    return item


def rebuild_index(
    *,
    dim: int = 256,
    db_dir: Path = DEFAULT_DB_DIR,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> int:
    if not events_path.exists():
        return 0

    db = _connect(db_dir)
    # Overwrite table for deterministic rebuild.
    try:
        db.drop_table("memories")
    except Exception:
        pass

    tbl = _open_or_create_table(db, dim=dim)
    rows: List[Dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rows.append(
                {
                    "id": rec["id"],
                    "ts": float(rec["ts"]),
                    "kind": rec.get("kind", ""),
                    "text": rec.get("text", ""),
                    "text_redacted": rec.get("text_redacted", rec.get("text", "")),
                    "tags": rec.get("tags", []) or [],
                    "importance": float(rec.get("importance", 0.5)),
                    "issues": json.dumps(rec.get("issues", []), ensure_ascii=True),
                    "vector": rec.get("vector") or [0.0] * dim,
                    "meta": json.dumps(rec.get("meta", {}), ensure_ascii=True),
                }
            )
    if rows:
        tbl.add(rows)
    try:
        tbl.create_fts_index("text_redacted", replace=True)
    except Exception:
        pass
    return len(rows)


def _days_since(ts: float) -> float:
    return max(0.0, (_now() - ts) / 86400.0)


def query_memories(
    query: str,
    *,
    limit: int = 8,
    dim: int = 256,
    db_dir: Path = DEFAULT_DB_DIR,
) -> List[Dict[str, Any]]:
    db = _connect(db_dir)
    tbl = _open_or_create_table(db, dim=dim)

    qv = hashed_embedding(query, dim=dim)

    # Vector search
    vec_rows: List[Dict[str, Any]] = []
    try:
        vec_rows = (
            tbl.search(qv, vector_column_name="vector", query_type="vector")
            .limit(max(limit * 2, limit))
            .to_list()
        )
    except Exception:
        vec_rows = []

    # FTS search
    fts_rows: List[Dict[str, Any]] = []
    try:
        fts_rows = (
            tbl.search(query, query_type="fts", fts_columns="text_redacted")
            .limit(max(limit * 2, limit))
            .to_list()
        )
    except Exception:
        fts_rows = []

    # Merge by id and score with MemAlign.
    merged: Dict[str, Dict[str, Any]] = {}
    for r in vec_rows:
        # LanceDB returns `_distance` (lower is better). Convert to a bounded similarity proxy.
        dist = float(r.get("_distance", 0.0) or 0.0)
        sim = 1.0 / (1.0 + max(0.0, dist))
        merged[str(r.get("id"))] = {"row": r, "vector_sim": sim}
    for r in fts_rows:
        rid = str(r.get("id"))
        m = merged.setdefault(rid, {"row": r, "vector_sim": 0.0})
        m["row"] = r
        # LanceDB FTS score naming varies; keep best-effort.
        raw = float(r.get("_score", r.get("_rank", 0.0)) or 0.0)
        # Convert to a bounded rank proxy (0..1) without assuming a specific scale.
        m["fts_rank"] = min(1.0, max(0.0, raw / 10.0))

    scored: List[Dict[str, Any]] = []
    for rid, m in merged.items():
        row = m["row"]
        ts = float(row.get("ts", 0.0) or 0.0)
        res = score_record(
            vector_sim=float(m.get("vector_sim", 0.0)),
            fts_rank=m.get("fts_rank"),
            importance=float(row.get("importance", 0.5) or 0.5),
            recency_days=_days_since(ts) if ts else None,
        )
        scored.append(
            {
                "id": rid,
                "score": res.score,
                "reasons": res.reasons,
                "kind": row.get("kind", ""),
                "ts": ts,
                "tags": row.get("tags", []),
                "text": row.get("text_redacted", row.get("text", "")),
                "meta": row.get("meta", "{}"),
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
