#!/usr/bin/env python3
"""Read NVIDIA PAIR Jobs/workloads history — multi-node ground truth.

Upstream: https://github.com/NVIDIA/Personal-AI-Router

PAIR persists workloads under the per-user app data dir as
`workloads-history.json`. Each row carries `scheduledOn` (node UUID that ran
the request) and `originatedFrom` (node that accepted the client request).
Multi-node claims require **distinct `scheduledOn` values** in this history
(or live Jobs / Workloads UI) — never agent/subagent counts alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

UPSTREAM_GITHUB = "https://github.com/NVIDIA/Personal-AI-Router"

# macOS path from NVIDIA Personal AI Router installers / desktop app.
_MACOS_APP_SUPPORT = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Nvidia Corporation"
    / "Personal AI Router"
    / "workloads-history.json"
)


def default_workloads_history_path() -> Path:
    return _MACOS_APP_SUPPORT


def load_workloads(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("workloads-history.json must be a JSON array")
    out: list[dict[str, Any]] = []
    for row in data:
        if isinstance(row, Mapping):
            out.append(dict(row))
    return out


def summarize_workloads(
    rows: Sequence[Mapping[str, Any]],
    *,
    recent: int | None = None,
) -> dict[str, Any]:
    selected = list(rows)
    if recent is not None and recent > 0:
        selected = selected[-recent:]
    scheduled: list[str] = []
    originated: list[str] = []
    for row in selected:
        s = row.get("scheduledOn")
        o = row.get("originatedFrom")
        if isinstance(s, str) and s.strip():
            scheduled.append(s.strip())
        if isinstance(o, str) and o.strip():
            originated.append(o.strip())
    distinct_sched = sorted(set(scheduled))
    distinct_orig = sorted(set(originated))
    return {
        "job_count": len(selected),
        "distinct_scheduled_on": distinct_sched,
        "distinct_originated_from": distinct_orig,
        "scheduled_on_count": len(distinct_sched),
        "originated_from_count": len(distinct_orig),
        "multinode": len(distinct_sched) > 1,
        "upstream": UPSTREAM_GITHUB,
    }


def evaluate_multinode_from_workloads(
    path: Path,
    *,
    recent: int | None = 500,
) -> dict[str, Any]:
    if not path.is_file():
        return {
            "ok": False,
            "reason": "workloads_history_missing",
            "path": str(path),
            "multinode": False,
            "upstream": UPSTREAM_GITHUB,
        }
    try:
        rows = load_workloads(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "ok": False,
            "reason": f"workloads_history_invalid:{exc}",
            "path": str(path),
            "multinode": False,
            "upstream": UPSTREAM_GITHUB,
        }
    summary = summarize_workloads(rows, recent=recent)
    if not summary["multinode"]:
        return {
            "ok": False,
            "reason": "single_node_only",
            "path": str(path),
            **summary,
        }
    return {
        "ok": True,
        "reason": "distinct_scheduled_on",
        "path": str(path),
        **summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize NVIDIA PAIR workloads-history.json (Jobs ground truth)"
    )
    parser.add_argument(
        "--path",
        default=str(default_workloads_history_path()),
        help="Path to workloads-history.json",
    )
    parser.add_argument("--recent", type=int, default=500)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--require-multinode",
        action="store_true",
        help="Exit 1 unless distinct scheduledOn > 1",
    )
    args = parser.parse_args(argv)
    path = Path(args.path)
    report = evaluate_multinode_from_workloads(path, recent=args.recent)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report)
    if args.require_multinode:
        return 0 if report.get("ok") else 1
    return 0 if report.get("reason") != "workloads_history_invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
