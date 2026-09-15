#!/usr/bin/env python3
"""Agent integrity lite — human is the standard agents are held to.

Inspired by Ofek Haviv / Terra Security (CTech, 2026-09-14):
  https://www.calcalistech.com/ctechnews/article/km507avs3

High-ROI steals for Random Timer (not a pentest product):
  - Researchers/operators set integrity; agents take high-volume speed work
  - Velocity without rigor is a fail (no "looks right" done claims)
  - Continuous research↔product feedback loop ("muscle memory")
  - Formalize tacit expert instincts into agent workflows
  - Human judgment at critical moments only
  - Never declare expert judgment fully captured ("absolute truth")
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SOURCE = "https://www.calcalistech.com/ctechnews/article/km507avs3"

INTEGRITY_PILLARS = (
    "human_standard",
    "velocity_with_rigor",
    "research_product_loop",
    "critical_judgment_human",
)

LOOKS_RIGHT_MARKERS = (
    "looks right",
    "looks correct",
    "seems fine",
    "shipped fast",
    "probably done",
    "assume success",
)

ABSOLUTE_CAPTURE_MARKERS = (
    "absolute truth",
    "fully captured",
    "complete expert judgment",
    "all instincts encoded",
    "playbook finished",
)


@dataclass(frozen=True)
class Decision:
    action: str
    ok: bool
    reason: str


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def evaluate_agent_claim(claim: Mapping[str, object]) -> Decision:
    text = f"{_norm(claim.get('claim'))} {_norm(claim.get('evidence'))}"
    verified = bool(claim.get("verified_readback"))

    if any(m in text for m in ABSOLUTE_CAPTURE_MARKERS):
        return Decision(
            action="block_absolute_expert_capture",
            ok=False,
            reason="never declare expert judgment fully captured; keep finding missed instincts",
        )

    if not verified or any(m in text for m in LOOKS_RIGHT_MARKERS):
        return Decision(
            action="block_velocity_without_integrity",
            ok=False,
            reason="velocity without verified read-back fails the human integrity standard",
        )

    human_at = _norm(claim.get("human_judgment_at"))
    if not human_at:
        return Decision(
            action="block_no_critical_judgment_point",
            ok=False,
            reason="declare where human judgment holds the quality line",
        )

    return Decision(
        action="allow_integrity_backed_claim",
        ok=True,
        reason="verified read-back + human judgment point + no absolute-capture claim",
    )


def evaluate_research_loop(loop: Mapping[str, object]) -> Decision:
    to_product = _norm(loop.get("research_to_product"))
    to_research = _norm(loop.get("product_to_research"))
    if not to_product or not to_research:
        return Decision(
            action="block_one_way_loop",
            ok=False,
            reason="require bidirectional research↔product feedback (muscle memory)",
        )
    return Decision(
        action="allow_research_product_loop",
        ok=True,
        reason="research advances agents; agents expose new research questions",
    )


def _skill_ok(root: Path, name: str) -> bool:
    path = root / name / "SKILL.md"
    return path.is_file() and path.stat().st_size > 0


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "AGENT_INTEGRITY.md").is_file():
        blockers.append("missing_docs/AGENT_INTEGRITY.md")
    if not (repo / "scripts" / "agent_integrity_gate.py").is_file():
        blockers.append("missing_scripts/agent_integrity_gate.py")
    for skill_root_rel in (".cursor/skills", ".claude/skills"):
        if not _skill_ok(repo / skill_root_rel, "agent-integrity-lite"):
            blockers.append(f"missing:{skill_root_rel}/agent-integrity-lite")

    docs = repo / "docs" / "AGENT_INTEGRITY.md"
    if docs.is_file():
        text = docs.read_text(encoding="utf-8").lower()
        for needle in (
            "standard the agents",
            "integrity",
            "research",
            "feedback loop",
            "critical",
            "muscle memory",
        ):
            if needle not in text:
                blockers.append(f"docs_missing:{needle.replace(' ', '_')}")

    fixture = repo / "marketing" / "data" / "integrity" / "native_release_integrity.json"
    if not fixture.is_file():
        blockers.append("missing_fixture:marketing/data/integrity/native_release_integrity.json")
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            for pillar in INTEGRITY_PILLARS:
                if pillar == "research_product_loop":
                    loop = charter.get("research_product_loop") or {}
                    if not isinstance(loop, dict):
                        blockers.append("fixture_loop_not_object")
                    else:
                        decision = evaluate_research_loop(loop)
                        if not decision.ok:
                            blockers.append(f"fixture_loop:{decision.action}")
                elif not str(charter.get(pillar, "")).strip():
                    blockers.append(f"fixture_missing:{pillar}")
            if not charter.get("never_absolute"):
                blockers.append("fixture_missing:never_absolute")

    ready = len(blockers) == 0
    return {
        "framework": "agent-integrity-lite",
        "source": SOURCE,
        "ready": ready,
        "blockers": blockers,
        "pillars": list(INTEGRITY_PILLARS),
        "anti_pattern": "velocity_without_integrity",
        "human_role": "standard_agents_held_to",
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
        report["claim"] = asdict(evaluate_agent_claim(claim))
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
