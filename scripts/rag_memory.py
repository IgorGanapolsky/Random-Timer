#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.rag.store import add_memory, query_memories, rebuild_index
from tools.rag.rlhf import add_preference, iter_preferences


def _parse_tags(val: str) -> List[str]:
    tags: List[str] = []
    for t in (val or "").split(","):
        t = t.strip()
        if t:
            tags.append(t)
    return tags


def cmd_add(args: argparse.Namespace) -> int:
    meta: Dict[str, Any] = {}
    if args.meta_json:
        try:
            meta = json.loads(args.meta_json)
        except Exception as e:
            print(f"Invalid --meta-json: {e}", file=sys.stderr)
            return 2

    item = add_memory(
        kind=args.kind,
        text=args.text,
        tags=_parse_tags(args.tags),
        importance=args.importance,
        meta=meta,
    )
    print(item.id)
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    hits = query_memories(args.query, limit=args.limit)
    if args.json:
        print(json.dumps(hits, ensure_ascii=True, indent=2))
        return 0

    for h in hits:
        print(f"- score={h['score']:.3f} kind={h.get('kind','')} tags={','.join(h.get('tags') or [])}")
        print(f"  id={h['id']}")
        print(f"  text={h['text'][:240].replace('\\n',' ')}")
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    n = rebuild_index()
    print(n)
    return 0


def cmd_pref_add(args: argparse.Namespace) -> int:
    meta: Dict[str, Any] = {}
    if args.meta_json:
        try:
            meta = json.loads(args.meta_json)
        except Exception as e:
            print(f"Invalid --meta-json: {e}", file=sys.stderr)
            return 2

    item = add_preference(
        prompt=args.prompt,
        chosen=args.chosen,
        rejected=args.rejected,
        tags=_parse_tags(args.tags),
        meta=meta,
    )
    # Also index a short redacted summary for retrieval.
    add_memory(
        kind="preference",
        text=f"prompt: {item.prompt_redacted}\nchosen: {item.chosen_redacted}\nrejected: {item.rejected_redacted}",
        tags=(["rlhf"] + item.tags),
        importance=0.7,
        meta={"pref_id": item.id, **item.meta},
    )
    print(item.id)
    return 0


def cmd_pref_export(args: argparse.Namespace) -> int:
    items = iter_preferences()
    # OpenAI-style preference jsonl: {prompt, chosen, rejected, ...}
    for it in items:
        obj = {
            "prompt": it.prompt_redacted,
            "chosen": it.chosen_redacted,
            "rejected": it.rejected_redacted,
            "tags": it.tags,
            "meta": it.meta,
            "ts": it.ts,
            "id": it.id,
        }
        print(json.dumps(obj, ensure_ascii=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Local RAG memory (LanceDB + jsonl) for this repo.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Add a memory item (also appends to .rag/events.jsonl)")
    pa.add_argument("--kind", required=True, help="e.g. question, answer, decision, bug, fix")
    pa.add_argument("--text", required=True, help="freeform text (will be redacted before indexing)")
    pa.add_argument("--tags", default="", help="comma-separated tags")
    pa.add_argument("--importance", type=float, default=0.5, help="0..1")
    pa.add_argument("--meta-json", default="", help="JSON object string (optional)")
    pa.set_defaults(fn=cmd_add)

    pq = sub.add_parser("query", help="Query memories")
    pq.add_argument("query", help="search string")
    pq.add_argument("--limit", type=int, default=8)
    pq.add_argument("--json", action="store_true", help="output JSON")
    pq.set_defaults(fn=cmd_query)

    pr = sub.add_parser("rebuild", help="Rebuild LanceDB index from .rag/events.jsonl")
    pr.set_defaults(fn=cmd_rebuild)

    pp = sub.add_parser("pref-add", help="Add an RLHF preference (prompt/chosen/rejected) to .rag/prefs.jsonl")
    pp.add_argument("--prompt", required=True)
    pp.add_argument("--chosen", required=True)
    pp.add_argument("--rejected", required=True)
    pp.add_argument("--tags", default="", help="comma-separated tags")
    pp.add_argument("--meta-json", default="", help="JSON object string (optional)")
    pp.set_defaults(fn=cmd_pref_add)

    pe = sub.add_parser("pref-export", help="Export RLHF preferences as JSONL to stdout")
    pe.set_defaults(fn=cmd_pref_export)

    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
