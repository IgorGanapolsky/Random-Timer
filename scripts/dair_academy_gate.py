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



def _check_fixture(repo: Path) -> list[str]:
    blockers: list[str] = []
    fixture = repo / "marketing" / "data" / "code_health" / "dair_academy_discipline.json"
    if not fixture.is_file():
        return ["missing_fixture:marketing/data/code_health/dair_academy_discipline.json"]
    try:
        charter = json.loads(fixture.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"fixture_invalid_json:{exc}"]
    for signal in HEALTH_SIGNALS:
        if not charter.get(signal):
            blockers.append(f"fixture_missing:{signal}")
    return blockers


def _check_artifact(repo: Path) -> list[str]:
    artifact = repo / "marketing" / "data" / "dair_daily_learn.json"
    if not artifact.is_file():
        return ["missing_artifact:marketing/data/dair_daily_learn.json"]
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"artifact_invalid_json:{exc}"]
    if not isinstance(payload, dict):
        return ["artifact_not_object"]
    blockers: list[str] = []
    if payload.get("framework") != "dair-academy-daily":
        blockers.append("artifact_missing:framework")
    if not payload.get("scraped_at_utc"):
        blockers.append("artifact_missing:scraped_at_utc")
    if int(payload.get("paper_count") or 0) < 1:
        blockers.append("artifact_empty_scrape")
    if not isinstance(payload.get("papers"), list) or not payload.get("papers"):
        blockers.append("artifact_missing:papers")
    if "implement_queue" not in payload or not isinstance(payload.get("implement_queue"), list):
        blockers.append("artifact_missing:implement_queue")
    return blockers


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    required = (
        ("docs/DAIR_ACADEMY_DAILY.md", "missing_docs/DAIR_ACADEMY_DAILY.md"),
        ("scripts/dair_academy_daily.py", "missing_scripts/dair_academy_daily.py"),
        ("scripts/dair_academy_gate.py", "missing_scripts/dair_academy_gate.py"),
        (".github/workflows/dair-academy-daily.yml", "missing_workflow:dair-academy-daily.yml"),
    )
    for rel, code in required:
        if not (repo / rel).is_file():
            blockers.append(code)
    blockers.extend(require_dual_skills(repo, "dair-academy-daily"))
    blockers.extend(
        require_docs_needles(
            repo / "docs" / "DAIR_ACADEMY_DAILY.md",
            ("papers", "roi", "implement", "agents.md", "cron", "paid"),
        )
    )
    blockers.extend(_check_fixture(repo))
    blockers.extend(_check_artifact(repo))
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
