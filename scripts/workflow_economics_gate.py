#!/usr/bin/env python3
"""Workflow economics lite — escape AI pilot purgatory.

Inspired by the operating brief on turning isolated AI demos into measurable,
repeatable operational systems (completion loop + economic metrics), not
model shopping or orphan chatbots.

High-ROI steals:
  - Prefer high-volume digital workflows with a clear baseline
  - Design for completion: trigger→context→decision→action→verification→audit
  - One accountable owner + weekly economic metric
  - Human approval only at material risk points
  - Block interest/demo claims as ROI
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

COMPLETION_STAGES = (
    "trigger",
    "context_retrieval",
    "decision",
    "action",
    "verification",
    "audit_trail",
)

ECONOMIC_METRICS = frozenset(
    {
        "automation_rate",
        "cycle_time_hours",
        "cycle_time_minutes",
        "cost_per_completed_task",
        "quality_rate",
        "capacity_hours_released",
        "conversion_uplift",
        "wqtu",
        "paywall_attempt_success_rate",
    }
)

VANITY_METRICS = frozenset(
    {
        "interest",
        "demo",
        "likes",
        "usage",
        "dau",
        "sessions",
        "prompts",
        "tokens",
    }
)

CHATBOT_KINDS = frozenset({"chatbot", "enterprise_chatbot", "generic_assistant"})


@dataclass(frozen=True)
class Decision:
    action: str
    ok: bool
    reason: str


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def evaluate_workflow_charter(charter: Mapping[str, object]) -> Decision:
    name = _norm(charter.get("name"))
    kind = _norm(charter.get("kind"))
    owner = _norm(charter.get("owner"))
    metric = _norm(charter.get("metric"))
    sor = _norm(charter.get("system_of_record"))
    stages = charter.get("stages") or {}
    baseline = charter.get("baseline") or {}

    if kind in CHATBOT_KINDS or "chatbot" in name:
        if not owner or metric in VANITY_METRICS or not isinstance(baseline, dict) or not baseline:
            return Decision(
                action="block_orphan_pilot",
                ok=False,
                reason="chatbots without owner+baseline+economic metric stay in pilot purgatory",
            )

    if not owner:
        return Decision(
            action="block_no_owner",
            ok=False,
            reason="assign one accountable process owner",
        )

    if not isinstance(baseline, dict) or baseline.get("value") is None or not baseline.get("metric"):
        return Decision(
            action="block_no_baseline",
            ok=False,
            reason="establish a numeric baseline before claiming improvement",
        )

    if metric in VANITY_METRICS or metric not in ECONOMIC_METRICS:
        return Decision(
            action="block_non_economic_metric",
            ok=False,
            reason=f"metric must be economic ({', '.join(sorted(ECONOMIC_METRICS))})",
        )

    if not sor:
        return Decision(
            action="block_no_system_of_record",
            ok=False,
            reason="integrate with a system of record (no copy/paste-only pilots)",
        )

    if not isinstance(stages, dict):
        return Decision(
            action="block_incomplete_completion_loop",
            ok=False,
            reason="stages must map the completion loop",
        )
    missing = [s for s in COMPLETION_STAGES if not str(stages.get(s, "")).strip()]
    if missing:
        return Decision(
            action="block_incomplete_completion_loop",
            ok=False,
            reason=f"missing stages: {','.join(missing)}",
        )

    approval = _norm(charter.get("approval_policy"))
    if not approval:
        return Decision(
            action="block_no_approval_policy",
            ok=False,
            reason="declare where humans approve (material risk only)",
        )

    return Decision(
        action="allow_completion_workflow",
        ok=True,
        reason="owner + baseline + economic metric + SoR + full completion loop",
    )


def evaluate_pilot_claim(claim: Mapping[str, object]) -> Decision:
    metric = _norm(claim.get("metric"))
    evidence = _norm(claim.get("evidence"))
    if metric in VANITY_METRICS or "demo" in evidence or "likes" in evidence or "interest" in evidence:
        if metric not in ECONOMIC_METRICS:
            return Decision(
                action="block_interest_not_roi",
                ok=False,
                reason="interest/demo/usage is not an economic outcome",
            )
    if metric not in ECONOMIC_METRICS:
        return Decision(
            action="block_non_economic_metric",
            ok=False,
            reason="claim a weekly economic metric",
        )
    try:
        baseline = float(claim.get("baseline_value"))  # type: ignore[arg-type]
        current = float(claim.get("current_value"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return Decision(
            action="block_missing_comparison",
            ok=False,
            reason="provide baseline_value and current_value",
        )
    if current == baseline:
        return Decision(
            action="block_no_movement",
            ok=False,
            reason="current equals baseline — no demonstrated improvement",
        )
    return Decision(
        action="allow_economic_claim",
        ok=True,
        reason="economic metric moved vs baseline",
    )


def _skill_ok(root: Path, name: str) -> bool:
    path = root / name / "SKILL.md"
    return path.is_file() and path.stat().st_size > 0


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "WORKFLOW_ECONOMICS.md").is_file():
        blockers.append("missing_docs/WORKFLOW_ECONOMICS.md")
    if not (repo / "scripts" / "workflow_economics_gate.py").is_file():
        blockers.append("missing_scripts/workflow_economics_gate.py")
    for skill_root_rel in (".cursor/skills", ".claude/skills"):
        if not _skill_ok(repo / skill_root_rel, "workflow-economics-lite"):
            blockers.append(f"missing:{skill_root_rel}/workflow-economics-lite")

    docs = repo / "docs" / "WORKFLOW_ECONOMICS.md"
    if docs.is_file():
        text = docs.read_text(encoding="utf-8").lower()
        for needle in (
            "pilot purgatory",
            "completion",
            "accountable",
            "weekly",
            "system of record",
        ):
            if needle not in text:
                blockers.append(f"docs_missing:{needle.replace(' ', '_')}")

    fixture = repo / "marketing" / "data" / "workflows" / "native_release_completion.json"
    if not fixture.is_file():
        blockers.append("missing_fixture:marketing/data/workflows/native_release_completion.json")
    else:
        try:
            charter = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blockers.append(f"fixture_invalid_json:{exc}")
        else:
            decision = evaluate_workflow_charter(charter)
            if not decision.ok:
                blockers.append(f"fixture_charter:{decision.action}")

    ready = len(blockers) == 0
    return {
        "framework": "workflow-economics-lite",
        "ready": ready,
        "blockers": blockers,
        "completion_stages": list(COMPLETION_STAGES),
        "economic_metrics": sorted(ECONOMIC_METRICS),
        "anti_pattern": "orphan_enterprise_chatbot",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--charter-json", type=Path, default=None)
    args = parser.parse_args(argv)

    report = evaluate(args.repo.resolve())
    if args.charter_json and args.charter_json.is_file():
        charter = json.loads(args.charter_json.read_text(encoding="utf-8"))
        report["charter"] = asdict(evaluate_workflow_charter(charter))
        report["ready"] = report["ready"] and report["charter"]["ok"]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("READY" if report["ready"] else "BLOCKED")
        for b in report["blockers"]:
            print(f"  - {b}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
