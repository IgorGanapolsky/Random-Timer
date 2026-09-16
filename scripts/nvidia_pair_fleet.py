#!/usr/bin/env python3
"""NVIDIA PAIR fleet inventory + independent-job scheduler (local / Tailscale).

Does not call cloud GPUs. Schedules whole requests to one eligible node.
Galaxy S25 is modeled as Termux/Ollama edge (native_pair=false).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

FLEET_FIXTURE_REL = "marketing/data/fleet/nvidia_pair_nodes.json"


def load_fleet(repo: Path | None = None) -> dict[str, Any]:
    root = repo or _REPO_ROOT
    path = root / FLEET_FIXTURE_REL
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("fleet fixture must be an object")
    return data


def _node_eligible(
    node: Mapping[str, Any],
    *,
    model: str,
    engine: str,
) -> bool:
    if node.get("ready") is not True:
        return False
    if node.get("online") is not True:
        return False
    engines = node.get("engines") or []
    if isinstance(engines, list):
        eng_ok = engine in {str(e).lower() for e in engines}
    else:
        eng_ok = False
    if not eng_ok:
        return False
    models = node.get("models") or []
    if not isinstance(models, list):
        return False
    want = (model or "").strip()
    if not want:
        return False
    return want in {str(m) for m in models}


def select_eligible_node(
    *,
    fleet: Mapping[str, Any],
    model: str,
    engine: str = "ollama",
    prefer_roles: Sequence[str] | None = None,
) -> dict[str, Any] | None:
    """Pick one ready node with engine + exact model; prefer lower active_jobs."""
    nodes = fleet.get("nodes") or []
    if not isinstance(nodes, list):
        return None
    eligible: list[dict[str, Any]] = []
    for raw in nodes:
        if not isinstance(raw, Mapping):
            continue
        node = dict(raw)
        if _node_eligible(node, model=model, engine=engine):
            eligible.append(node)
    if not eligible:
        return None
    prefer = [str(r) for r in (prefer_roles or ())]
    if prefer:
        preferred = [n for n in eligible if str(n.get("role") or "") in prefer]
        if preferred:
            eligible = preferred
    eligible.sort(
        key=lambda n: (
            int(n.get("active_jobs") or 0),
            float(n.get("gpu_util") or 0.0),
            str(n.get("id") or ""),
        )
    )
    return eligible[0]


def schedule_independent_jobs(
    *,
    fleet: Mapping[str, Any],
    model: str,
    engine: str = "ollama",
    job_count: int = 1,
) -> dict[str, Any]:
    """Workload-level concurrency: each job → one eligible node for its lifetime."""
    count = max(1, int(job_count))
    # Mutable load simulation so later jobs see earlier placements
    working: list[MutableMapping[str, Any]] = []
    for raw in fleet.get("nodes") or []:
        if isinstance(raw, Mapping):
            working.append(dict(raw))
    sim_fleet: dict[str, Any] = {**dict(fleet), "nodes": working}

    placements: list[dict[str, Any]] = []
    for i in range(count):
        node = select_eligible_node(fleet=sim_fleet, model=model, engine=engine)
        if not node:
            return {
                "ok": False,
                "reason": "no_eligible_node",
                "placed": len(placements),
                "requested": count,
                "placements": placements,
                "nodes_used": len({p["node_id"] for p in placements}),
                "multinode": False,
            }
        node_id = str(node.get("id"))
        placements.append({"job_index": i, "node_id": node_id, "model": model})
        for n in working:
            if str(n.get("id")) == node_id:
                n["active_jobs"] = int(n.get("active_jobs") or 0) + 1
                break

    nodes_used = sorted({p["node_id"] for p in placements})
    return {
        "ok": True,
        "reason": "scheduled",
        "placed": len(placements),
        "requested": count,
        "placements": placements,
        "nodes_used": len(nodes_used),
        "node_ids": nodes_used,
        "multinode": len(nodes_used) > 1,
        "model": model,
        "engine": engine,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NVIDIA PAIR fleet scheduler")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--model", default="qwen2.5:3b-hermes-64k")
    parser.add_argument("--engine", default="ollama")
    parser.add_argument("--jobs", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    fleet = load_fleet(Path(args.repo_root))
    plan = schedule_independent_jobs(
        fleet=fleet,
        model=args.model,
        engine=args.engine,
        job_count=args.jobs,
    )
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(plan)
    return 0 if plan.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
