#!/usr/bin/env python3
"""Spec governance lite — when SDD pays off (InfoQ / Garg).

Source: https://www.infoq.com/articles/when-spec-driven-development-pays-off/

High-ROI steals only:
  - Verification is the bottleneck (not code writing)
  - Spec baseline buys attribution, not higher bug recall
  - Stage: approved baseline → fresh generation (not inline prompt)
  - Targeting: hard multi-constraint work; skip easy / throwaway
  - Drift findings must cite named invariants; human stays Accountable
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

SOURCE = "https://www.infoq.com/articles/when-spec-driven-development-pays-off/"

CONTROL_POINTS = (
    "specification_authoring",
    "specification_review_gate",
    "guided_generation",
    "drift_detection",
    "reconciliation",
)

HARD_MARKERS = (
    "paywall",
    "entitlement",
    "idempoten",
    "atomic",
    "multi-constraint",
    "multi constraint",
    "signing",
    "store release",
    "app store",
    "play production",
    "timer_completed",
    "wqtu",
    "security",
    "auth",
    "purchase",
    "iap",
    "catalog load",
)

EASY_MARKERS = (
    "typo",
    "rename",
    "readme",
    "comment only",
    "docs only",
    "changelog",
    "whitespace",
    "format",
    "lint fix",
)

FALSE_RECALL_CLAIMS = (
    "raises bug recall",
    "raise recall",
    "more bugs",
    "better bug-find",
    "better bug find",
    "catch more bugs",
)

MODELISH = (
    "model",
    "claude",
    "gpt",
    "gemini",
    "sonnet",
    "opus",
    "haiku",
    "assistant",
    "llm",
)


@dataclass(frozen=True)
class Decision:
    action: str
    ok: bool
    reason: str


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def classify_task(description: str) -> dict[str, str]:
    text = _norm(description)
    if any(m in text for m in HARD_MARKERS):
        return {"hardness": "hard", "description": description}
    if any(m in text for m in EASY_MARKERS):
        return {"hardness": "easy", "description": description}
    return {"hardness": "medium", "description": description}


def evaluate_targeting(task: Mapping[str, object] | str) -> Decision:
    if isinstance(task, str):
        task = classify_task(task)
    hardness = _norm(task.get("hardness", "medium"))
    claim = _norm(task.get("claim", ""))
    if claim and any(c in claim for c in FALSE_RECALL_CLAIMS):
        return Decision(
            action="block_false_recall_claim",
            ok=False,
            reason="InfoQ: baseline did not raise recall; it raises attribution",
        )
    if hardness == "hard":
        return Decision(
            action="require_spec_governance",
            ok=True,
            reason="hard multi-constraint work: use approved baseline + drift attribution",
        )
    if hardness == "easy":
        return Decision(
            action="allow_reason_first",
            ok=True,
            reason="easy tasks: reason-first captures most of the 'spec-first' gain",
        )
    return Decision(
        action="allow_optional_governance",
        ok=True,
        reason="medium: prefer Spec Kit when intent must survive; else reason-first",
    )


def evaluate_generation_mode(
    *,
    hardness: str,
    mode: str,
    baseline_version: str = "",
) -> Decision:
    h = _norm(hardness)
    m = _norm(mode)
    if h != "hard":
        return Decision(
            action="allow_nonhard_generation",
            ok=True,
            reason="non-hard work may use lighter generation modes",
        )
    if m in {
        "single_prompt_spec_then_code",
        "inline_spec_prompt",
        "spec_in_same_prompt",
    }:
        return Decision(
            action="block_inline_spec_prompt",
            ok=False,
            reason="hard work needs staged approved baseline then a fresh generate step",
        )
    if m == "staged_approved_baseline_then_generate" and baseline_version.strip():
        return Decision(
            action="allow_staged_generation",
            ok=True,
            reason="governing artifact + fresh generation record",
        )
    return Decision(
        action="block_missing_staged_baseline",
        ok=False,
        reason="hard work requires staged_approved_baseline_then_generate + baseline_version",
    )


def evaluate_drift_review(
    *,
    findings: Sequence[Mapping[str, object]],
    reconciler: str = "cto-agent",
    accountable_human: str = "ceo",
) -> Decision:
    if not findings:
        return Decision(
            action="block_empty_drift_review",
            ok=False,
            reason="drift review requires at least one finding or explicit empty-ok record",
        )
    unattributed = [
        f
        for f in findings
        if not str(f.get("invariant") or f.get("clause") or "").strip()
    ]
    if unattributed:
        return Decision(
            action="block_unattributed_drift",
            ok=False,
            reason="each finding must cite a named invariant/clause (attribution)",
        )
    if any(m in _norm(accountable_human) for m in MODELISH):
        return Decision(
            action="block_model_accountable",
            ok=False,
            reason="RACI: model may be Responsible for generation; human stays Accountable",
        )
    if not str(reconciler).strip():
        return Decision(
            action="block_missing_reconciler",
            ok=False,
            reason="name who reconciled each drift",
        )
    return Decision(
        action="allow_attributed_drift",
        ok=True,
        reason="findings attributed to named invariants with human accountability",
    )


def _skill_ok(root: Path, name: str) -> bool:
    path = root / name / "SKILL.md"
    return path.is_file() and path.stat().st_size > 0


def evaluate(repo: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not (repo / "docs" / "SPEC_GOVERNANCE.md").is_file():
        blockers.append("missing_docs/SPEC_GOVERNANCE.md")
    if not (repo / "scripts" / "spec_governance_gate.py").is_file():
        blockers.append("missing_scripts/spec_governance_gate.py")
    for skill_root_rel in (".cursor/skills", ".claude/skills"):
        if not _skill_ok(repo / skill_root_rel, "spec-governance-lite"):
            blockers.append(f"missing:{skill_root_rel}/spec-governance-lite")

    docs = repo / "docs" / "SPEC_GOVERNANCE.md"
    if docs.is_file():
        text = docs.read_text(encoding="utf-8").lower()
        required = {
            "targeting": ("targeting",),
            "attribution": ("attribution", "attributable"),
            "human_accountable": ("human accountable", "accountable"),
            "control_point": ("control point", "control points"),
        }
        for key, alts in required.items():
            if not any(a in text for a in alts):
                blockers.append(f"docs_missing:{key}")

    ready = len(blockers) == 0
    return {
        "source": SOURCE,
        "framework": "spec-governance-lite",
        "ready": ready,
        "blockers": blockers,
        "control_points": list(CONTROL_POINTS),
        "pays_off_when": "hard_multi_constraint_capable_but_imperfect_model",
        "does_not_buy": "higher_bug_recall",
        "does_buy": "attributable_contract_anchored_drift_review",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--task", type=str, default="", help="Free-text task to classify")
    args = parser.parse_args(argv)

    report = evaluate(args.repo.resolve())
    if args.task:
        classified = classify_task(args.task)
        report["task"] = classified
        report["targeting"] = asdict(evaluate_targeting(classified))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("READY" if report["ready"] else "BLOCKED")
        for b in report["blockers"]:
            print(f"  - {b}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
