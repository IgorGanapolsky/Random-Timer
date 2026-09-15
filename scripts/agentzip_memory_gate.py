#!/usr/bin/env python3
"""AgentZip memory lite — bound high-fanout sandbox redundancy.

Sources:
  https://x.com/omarsar0/status/2098531286319341932
  https://arxiv.org/abs/2609.11294

Thesis: parallel agent sandboxes share template + sibling pages (76–96%
redundant). Compress against template/siblings during LLM wait; prefetch on
restore. Paper: up to 8.7× sandbox memory vs ~2.1× Linux; slowdown ~1.40× with
scheduling/prefetch (3.1× without).

Random Timer steals (hard monthly budget — no AgentZip product):
  - Cap concurrent worktrees/sandboxes to measured RAM headroom
  - Prefer shared template + deltas over full forks
  - Schedule heavy cleanup during LLM idle
  - Measure redundancy before claiming × memory wins
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

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

SOURCE = "https://arxiv.org/abs/2609.11294"
THREAD = "https://x.com/omarsar0/status/2098531286319341932"

HEALTH_SIGNALS = (
    "share_template_not_full_forks",
    "compress_during_llm_wait",
    "cap_fanout_before_oom",
    "measure_redundancy_before_scale",
)

# Paper markers (illustrative; still require local measurement before claims)
PAPER_MAX_MEMORY_REDUCTION = 8.7
PAPER_LINUX_BASELINE = 2.1
PAPER_SLOWDOWN_WITH_PREFETCH = 1.40


def evaluate_fanout_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))
    mode = norm(claim.get("mode") or claim.get("memory_mode"))

    if action in {"buy_agentzip", "subscribe_sandbox_compression"}:
        return Decision(
            action="block_paid_agentzip",
            ok=False,
            reason="encode AgentZip discipline locally; skip paid sandbox-compression products",
        )

    if action in {"claim_memory_reduction", "project_memory_win"}:
        measured = claim.get("redundancy_pct")
        if measured is None:
            return Decision(
                action="block_unmeasured_memory_claim",
                ok=False,
                reason="measure redundancy_pct before claiming × memory reduction",
            )
        try:
            red = float(measured)
        except (TypeError, ValueError):
            return Decision(
                action="block_malformed_redundancy",
                ok=False,
                reason="redundancy_pct must be a finite number",
            )
        if not math.isfinite(red) or red <= 0:
            return Decision(
                action="block_unmeasured_memory_claim",
                ok=False,
                reason="redundancy_pct must be a finite number > 0",
            )

    concurrent = claim.get("concurrent_sandboxes")
    if concurrent is not None:
        try:
            as_float = float(concurrent)
            n = int(as_float)
        except (TypeError, ValueError):
            return Decision(
                action="block_malformed_fanout",
                ok=False,
                reason="concurrent_sandboxes must be an integer",
            )
        if as_float != n:
            return Decision(
                action="block_malformed_fanout",
                ok=False,
                reason="concurrent_sandboxes must be a whole integer (no fractions)",
            )
        budget = claim.get("memory_budget_ok")
        if n > 1 and budget is not True:
            return Decision(
                action="block_unbounded_fanout",
                ok=False,
                reason="cap fanout: require memory_budget_ok=true when concurrent_sandboxes > 1",
            )

    if mode == "full_fork_per_sandbox" and bool(claim.get("scale_claimed")):
        return Decision(
            action="block_full_fork_scale",
            ok=False,
            reason="prefer shared template + deltas; full forks amplify redundant pages",
        )

    if action in {"spawn_parallel", "compress_on_llm_wait", "claim_memory_reduction", "project_memory_win"}:
        if action == "compress_on_llm_wait" and not bool(claim.get("during_llm_idle")):
            return Decision(
                action="block_compress_on_critical_path",
                ok=False,
                reason="run expensive compression during LLM wait, not on the hot path",
            )
        if action in {"spawn_parallel", "claim_memory_reduction", "project_memory_win"} and claim.get("validated") is not True:
            return Decision(
                action="block_unvalidated_fanout",
                ok=False,
                reason="require validated=true before scaling or claiming memory wins",
            )
        return Decision(
            action="allow_agentzip_discipline",
            ok=True,
            reason="bounded fanout / measured memory discipline",
        )

    return Decision(
        action="block_unknown_agentzip_action",
        ok=False,
        reason="declare action: spawn_parallel|compress_on_llm_wait|claim_memory_reduction",
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "AGENTZIP_MEMORY.md").is_file():
        blockers.append("missing_docs/AGENTZIP_MEMORY.md")
    if not (repo / "scripts" / "agentzip_memory_gate.py").is_file():
        blockers.append("missing_scripts/agentzip_memory_gate.py")
    blockers.extend(require_dual_skills(repo, "agentzip-memory-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "AGENTZIP_MEMORY.md",
            (
                "template",
                "redundancy",
                "llm wait",
                "fanout",
                "8.7",
                "prefetch",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "agentzip_memory_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/agentzip_memory_discipline.json"
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
            if not isinstance(budget, dict) or budget.get("subscribe_agentzip") is not False:
                blockers.append("fixture_missing:budget.subscribe_agentzip=false")

    ready = len(blockers) == 0
    return {
        "framework": "agentzip-memory-lite",
        "source": SOURCE,
        "thread": THREAD,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "paper_markers": {
            "max_memory_reduction_x": PAPER_MAX_MEMORY_REDUCTION,
            "linux_baseline_x": PAPER_LINUX_BASELINE,
            "slowdown_with_prefetch_x": PAPER_SLOWDOWN_WITH_PREFETCH,
            "note": "illustrative — measure local redundancy before claims",
        },
        "anti_pattern": "high_fanout_without_memory_discipline",
        "budget_note": "cap worktree fanout locally; no AgentZip product under hard cap",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "agentzip-memory-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_fanout_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
