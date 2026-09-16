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
_MACOS_PAIR_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Nvidia Corporation"
    / "Personal AI Router"
)
_MACOS_APP_SUPPORT = _MACOS_PAIR_DIR / "workloads-history.json"
_ALLOWED_BASENAMES = frozenset(
    {
        "workloads-history.json",
        "workloads-history.json.1",
        "workloads-history.json.2",
        "workloads-history.json.3",
    }
)


def default_workloads_history_path() -> Path:
    return _MACOS_APP_SUPPORT


def resolve_workloads_path(
    path: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    """Only allow workloads-history* under the PAIR app-support directory.

    Blocks path traversal from CLI / LLM-supplied --path (Sonar S8707).
    Tests may pass ``allowed_root`` to sandbox a temp directory.
    """
    resolved = path.expanduser().resolve()
    root = (allowed_root or _MACOS_PAIR_DIR).expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"workloads path must stay under {root}: {resolved}") from exc
    if resolved.name not in _ALLOWED_BASENAMES:
        raise ValueError(
            f"workloads basename must be one of {sorted(_ALLOWED_BASENAMES)}"
        )
    return resolved


def load_workloads(
    path: Path,
    *,
    allowed_root: Path | None = None,
) -> list[dict[str, Any]]:
    safe = resolve_workloads_path(path, allowed_root=allowed_root)
    if not safe.is_file():
        raise FileNotFoundError(str(safe))
    data = json.loads(safe.read_text(encoding="utf-8"))
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
    allowed_root: Path | None = None,
) -> dict[str, Any]:
    try:
        safe = resolve_workloads_path(path, allowed_root=allowed_root)
    except ValueError as exc:
        return {
            "ok": False,
            "reason": f"workloads_path_rejected:{exc}",
            "path": str(path),
            "multinode": False,
            "upstream": UPSTREAM_GITHUB,
        }
    if not safe.is_file():
        return {
            "ok": False,
            "reason": "workloads_history_missing",
            "path": str(safe),
            "multinode": False,
            "upstream": UPSTREAM_GITHUB,
        }
    try:
        rows = load_workloads(safe, allowed_root=allowed_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "ok": False,
            "reason": f"workloads_history_invalid:{exc}",
            "path": str(safe),
            "multinode": False,
            "upstream": UPSTREAM_GITHUB,
        }
    summary = summarize_workloads(rows, recent=recent)
    if not summary["multinode"]:
        return {
            "ok": False,
            "reason": "single_node_only",
            "path": str(safe),
            **summary,
        }
    return {
        "ok": True,
        "reason": "distinct_scheduled_on",
        "path": str(safe),
        **summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize NVIDIA PAIR workloads-history.json (Jobs ground truth)"
    )
    parser.add_argument(
        "--history-index",
        type=int,
        default=0,
        choices=(0, 1, 2, 3),
        help="0=workloads-history.json; 1..3=rotated .json.N under PAIR app-support",
    )
    parser.add_argument("--recent", type=int, default=500)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--require-multinode",
        action="store_true",
        help="Exit 1 unless distinct scheduledOn > 1",
    )
    args = parser.parse_args(argv)
    # No free-form --path: only fixed basenames under the PAIR app-support dir
    # (blocks LLM/CLI path injection — Sonar pythonsecurity:S8707).
    if args.history_index == 0:
        path = default_workloads_history_path()
    else:
        path = _MACOS_PAIR_DIR / f"workloads-history.json.{args.history_index}"
    report = evaluate_multinode_from_workloads(path, recent=args.recent)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report)
    reason = str(report.get("reason") or "")
    if args.require_multinode:
        return 0 if report.get("ok") else 1
    if reason.startswith("workloads_history_invalid") or reason.startswith(
        "workloads_path_rejected"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
