#!/usr/bin/env python3
"""Greptile free-only gate — never pay for Greptile reviews.

Policy from CEO + Greptile support (Muzz Khan): free tier is available if we
disable reviews on repos that generate charges:
  - private repos (not covered by free/OSS allowances)
  - public repos with fewer than 50 stars (no OSS grant)

Open-source repos with an OSI license and 50+ stars get 100 free review credits.
Hard rule: never update a payment method for Greptile; never enable flex/paid
credits. Prefer label filter `needs-greptile-review` only on free-eligible repos.
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

SOURCE = "https://app.greptile.com/hermes-mobile/-/settings/review#when-reviews"

HEALTH_SIGNALS = (
    "free_tier_only",
    "no_payment_method",
    "disable_reviews_on_private_repos",
    "disable_reviews_on_public_under_50_stars",
    "label_filter_needs_greptile_review",
    "no_flex_paid_credits",
    "oss_grant_50_stars_osi_only",
)


def evaluate_greptile_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))

    if action in {
        "add_payment_method",
        "enable_flex_credits",
        "upgrade_paid_plan",
        "pay_for_greptile",
    }:
        return Decision(
            action="block_greptile_paid",
            ok=False,
            reason="Greptile is free-only — never add payment or flex credits",
        )

    if action in {"enable_reviews_private_repo", "review_private_repo"}:
        return Decision(
            action="block_private_repo_reviews",
            ok=False,
            reason="private repos are billable — disable Greptile reviews there",
        )

    if action in {"enable_reviews_low_star_public", "review_public_under_50_stars"}:
        stars = claim.get("stars")
        try:
            n = int(stars)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            n = -1
        if n < 50:
            return Decision(
                action="block_under_50_star_reviews",
                ok=False,
                reason="public repos need 50+ stars for OSS free grant — disable otherwise",
            )

    if action in {"claim_free_tier", "use_free_only"}:
        if claim.get("payment_method_present") is True:
            return Decision(
                action="block_payment_method_present",
                ok=False,
                reason="remove/avoid Greptile payment method for free-only posture",
            )
        return Decision(
            action="allow_free_tier",
            ok=True,
            reason="free-tier Greptile posture",
        )

    if action in {"label_filter", "needs_greptile_review_only"}:
        return Decision(
            action="allow_label_filter",
            ok=True,
            reason="limit reviews to needs-greptile-review on free-eligible repos",
        )

    return Decision(
        action="block_unknown_greptile_action",
        ok=False,
        reason=(
            "declare action: use_free_only|add_payment_method|"
            "enable_reviews_private_repo|label_filter"
        ),
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "GREPTILE_FREE_ONLY.md").is_file():
        blockers.append("missing_docs/GREPTILE_FREE_ONLY.md")
    if not (repo / "scripts" / "greptile_free_only_gate.py").is_file():
        blockers.append("missing_scripts/greptile_free_only_gate.py")
    blockers.extend(require_dual_skills(repo, "greptile-free-only"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "GREPTILE_FREE_ONLY.md",
            (
                "free",
                "payment",
                "private",
                "50 stars",
                "needs-greptile-review",
                "flex",
                "oss",
                "never pay",
            ),
        )
    )

    fixture = (
        repo / "marketing" / "data" / "code_health" / "greptile_free_only_discipline.json"
    )
    if not fixture.is_file():
        blockers.append(
            "missing_fixture:marketing/data/code_health/greptile_free_only_discipline.json"
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
            if not isinstance(budget, dict) or budget.get("paid_greptile") is not False:
                blockers.append("fixture_missing:budget.paid_greptile=false")

    ready = len(blockers) == 0
    return {
        "framework": "greptile-free-only",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "paid_flex_credits_or_private_repo_autoview",
        "budget_note": "Greptile free-only; never pay; $20/mo cap excludes Greptile spend",
        "settings_url": SOURCE,
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "greptile-free-only",
        evaluate=evaluate,
        claim_evaluator=evaluate_greptile_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
