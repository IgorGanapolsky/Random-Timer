#!/usr/bin/env python3
"""Value-center fitness — InfoQ / Rohrer VSM (agency + coherence).

Source:
  https://www.infoq.com/news/2026/09/autonomous-software-teams/

Steal the method, not a reorg: replace "autonomous team" slogans with
value-center answers (Viable Systems Model five questions), classify
essential vs accidental dependencies, and require coherence fitness
(gates/docs) alongside local agency.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SOURCE = "https://www.infoq.com/news/2026/09/autonomous-software-teams/"

VSM_QUESTIONS = (
    "what_value",
    "how_coordinate",
    "how_fit_together",
    "whats_out_there",
    "who_are_we",
)

NORTH_STAR_MARKERS = (
    "wqtu",
    "timer_completed",
    "$100",
    "100/day",
    "paywall",
    "after-tax",
)

ACCIDENTAL_MARKERS = (
    "full bmad",
    "bmad-method",
    "copilot code review",
    "copilot review",
    "paid saas",
    "webinar",
    "foundry model router",
    "openrouter primary",
    "ori login",
    "33 skills",
    "plugin farm",
)

ESSENTIAL_MARKERS = (
    "play billing",
    "app store",
    "testflight",
    "posthog",
    "wqtu",
    "timer_completed",
    "signing",
    "oidc",
    "internal-signoff",
    "store listing",
)


@dataclass(frozen=True)
class Decision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def evaluate_charter(charter: Mapping[str, object]) -> Decision:
    """Fail closed on product-only autonomy slogans without value + coherence."""
    value = _norm(str(charter.get("value", "")))
    mode = _norm(str(charter.get("mode", "")))
    north = _norm(str(charter.get("north_star", "")))
    coordination = _norm(str(charter.get("coordination", "")))

    value_ok = any(m in value or m in north for m in NORTH_STAR_MARKERS)
    if not value_ok:
        return Decision(
            action="block_product_not_value",
            ok=False,
            reason="Rohrer: talk value (WQTU / paywall / $100/day), not feature shipping",
        )

    if mode in {"autonomous", "autonomy", "autonomous_team"}:
        return Decision(
            action="block_autonomy_slogan",
            ok=False,
            reason="prefer agency_and_coherence over pure autonomous-team slogans",
        )

    if mode not in {"agency_and_coherence", "agency+coherence", "nested_networked"}:
        return Decision(
            action="block_missing_coherence_mode",
            ok=False,
            reason="mode must be agency_and_coherence (or nested_networked)",
        )

    if not coordination:
        return Decision(
            action="block_no_coordination",
            ok=False,
            reason="value centers need an explicit coordination mechanism",
        )

    return Decision(
        action="allow_value_center",
        ok=True,
        reason="north-star value + agency/coherence + coordination present",
    )


def evaluate_vsm_answers(answers: Mapping[str, object]) -> Decision:
    missing = [
        key
        for key in VSM_QUESTIONS
        if not str(answers.get(key, "")).strip()
    ]
    if missing:
        return Decision(
            action="block_incomplete_vsm",
            ok=False,
            reason=f"missing VSM answers: {','.join(missing)}",
        )
    return Decision(
        action="allow_vsm",
        ok=True,
        reason="all five Viable Systems Model questions answered",
    )


def classify_dependency(description: str) -> str:
    text = _norm(description)
    if any(m in text for m in ACCIDENTAL_MARKERS):
        return "accidental"
    if any(m in text for m in ESSENTIAL_MARKERS):
        return "essential"
    # Default: treat unclear coupling as accidental until proven essential.
    return "accidental"


def _skill_ok(root: Path, name: str) -> bool:
    path = root / name / "SKILL.md"
    return path.is_file() and path.stat().st_size > 0


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "VALUE_CENTER.md").is_file():
        blockers.append("missing_docs/VALUE_CENTER.md")
    if not (repo / "scripts" / "value_center_gate.py").is_file():
        blockers.append("missing_scripts/value_center_gate.py")

    for skill_root_rel in (".cursor/skills", ".claude/skills"):
        if not _skill_ok(repo / skill_root_rel, "value-center-lite"):
            blockers.append(f"missing:{skill_root_rel}/value-center-lite")

    docs = repo / "docs" / "VALUE_CENTER.md"
    if docs.is_file():
        text = docs.read_text(encoding="utf-8")
        lowered = text.lower()
        if "wqtu" not in lowered and "timer_completed" not in lowered:
            blockers.append("docs_missing_north_star_marker")
        for needle in (
            "what value",
            "how do we coordinate",
            "how do we fit together",
            "what's out there",
            "who are we",
        ):
            # Allow curly apostrophe variants.
            alt = needle.replace("'", "’")
            if needle not in lowered and alt not in lowered:
                blockers.append(f"docs_missing_vsm:{re.sub(r'[^a-z]+', '_', needle)}")

    ready = len(blockers) == 0
    return {
        "source": SOURCE,
        "framework": "value-center-vsm-lite",
        "ready": ready,
        "blockers": blockers,
        "vsm_questions": list(VSM_QUESTIONS),
        "shift": {
            "from": ["products", "autonomy", "autonomous_product_teams"],
            "to": ["value", "agency_and_coherence", "nested_networked_org"],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--charter-json",
        type=Path,
        help="Optional charter JSON to evaluate with VSM answers",
    )
    args = parser.parse_args(argv)

    report = evaluate(args.repo.resolve())
    if args.charter_json and args.charter_json.is_file():
        payload = json.loads(args.charter_json.read_text(encoding="utf-8"))
        charter_d = evaluate_charter(payload.get("charter", payload))
        vsm_d = evaluate_vsm_answers(payload.get("vsm", payload.get("answers", {})))
        deps = payload.get("dependencies", [])
        classified = [
            {"description": d, "class": classify_dependency(str(d))} for d in deps
        ]
        report["charter"] = asdict(charter_d)
        report["vsm"] = asdict(vsm_d)
        report["dependencies"] = classified
        report["ready"] = report["ready"] and charter_d.ok and vsm_d.ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "READY" if report["ready"] else "BLOCKED"
        print(f"value-center-gate: {status}")
        for b in report["blockers"]:
            print(f"  - {b}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
