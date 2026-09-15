#!/usr/bin/env python3
"""DAIR Academy daily lite — presence gate for scrape→learn→implement loop."""

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

SOURCE = "https://academy.dair.ai/dashboard"
PAPERS = "https://academy.dair.ai/papers"

HEALTH_SIGNALS = (
    "daily_scrape_papers",
    "rank_by_wqtu_profit_roi",
    "queue_implementable_steals",
    "human_agents_md_not_llm_bloat",
)


def evaluate_learn_claim(claim: Mapping[str, object]) -> Decision:
    action = norm(claim.get("action"))
    if action in {"paid_tier_unlock", "academy_paid_unlock"}:
        return Decision(
            action="block_academy_paid_unlock",
            ok=False,
            reason="keep free papers + free dashboard; skip paid Academy unlocks",
        )
    if action == "auto_generate_agents_md":
        return Decision(
            action="block_llm_agents_md_bloat",
            ok=False,
            reason="ETH/AGENTbench: LLM-generated context files hurt; keep human AGENTS.md lean",
        )
    if action in {"scrape_and_rank", "implement_queued_steal"}:
        if not bool(claim.get("tests_planned")):
            return Decision(
                action="block_implement_without_tests",
                ok=False,
                reason="implementable steals require TDD/tests before merge",
            )
        return Decision(
            action="allow_dair_learn_loop",
            ok=True,
            reason="scrape→rank→test→implement is the daily loop",
        )
    return Decision(
        action="block_unknown_dair_action",
        ok=False,
        reason="declare action: scrape_and_rank|implement_queued_steal",
    )


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "DAIR_ACADEMY_DAILY.md").is_file():
        blockers.append("missing_docs/DAIR_ACADEMY_DAILY.md")
    if not (repo / "scripts" / "dair_academy_daily.py").is_file():
        blockers.append("missing_scripts/dair_academy_daily.py")
    if not (repo / "scripts" / "dair_academy_gate.py").is_file():
        blockers.append("missing_scripts/dair_academy_gate.py")
    if not (repo / ".github" / "workflows" / "dair-academy-daily.yml").is_file():
        blockers.append("missing_workflow:dair-academy-daily.yml")
    blockers.extend(require_dual_skills(repo, "dair-academy-daily"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "DAIR_ACADEMY_DAILY.md",
            ("papers", "roi", "implement", "agents.md", "cron", "paid"),
        )
    )
    fixture = repo / "marketing" / "data" / "code_health" / "dair_academy_discipline.json"
    if not fixture.is_file():
        blockers.append("missing_fixture:marketing/data/code_health/dair_academy_discipline.json")
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            for signal in HEALTH_SIGNALS:
                if not charter.get(signal):
                    blockers.append(f"fixture_missing:{signal}")
    artifact = repo / "marketing" / "data" / "dair_daily_learn.json"
    if not artifact.is_file():
        blockers.append("missing_artifact:marketing/data/dair_daily_learn.json")

    ready = len(blockers) == 0
    return {
        "framework": "dair-academy-daily",
        "source": SOURCE,
        "papers": PAPERS,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "anti_pattern": "academy_paid_unlock_or_llm_agents_md_bloat",
    }


def main(argv: list[str] | None = None) -> int:
    return run_presence_cli(
        description=__doc__ or "dair-academy-daily",
        evaluate=evaluate,
        claim_evaluator=evaluate_learn_claim,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
