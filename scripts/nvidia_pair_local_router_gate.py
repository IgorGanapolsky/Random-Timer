#!/usr/bin/env python3
"""NVIDIA PAIR local inference router lite — multi-node Ollama/LM Studio proxy.

Upstream (canonical): https://github.com/NVIDIA/Personal-AI-Router
Blog: https://developer.nvidia.com/blog/nvidia-pair-virtual-inference-router-expands-available-compute-on-your-local-network/
Digest: https://www.infoq.com/news/2026/09/nvidia-pair-ai-task-router/

PAIR thesis: multi-agent / subagent fanout bottlenecks one GPU. A virtual
inference router proxies familiar Ollama/LM Studio endpoints, discovers paired
local nodes (mDNS / Tailscale / manual), and schedules each *independent*
request onto one eligible node (engine ready + exact model present + load).
Does NOT merge GPUs, pool VRAM, or shard a single request across machines.
Jobs / workloads-history.json telemetry is ground truth for multi-node claims.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lite_gate_common import (
    Decision,
    norm,
    require_docs_needles,
    require_dual_skills,
    run_presence_cli,
)
from scripts.nvidia_pair_fleet import (
    FLEET_FIXTURE_REL,
    load_fleet,
    schedule_independent_jobs,
    select_eligible_node,
)
from scripts.nvidia_pair_workloads import (
    UPSTREAM_GITHUB,
    evaluate_multinode_from_workloads,
)

SOURCE = UPSTREAM_GITHUB
BLOG_SOURCE = (
    "https://developer.nvidia.com/blog/"
    "nvidia-pair-virtual-inference-router-expands-available-compute-on-your-local-network/"
)
INFOQ_SOURCE = "https://www.infoq.com/news/2026/09/nvidia-pair-ai-task-router/"

HEALTH_SIGNALS = (
    "proxy_familiar_local_interface",
    "workload_level_concurrency",
    "one_request_one_node",
    "elastic_home_nodes",
    "eligibility_model_engine_ready",
    "jobs_telemetry_ground_truth",
    "workloads_history_ground_truth",
    "no_vram_pooling",
    "no_harness_api_change",
    "tailscale_or_lan_pairing",
    "s25_edge_ollama_not_native_pair",
    "upstream_personal_ai_router_github",
)


def evaluate_pair_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "merge_gpus",
        "pool_vram",
        "shard_single_request",
        "split_one_inference_across_nodes",
    }:
        return Decision(
            action="block_vram_pooling_or_shard",
            ok=False,
            reason="PAIR schedules whole requests to one node — no VRAM pool / single-request shard",
        )

    if action in {
        "buy_cloud_gpu_cluster",
        "subscribe_remote_gpu_saas",
        "rent_h100_for_local_agents",
    }:
        return Decision(
            action="block_paid_remote_gpu",
            ok=False,
            reason="use home/Tailscale PAIR + Ollama; no paid remote GPU under hard monthly cap",
        )

    if action in {
        "claim_multinode_without_jobs",
        "claim_speedup_from_agent_count",
    }:
        return Decision(
            action="block_multinode_without_telemetry",
            ok=False,
            reason="Jobs/telemetry must show routed work on >1 node before multi-node claims",
        )

    if action in {"verify_multinode_from_workloads", "claim_multinode"}:
        wl_path = claim.get("workloads_history_path")
        path = Path(str(wl_path)) if wl_path else None
        if path is None:
            from scripts.nvidia_pair_workloads import default_workloads_history_path

            path = default_workloads_history_path()
        report = evaluate_multinode_from_workloads(path)
        if report.get("ok"):
            return Decision(
                action="allow_multinode_from_workloads",
                ok=True,
                reason=f"distinct scheduledOn={report.get('distinct_scheduled_on')}",
            )
        return Decision(
            action="block_multinode_without_telemetry",
            ok=False,
            reason=str(report.get("reason") or "workloads_not_multinode"),
        )

    if action in {"change_harness_to_cluster_api", "require_new_cluster_sdk"}:
        return Decision(
            action="block_harness_api_change",
            ok=False,
            reason="PAIR proxies Ollama/LM Studio — keep harness base URL; no new cluster API",
        )

    if action in {"treat_s25_as_native_pair_node", "install_pair_app_on_android"}:
        return Decision(
            action="block_s25_native_pair_claim",
            ok=False,
            reason="S25 is Termux/Ollama edge worker — not a native PAIR Windows/macOS/Linux target",
        )

    if action in {"schedule", "route_jobs"}:
        model = str(claim.get("model") or "")
        engine = norm(claim.get("engine") or "ollama") or "ollama"
        jobs = claim.get("jobs")
        fleet = claim.get("fleet")
        if not isinstance(fleet, Mapping):
            return Decision(
                action="block_schedule_without_fleet",
                ok=False,
                reason="pass fleet inventory mapping for schedule",
            )
        if isinstance(jobs, list) and jobs:
            plan = schedule_independent_jobs(
                fleet=fleet,  # type: ignore[arg-type]
                model=model,
                engine=engine,
                job_count=len(jobs),
            )
        else:
            try:
                job_count = int(claim.get("job_count") or 1)
            except (TypeError, ValueError):
                job_count = 1
            plan = schedule_independent_jobs(
                fleet=fleet,  # type: ignore[arg-type]
                model=model,
                engine=engine,
                job_count=max(1, job_count),
            )
        if not plan.get("ok"):
            return Decision(
                action="block_no_eligible_node",
                ok=False,
                reason=str(plan.get("reason") or "no eligible node"),
            )
        return Decision(
            action="allow_scheduled_jobs",
            ok=True,
            reason=(
                f"scheduled {plan['placed']} jobs across {plan['nodes_used']} node(s); "
                f"multinode={plan['multinode']}"
            ),
        )

    if action in {"select_node"}:
        fleet = claim.get("fleet")
        if not isinstance(fleet, Mapping):
            return Decision(
                action="block_select_without_fleet",
                ok=False,
                reason="pass fleet inventory for select_node",
            )
        node = select_eligible_node(
            fleet=fleet,  # type: ignore[arg-type]
            model=str(claim.get("model") or ""),
            engine=norm(claim.get("engine") or "ollama") or "ollama",
        )
        if not node:
            return Decision(
                action="block_no_eligible_node",
                ok=False,
                reason="no node ready with engine+exact model",
            )
        return Decision(
            action="allow_node_selected",
            ok=True,
            reason=f"selected node {node.get('id')}",
        )

    if action in {"verify_proxy", "claim_pair_ready"}:
        if claim.get("proxy_port_ok") is not True:
            return Decision(
                action="block_proxy_unverified",
                ok=False,
                reason="verify PAIR proxy owns Ollama port (11434) before claiming ready",
            )
        if claim.get("chat_smoke_ok") is not True:
            return Decision(
                action="block_smoke_unverified",
                ok=False,
                reason="chat smoke (e.g. PAIR_OK) required before claiming PAIR ready",
            )
        return Decision(
            action="allow_pair_verified",
            ok=True,
            reason="proxy + chat smoke verified",
        )

    return Decision(
        action="block_unknown_pair_action",
        ok=False,
        reason=(
            "declare action: schedule|select_node|verify_proxy|"
            "claim_multinode_without_jobs"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "NVIDIA_PAIR_LOCAL_ROUTER.md").is_file():
        blockers.append("missing_docs/NVIDIA_PAIR_LOCAL_ROUTER.md")
    if not (repo / "scripts" / "nvidia_pair_local_router_gate.py").is_file():
        blockers.append("missing_scripts/nvidia_pair_local_router_gate.py")
    if not (repo / "scripts" / "nvidia_pair_fleet.py").is_file():
        blockers.append("missing_scripts/nvidia_pair_fleet.py")
    if not (repo / "scripts" / "nvidia_pair_workloads.py").is_file():
        blockers.append("missing_scripts/nvidia_pair_workloads.py")
    blockers.extend(require_dual_skills(repo, "nvidia-pair-local-router-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "NVIDIA_PAIR_LOCAL_ROUTER.md",
            (
                "pair",
                "ollama",
                "lm studio",
                "proxy",
                "workload",
                "eligible",
                "jobs",
                "vram",
                "tailscale",
                "s25",
                "hermes",
                "independent",
                "github.com/nvidia/personal-ai-router",
                "workloads-history",
                "ollama-pr",
            ),
        )
    )

    fixture = (
        repo
        / "marketing"
        / "data"
        / "code_health"
        / "nvidia_pair_local_router_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/nvidia_pair_local_router_discipline.json"
        )
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            for signal in HEALTH_SIGNALS:
                if not charter.get(signal):
                    blockers.append(f"fixture_missing:{signal}")
            budget = charter.get("budget") or {}
            if (
                not isinstance(budget, dict)
                or budget.get("paid_remote_gpu_saas") is not False
            ):
                blockers.append("fixture_missing:budget.paid_remote_gpu_saas=false")

    fleet_path = repo / FLEET_FIXTURE_REL
    if not fleet_path.is_file():
        blockers.append(f"missing_fixture:{FLEET_FIXTURE_REL}")
    else:
        try:
            fleet = load_fleet(repo)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            blockers.append(f"fleet_invalid:{exc}")
        else:
            nodes = fleet.get("nodes") or []
            if not isinstance(nodes, list) or len(nodes) < 2:
                blockers.append("fleet_missing:nodes>=2")
            ids = {str(n.get("id")) for n in nodes if isinstance(n, Mapping)}
            if "macbook-pro" not in ids:
                blockers.append("fleet_missing:macbook-pro")
            if "mac-mini" not in ids:
                blockers.append("fleet_missing:mac-mini")
            if "galaxy-s25" not in ids:
                blockers.append("fleet_missing:galaxy-s25")
            s25 = next(
                (n for n in nodes if isinstance(n, Mapping) and n.get("id") == "galaxy-s25"),
                None,
            )
            if s25 and s25.get("native_pair") is not False:
                blockers.append("fleet_invalid:galaxy-s25.native_pair_must_be_false")

    ready = len(blockers) == 0
    return {
        "framework": "nvidia-pair-local-router-lite",
        "source": SOURCE,
        "blog_source": BLOG_SOURCE,
        "infoq_source": INFOQ_SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "single_gpu_queue_for_parallel_subagents",
        "budget_note": (
            "local PAIR + Ollama/LM Studio on home/Tailscale nodes; "
            "S25 as Termux edge Ollama; no paid remote GPU SaaS under hard cap"
        ),
        "pairs_with": [
            "scripts/agent_local_first_router.py",
            "docs/HYDRAFUSION_ROUTING.md",
            "docs/GPT6_ASTRA_HARNESS.md",
            "docs/MULTI_TEACHER_DISTILL.md",
        ],
        "verified_local": {
            "note": "session smoke recorded in marketing/data/nvidia_pair_local_router_adoption.json",
        },
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "nvidia-pair-local-router-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_pair_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
