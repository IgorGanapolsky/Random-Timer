#!/usr/bin/env python3
"""Diff Delta lite — GitClear durable AI ROI (not token vanity).

Source:
  https://www.gitclear.com/

GitClear scores AI by Diff Delta (lineage-aware durable change): moves,
renames, and reformatting keep lineage so rewrites stop counting toward a
model. Token-to-durable-production yield: generated → accepted → committed →
merged → day 7/30/90. Homepage research markers: ~8× duplicate blocks since
AI assistants went mainstream; ~9× higher churn from AI power users who also
ship 4–10× more volume.

High-ROI steals for Random Timer ($20/mo budget — do NOT buy GitClear SaaS):
  - Score durable Diff Delta proxies (Sonar dup density, surviving merges),
    not tokens / LOC / “model wrote more”
  - Pre-merge leakage is not ROI; count survival after merge
  - Flag AI hotspot directories (defect/dup rise) before compounding
  - Same yardstick for human vs LLM cohorts
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

SOURCE = "https://www.gitclear.com/"

HEALTH_SIGNALS = (
    "score_durable_diff_delta",
    "yield_to_production_not_tokens",
    "flag_ai_hotspot_dirs",
    "same_yardstick_human_llm",
)

VANITY_METRICS = frozenset(
    {
        "tokens",
        "token_count",
        "lines_of_code",
        "loc",
        "code_volume",
        "ai_volume",
        "features_shipped",
        "commits",
    }
)

PRE_MERGE_STAGES = frozenset(
    {"generated", "accepted", "committed", "pre_merge", "draft"}
)
SURVIVAL_STAGES = frozenset({"merged", "day_7", "day_30", "day_90", "production"})


def evaluate_roi_claim(claim: Mapping[str, object]) -> Decision:
    metric = norm(claim.get("metric"))
    text = f"{norm(claim.get('claim'))} {metric}"
    stage = norm(claim.get("stage"))

    if metric in VANITY_METRICS or "4x more code" in text or "10x" in text:
        return Decision(
            action="block_token_vanity_roi",
            ok=False,
            reason="tokens/LOC/volume are not Diff Delta; score durable surviving change",
        )

    if metric not in {"diff_delta", "durable_diff_delta", "surviving_share", "rework_rate"}:
        return Decision(
            action="block_unknown_roi_metric",
            ok=False,
            reason="use metric: diff_delta|durable_diff_delta|surviving_share|rework_rate",
        )

    if stage in PRE_MERGE_STAGES:
        return Decision(
            action="block_pre_merge_as_roi",
            ok=False,
            reason="pre-merge leakage is not durable ROI; wait for merge survival",
        )

    if not bool(claim.get("same_yardstick")):
        return Decision(
            action="block_apples_oranges_cohort",
            ok=False,
            reason="compare human vs LLM with the same Diff Delta yardstick",
        )

    surviving = claim.get("surviving_share_pct")
    if surviving is None or float(surviving) < 50:
        return Decision(
            action="block_weak_survival",
            ok=False,
            reason="require surviving_share_pct >= 50 at day_30+ (proxy for durable yield)",
        )

    return Decision(
        action="allow_durable_roi",
        ok=True,
        reason="durable Diff Delta with same-yardstick survival evidence",
    )


def evaluate_yield_stage(posture: Mapping[str, object]) -> Decision:
    stage = norm(posture.get("stage"))
    count_as_roi = bool(posture.get("count_as_roi"))
    if count_as_roi and stage in PRE_MERGE_STAGES:
        return Decision(
            action="block_pre_merge_as_roi",
            ok=False,
            reason="generated/accepted/committed volume is pre-merge leakage, not ROI",
        )
    if count_as_roi and stage in SURVIVAL_STAGES:
        return Decision(
            action="allow_post_merge_survival",
            ok=True,
            reason="post-merge / day_N survival is the Diff Delta yield stage that counts",
        )
    if not count_as_roi:
        return Decision(
            action="allow_stage_observed",
            ok=True,
            reason="observing funnel stages without claiming ROI is fine",
        )
    return Decision(
        action="block_unknown_yield_stage",
        ok=False,
        reason="declare stage: generated|accepted|committed|merged|day_7|day_30|day_90",
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "DIFF_DELTA.md").is_file():
        blockers.append("missing_docs/DIFF_DELTA.md")
    if not (repo / "scripts" / "diff_delta_gate.py").is_file():
        blockers.append("missing_scripts/diff_delta_gate.py")
    blockers.extend(require_dual_skills(repo, "diff-delta-lite"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "DIFF_DELTA.md",
            (
                "diff delta",
                "yield",
                "tokens",
                "hotspot",
                "yardstick",
                "moves",
            ),
        )
    )

    fixture = repo / "marketing" / "data" / "code_health" / "diff_delta_discipline.json"
    if not fixture.is_file():
        blockers.append("missing_fixture:marketing/data/code_health/diff_delta_discipline.json")
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
            if not isinstance(baseline, dict) or baseline.get("industry_dup_block_multiplier") is None:
                blockers.append("fixture_missing:baseline")

    ready = len(blockers) == 0
    return {
        "framework": "diff-delta-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "industry_snapshot": {
            "duplicate_block_multiplier": 8,
            "ai_power_user_churn_multiplier": 9,
            "ai_volume_multiplier_range": "4-10x",
        },
        "anti_pattern": "token_vanity_ai_roi",
        "budget_note": "encode Diff Delta discipline; do not subscribe to GitClear under $20/mo cap",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "diff-delta-lite",
        evaluate=evaluate,
        claim_evaluator=evaluate_roi_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
