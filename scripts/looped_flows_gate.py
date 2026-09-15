#!/usr/bin/env python3
"""Looped Flows lite — recurrent reasoning depth without parameter bloat.

Source:
  https://arxiv.org/abs/2609.11801
  https://x.com/omarsar0/status/2098807354343260366

Paper (Suleymanzade et al., Thinking with Looped Flows): looped models get more
reasoning at inference by recurrently updating a hidden state — without adding
parameters. Training usually backprops through only the last one/few updates, so
early updates never learn to set up later ones. Looped flows train recurrence
with local denoising objectives (decreasing noise + shared noise ties steps).
Inference integrates a probability flow: finer time grid = more compute; different
initial noise can yield different valid answers on multi-solution tasks.

High-ROI steals for Random Timer agents (operational analogy — we do not train NNs):
  - Prefer more verify/refine loops over “bigger model / more tools”
  - Design early steps so later steps inherit useful state (not last-check-only)
  - Each loop has a local objective chained to the next (shared context)
  - Spend more compute (finer grid) on harder failures; allow multi-path answers
"""

from __future__ import annotations

import json
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

SOURCE = "https://arxiv.org/abs/2609.11801"
THREAD = "https://x.com/omarsar0/status/2098807354343260366"

HEALTH_SIGNALS = (
    "reason_by_recurrence_not_params",
    "early_steps_set_up_later",
    "local_objectives_chain",
    "adaptive_compute_grid",
)

PARAM_STRATEGIES = frozenset(
    {"add_parameters", "bigger_model", "more_tools", "scale_params", "upgrade_model"}
)


def evaluate_loop_plan(plan: Mapping[str, object]) -> Decision:
    strategy = norm(plan.get("strategy"))
    text = f"{norm(plan.get('claim'))} {strategy}"
    loops = int(plan.get("loops") or 0)

    if strategy in PARAM_STRATEGIES or "larger model" in text or "bigger model" in text:
        return Decision(
            action="block_params_over_recurrence",
            ok=False,
            reason="prefer recurrent verify/refine loops over adding parameters/tools",
        )

    if strategy not in {"recurrent", "looped", "looped_flow"}:
        return Decision(
            action="block_unknown_loop_strategy",
            ok=False,
            reason="declare strategy: recurrent|looped|looped_flow",
        )

    if loops < 2:
        return Decision(
            action="block_single_shot_as_loop",
            ok=False,
            reason="recurrent reasoning needs loops >= 2 (finer grid when harder)",
        )

    if not bool(plan.get("local_objectives")):
        return Decision(
            action="block_untied_loops",
            ok=False,
            reason="each loop needs a local objective tied to the next (shared context)",
        )

    if not bool(plan.get("early_sets_up_later")):
        return Decision(
            action="block_last_step_only_plan",
            ok=False,
            reason="early steps must set up later ones — not last-check-only gradients",
        )

    if not bool(plan.get("adaptive_grid")):
        return Decision(
            action="block_fixed_shallow_grid",
            ok=False,
            reason="allow finer compute grid on harder problems",
        )

    return Decision(
        action="allow_looped_reasoning",
        ok=True,
        reason="chained local objectives with adaptive recurrent depth",
    )


def evaluate_training_posture(posture: Mapping[str, object]) -> Decision:
    """Operational stand-in for paper training: how we 'train' multi-step agent loops."""
    span = norm(posture.get("gradient_span"))
    if span in {"last_one", "last_two", "final_only"}:
        return Decision(
            action="block_last_step_only",
            ok=False,
            reason="last-step-only credit assignment leaves early loops untrained",
        )
    if span == "local" and bool(posture.get("shared_noise")) and bool(
        posture.get("decreasing_noise")
    ):
        return Decision(
            action="allow_local_denoising_chain",
            ok=True,
            reason="local objectives + shared/decreasing noise tie early→late updates",
        )
    return Decision(
        action="block_weak_training_posture",
        ok=False,
        reason="set gradient_span=local with shared_noise and decreasing_noise",
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "LOOPED_FLOWS.md").is_file():
        blockers.append("missing_docs/LOOPED_FLOWS.md")
    if not (repo / "scripts" / "looped_flows_gate.py").is_file():
        blockers.append("missing_scripts/looped_flows_gate.py")
    blockers.extend(require_dual_skills(repo, "looped-flows-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "LOOPED_FLOWS.md",
            (
                "recurrent",
                "parameters",
                "early",
                "local",
                "denoising",
                "grid",
                "gradients",
            ),
        )
    )

    fixture = repo / "marketing" / "data" / "code_health" / "looped_flows_discipline.json"
    if not fixture.is_file():
        blockers.append("missing_fixture:marketing/data/code_health/looped_flows_discipline.json")
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            for signal in HEALTH_SIGNALS:
                if not charter.get(signal):
                    blockers.append(f"fixture_missing:{signal}")
            baseline = charter.get("baseline") or {}
            if not isinstance(baseline, dict) or baseline.get("arxiv") is None:
                blockers.append("fixture_missing:baseline")

    ready = len(blockers) == 0
    return {
        "framework": "looped-flows-lite",
        "source": SOURCE,
        "thread": THREAD,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "paper_snapshot": {
            "title": "Thinking with Looped Flows",
            "arxiv": "2609.11801",
            "arc_agi_1_pct": 58.8,
            "arc_agi_2_pct": 12.2,
        },
        "anti_pattern": "last_step_only_credit_assignment",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "looped-flows-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_loop_plan,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
