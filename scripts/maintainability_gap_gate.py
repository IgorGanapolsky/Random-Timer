#!/usr/bin/env python3
"""Maintainability gap lite — GitClear / The New Stack duplication signal.

Source:
  https://thenewstack.io/ai-coding-duplication-rose/

GitClear Maintainability Gap (623M changes, 2023–2026): heavy AI users ~+25%
velocity vs self; block duplication +81%; moved-code (refactor) share collapsed
from ~21% (2022) to ~3.8% (2026). Before AI, refactor beat copy-paste ~2:1;
now copy-paste is ~5× likelier.

High-ROI steals for Random Timer:
  - LOC / PR count / “10x” are not ROI
  - Prefer refactor/reuse over copy-paste
  - Tests + refactoring are the mission, not a side quest
  - Use AI as a forklift (large safe lifts), not a racing car
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SOURCE = "https://thenewstack.io/ai-coding-duplication-rose/"

HEALTH_SIGNALS = (
    "reject_loc_as_roi",
    "prefer_refactor_over_copy",
    "tests_refactor_are_the_work",
    "forklift_not_racecar",
)

VANITY_OUTPUT_METRICS = frozenset(
    {
        "lines_of_code",
        "loc",
        "pr_count",
        "prs",
        "features_shipped",
        "tokens",
        "commits",
    }
)

TENX_MARKERS = (
    "10x",
    "10×",
    "ten x",
    "ten times",
)

SIDE_QUEST_MARKERS = frozenset({"side_quest", "later", "optional", "skip", "deferred"})


@dataclass(frozen=True)
class Decision:
    action: str
    ok: bool
    reason: str


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def evaluate_change_claim(claim: Mapping[str, object]) -> Decision:
    metric = _norm(claim.get("metric"))
    text = f"{_norm(claim.get('claim'))} {metric}"
    practice = _norm(claim.get("practice"))

    if metric in VANITY_OUTPUT_METRICS or any(m in text for m in TENX_MARKERS):
        return Decision(
            action="block_output_vanity_roi",
            ok=False,
            reason="LOC/PR/10x output is not maintainability or business ROI",
        )

    if practice in {"copy_paste", "duplicate", "clone"}:
        if not bool(claim.get("searched_existing")):
            return Decision(
                action="block_copy_without_reuse_search",
                ok=False,
                reason="search existing helpers/gates before pasting a twin",
            )

    if practice in {"refactor_move", "extract", "reuse"} and not bool(claim.get("tests_updated")):
        return Decision(
            action="block_refactor_without_tests",
            ok=False,
            reason="refactoring requires tests (the mission, not a side quest)",
        )

    if practice in {"refactor_move", "extract", "reuse"} and bool(claim.get("tests_updated")):
        return Decision(
            action="allow_maintainable_change",
            ok=True,
            reason="refactor/reuse with tests beats copy-paste sprawl",
        )

    if practice in {"copy_paste", "duplicate", "clone"} and bool(claim.get("searched_existing")):
        return Decision(
            action="allow_justified_copy",
            ok=False,
            reason="prefer refactor; justified copy still needs extract follow-up — treat as debt",
        )

    return Decision(
        action="block_unknown_practice",
        ok=False,
        reason="declare practice: refactor_move|extract|reuse|copy_paste",
    )


def evaluate_practice_posture(posture: Mapping[str, object]) -> Decision:
    tests = _norm(posture.get("tests"))
    refactor = _norm(posture.get("refactor"))
    if tests in SIDE_QUEST_MARKERS or refactor in SIDE_QUEST_MARKERS:
        return Decision(
            action="block_side_quest_practices",
            ok=False,
            reason="tests and refactoring are the work, not permission-gated side quests",
        )
    if tests not in {"required", "mandatory", "mission"} or refactor not in {
        "required",
        "mandatory",
        "mission",
    }:
        return Decision(
            action="block_weak_practice_posture",
            ok=False,
            reason="set tests and refactor to required/mission",
        )
    return Decision(
        action="allow_mission_practices",
        ok=True,
        reason="technical discipline is non-optional for software that must last",
    )


def _skill_ok(root: Path, name: str) -> bool:
    path = root / name / "SKILL.md"
    return path.is_file() and path.stat().st_size > 0


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "MAINTAINABILITY_GAP.md").is_file():
        blockers.append("missing_docs/MAINTAINABILITY_GAP.md")
    if not (repo / "scripts" / "maintainability_gap_gate.py").is_file():
        blockers.append("missing_scripts/maintainability_gap_gate.py")
    for skill_root_rel in (".cursor/skills", ".claude/skills"):
        if not _skill_ok(repo / skill_root_rel, "maintainability-gap-lite"):
            blockers.append(f"missing:{skill_root_rel}/maintainability-gap-lite")

    docs = repo / "docs" / "MAINTAINABILITY_GAP.md"
    if docs.is_file():
        text = docs.read_text(encoding="utf-8").lower()
        for needle in (
            "duplication",
            "refactor",
            "side quest",
            "forklift",
            "lines of code",
        ):
            if needle not in text:
                blockers.append(f"docs_missing:{needle.replace(' ', '_')}")

    fixture = repo / "marketing" / "data" / "code_health" / "agent_layer_discipline.json"
    if not fixture.is_file():
        blockers.append("missing_fixture:marketing/data/code_health/agent_layer_discipline.json")
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
            if not isinstance(baseline, dict) or baseline.get("industry_dup_rise_pct") is None:
                blockers.append("fixture_missing:baseline")

    ready = len(blockers) == 0
    return {
        "framework": "maintainability-gap-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "health_signals": list(HEALTH_SIGNALS),
        "industry_snapshot": {
            "velocity_gain_pct_heavy_ai": 25,
            "block_duplication_rise_pct": 81,
            "moved_code_share_2026_pct": 3.8,
        },
        "anti_pattern": "ai_copy_paste_sprawl",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--claim-json", type=Path, default=None)
    args = parser.parse_args(argv)

    report = evaluate(args.repo.resolve())
    if args.claim_json and args.claim_json.is_file():
        claim = json.loads(args.claim_json.read_text(encoding="utf-8"))
        report["claim"] = asdict(evaluate_change_claim(claim))
        report["ready"] = report["ready"] and report["claim"]["ok"]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("READY" if report["ready"] else "BLOCKED")
        for b in report["blockers"]:
            print(f"  - {b}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
