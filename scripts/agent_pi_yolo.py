"""Pi-style gated engineering harness (pi-yolo).

Reusable primitives from agentic engineering workflows (plan → approval →
worktree impl → tests → concise evidence). Default task class: issue_to_pr.

Episode framing: https://music.youtube.com/watch?v=SxuQs9GGYbk

Fleet cap: FLEET_MONTHLY_CAP_USD ($20). Prefer single-agent lane before
multi-agent orchestration.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

FLEET_MONTHLY_CAP_USD = 20.0

ALLOWED_PLATFORMS = frozenset(
    {
        "local_pi_yolo",
        "agent_pi_yolo",
        "pi_yolo",
        "pi_agent_harness",
    }
)
OVERBROAD_MARKERS = (
    "autonomous_coding_company",
    "unrestricted_multi_agent",
    "full_repo_rewrite",
    "production_cloud_admin",
)

ALLOWED_TASK_CLASSES = frozenset(
    {
        "issue_to_pr",
        "repo_onboarding",
        "test_gap",
        "pr_review",
        "docs_byproduct",
        "write_tests",
        "fix_bug",
    }
)
AMBIGUOUS_MARKERS = (
    "ambiguous_product",
    "vague_rewrite",
    "build_everything",
    "autonomous_company",
)

QUALITY_COMMANDS = (
    "python3 -m pytest scripts/tests/test_agent_pi_yolo.py -q",
    "python3 -m pytest scripts/tests/ -q --tb=line",
    "cd native-android && ./gradlew testDebugUnitTest",
    "cd native-ios && xcodebuild -scheme RandomTimer test",
)

DEFAULT_LOOP = (
    "plan",
    "approve_or_yolo",
    "implement_in_worktree",
    "run_tests_self_review",
    "emit_evidence_package",
)


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_pi_yolo",
            ok=True,
            reason="local Pi-style harness under operating cap",
        )
    if any(marker in name for marker in OVERBROAD_MARKERS):
        return ControlDecision(
            action="block_overbroad_autonomy",
            ok=False,
            reason="prove single-agent issue→PR lane before broad autonomy",
        )
    return ControlDecision(
        action="block_unknown_platform",
        ok=False,
        reason="unknown pi-yolo platform denied",
    )


def evaluate_task_class(*, task_class: str) -> ControlDecision:
    name = _norm(task_class)
    if any(marker in name for marker in AMBIGUOUS_MARKERS):
        return ControlDecision(
            action="block_ambiguous_task",
            ok=False,
            reason="clarify the spec first; do not automate ambiguous product work",
        )
    if name in ALLOWED_TASK_CLASSES:
        return ControlDecision(
            action="allow_task_class",
            ok=True,
            reason=f"task class {name} is measurable and recurring",
        )
    return ControlDecision(
        action="block_unknown_task_class",
        ok=False,
        reason="use issue_to_pr|repo_onboarding|test_gap|pr_review|docs_byproduct",
    )


def evaluate_plan_gate(
    *,
    has_plan: bool,
    plan_approved: bool,
    yolo: bool,
    acceptance_criteria: Sequence[str],
) -> ControlDecision:
    if not has_plan:
        return ControlDecision(
            action="block_missing_plan",
            ok=False,
            reason="agent must write a plan before implementation",
        )
    criteria = tuple(c for c in acceptance_criteria if str(c).strip())
    if yolo and criteria:
        return ControlDecision(
            action="allow_yolo_plan",
            ok=True,
            reason="yolo auto-approves plan when acceptance criteria are explicit",
        )
    if plan_approved:
        return ControlDecision(
            action="allow_approved_plan",
            ok=True,
            reason="plan approved",
        )
    return ControlDecision(
        action="require_plan_approval",
        ok=False,
        reason="approve or revise the plan before coding",
    )


def validate_repo_rules(
    *,
    touches_secrets: bool,
    production_change: bool,
    adds_dependency: bool,
    dependency_approved: bool,
    uses_worktree: bool,
) -> ControlDecision:
    if touches_secrets:
        return ControlDecision(
            action="block_secrets",
            ok=False,
            reason="no secrets in commits or chat",
        )
    if production_change:
        return ControlDecision(
            action="block_production_change",
            ok=False,
            reason="no direct production/cloud changes from this harness",
        )
    if adds_dependency and not dependency_approved:
        return ControlDecision(
            action="block_unapproved_dependency",
            ok=False,
            reason="dependency additions require explicit approval",
        )
    if not uses_worktree:
        return ControlDecision(
            action="block_no_worktree",
            ok=False,
            reason="implement in a branch/worktree, never on the shared tip",
        )
    return ControlDecision(
        action="allow_repo_rules",
        ok=True,
        reason="repo rules satisfied",
    )


def evaluate_definition_of_done(
    *,
    files_changed: Sequence[str],
    tests_run: Sequence[str],
    tests_passed: bool,
    risks_documented: bool,
    rollback_notes: bool,
    evidence_paths: Sequence[str],
) -> ControlDecision:
    if not files_changed:
        return ControlDecision(
            action="block_incomplete_dod",
            ok=False,
            reason="files_changed required",
        )
    if not tests_run or not tests_passed:
        return ControlDecision(
            action="block_incomplete_dod",
            ok=False,
            reason="tests must be run and pass",
        )
    if not risks_documented or not rollback_notes:
        return ControlDecision(
            action="block_incomplete_dod",
            ok=False,
            reason="risks and rollback notes required",
        )
    if not evidence_paths:
        return ControlDecision(
            action="block_incomplete_dod",
            ok=False,
            reason="evidence package path required",
        )
    return ControlDecision(
        action="allow_definition_of_done",
        ok=True,
        reason="definition of done complete",
    )


def build_evidence_package(
    *,
    files_changed: Sequence[str],
    tests_run: Sequence[str],
    tests_passed: bool,
    risks: Sequence[str],
    rollback_notes: str,
    plan_summary: str,
) -> dict[str, Any]:
    return {
        "plan_summary": plan_summary,
        "files_changed": list(files_changed),
        "tests_run": list(tests_run),
        "tests_passed": bool(tests_passed),
        "risks": list(risks),
        "rollback_notes": rollback_notes,
        "quality_commands": list(QUALITY_COMMANDS),
        "loop": list(DEFAULT_LOOP),
    }


def record_kpi(
    *,
    task_id: str,
    minutes_to_mergeable_pr: float,
    human_review_minutes: float,
    first_pass_tests: bool,
    rework: bool,
    usd_per_success: float,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "minutes_to_mergeable_pr": float(minutes_to_mergeable_pr),
        "human_review_minutes": float(human_review_minutes),
        "first_pass_tests": bool(first_pass_tests),
        "rework": bool(rework),
        "usd_per_success": float(usd_per_success),
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "note": (
            "ROI uses net time saved minus tooling/review/rework; "
            "do not count volume of drafts as success."
        ),
    }


def run_harness(
    *,
    platform: str,
    task_class: str,
    has_plan: bool,
    plan_approved: bool,
    yolo: bool,
    acceptance_criteria: Sequence[str],
    touches_secrets: bool,
    production_change: bool,
    adds_dependency: bool,
    dependency_approved: bool,
    uses_worktree: bool,
    files_changed: Sequence[str],
    tests_run: Sequence[str],
    tests_passed: bool,
    risks_documented: bool,
    rollback_notes: bool,
    evidence_paths: Sequence[str],
    plan_summary: str,
    risks: Sequence[str],
    rollback_text: str,
) -> dict[str, Any]:
    platform_d = evaluate_platform(platform=platform)
    task_d = evaluate_task_class(task_class=task_class)
    plan_d = evaluate_plan_gate(
        has_plan=has_plan,
        plan_approved=plan_approved,
        yolo=yolo,
        acceptance_criteria=acceptance_criteria,
    )
    rules_d = validate_repo_rules(
        touches_secrets=touches_secrets,
        production_change=production_change,
        adds_dependency=adds_dependency,
        dependency_approved=dependency_approved,
        uses_worktree=uses_worktree,
    )
    dod_d = evaluate_definition_of_done(
        files_changed=files_changed,
        tests_run=tests_run,
        tests_passed=tests_passed,
        risks_documented=risks_documented,
        rollback_notes=rollback_notes,
        evidence_paths=evidence_paths,
    )
    evidence = build_evidence_package(
        files_changed=files_changed,
        tests_run=tests_run,
        tests_passed=tests_passed,
        risks=risks,
        rollback_notes=rollback_text,
        plan_summary=plan_summary,
    )
    ok = platform_d.ok and task_d.ok and plan_d.ok and rules_d.ok and dod_d.ok
    return {
        "ok": ok,
        "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
        "platform": asdict(platform_d),
        "task": asdict(task_d),
        "plan_gate": asdict(plan_d),
        "repo_rules": asdict(rules_d),
        "definition_of_done": asdict(dod_d),
        "evidence": evidence,
        "proxy_vs_ground_truth": {
            "note": (
                "minutes_to_mergeable_pr and usd_per_success are KPIs to measure "
                "across 5–10 tasks; single-run claims remain unverified."
            )
        },
    }


def repo_guide(*, root: Path | None = None) -> dict[str, Any]:
    base = root or Path.cwd()
    return {
        "repo": str(base),
        "architecture_map": [
            "native-android/",
            "native-ios/",
            "scripts/",
            "docs/",
            "marketing/data/",
            "AGENTS.md",
            "CLAUDE.md",
        ],
        "quality_commands": list(QUALITY_COMMANDS),
        "definition_of_done": [
            "files_changed",
            "tests_run_and_passed",
            "risks_documented",
            "rollback_notes",
            "evidence_package",
        ],
        "rules": [
            "no_secrets",
            "no_production_changes",
            "no_dependency_additions_without_approval",
            "use_worktree_or_feature_branch",
        ],
        "loop": list(DEFAULT_LOOP),
        "default_task_class": "issue_to_pr",
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="pi-yolo — Pi-style gated issue→PR harness"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_guide = sub.add_parser("guide", help="print repo harness guide")
    p_guide.add_argument("--json", action="store_true")

    p_check = sub.add_parser("check", help="evaluate a harness run")
    p_check.add_argument("--platform", default="local_pi_yolo")
    p_check.add_argument("--task-class", default="issue_to_pr")
    p_check.add_argument("--plan", action="store_true")
    p_check.add_argument("--approved", action="store_true")
    p_check.add_argument("--yolo", action="store_true")
    p_check.add_argument("--criteria", action="append", default=[])
    p_check.add_argument("--secrets", action="store_true")
    p_check.add_argument("--production", action="store_true")
    p_check.add_argument("--add-dep", action="store_true")
    p_check.add_argument("--dep-approved", action="store_true")
    p_check.add_argument("--worktree", action="store_true", default=True)
    p_check.add_argument("--no-worktree", action="store_true")
    p_check.add_argument("--file", action="append", default=[])
    p_check.add_argument("--test", action="append", default=[])
    p_check.add_argument("--tests-passed", action="store_true")
    p_check.add_argument("--risks-ok", action="store_true")
    p_check.add_argument("--rollback-ok", action="store_true")
    p_check.add_argument("--evidence", action="append", default=[])
    p_check.add_argument("--plan-summary", default="")
    p_check.add_argument("--risk", action="append", default=[])
    p_check.add_argument("--rollback", default="")
    p_check.add_argument("--json", action="store_true")

    p_doctor = sub.add_parser("doctor", help="health check")
    p_doctor.add_argument("--json", action="store_true")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "guide":
        payload = repo_guide()
        print(json.dumps(payload, indent=2 if args.json else None))
        return 0

    if args.cmd == "doctor":
        payload = {
            "ok": True,
            "command": "pi-yolo",
            "module": "scripts/agent_pi_yolo.py",
            "fleet_monthly_cap_usd": FLEET_MONTHLY_CAP_USD,
            "default_task_class": "issue_to_pr",
            "loop": list(DEFAULT_LOOP),
        }
        print(json.dumps(payload, indent=2 if args.json else None))
        return 0

    report = run_harness(
        platform=args.platform,
        task_class=args.task_class,
        has_plan=args.plan,
        plan_approved=args.approved,
        yolo=args.yolo,
        acceptance_criteria=tuple(args.criteria or ()),
        touches_secrets=args.secrets,
        production_change=args.production,
        adds_dependency=args.add_dep,
        dependency_approved=args.dep_approved,
        uses_worktree=(not args.no_worktree) and args.worktree,
        files_changed=tuple(args.file or ()),
        tests_run=tuple(args.test or ()),
        tests_passed=args.tests_passed,
        risks_documented=args.risks_ok,
        rollback_notes=args.rollback_ok,
        evidence_paths=tuple(args.evidence or ()),
        plan_summary=args.plan_summary,
        risks=tuple(args.risk or ()),
        rollback_text=args.rollback,
    )
    print(json.dumps(report, indent=2 if args.json else None))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
