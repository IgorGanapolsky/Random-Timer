"""Tests for HydraFusion-inspired multi-model orchestration router.

Patterns from GitHub Project HydraFusion (2026-09-04):
Single | Cascade | Critique, least-complex workflow that clears quality bar.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "hydrafusion_route.py"

# Import once available; tests that need the module will fail until implemented.
sys.path.insert(0, str(ROOT / "scripts"))


def test_script_exists() -> None:
    assert SCRIPT.is_file(), "scripts/hydrafusion_route.py must exist"


def test_single_for_scoped_utility() -> None:
    from hydrafusion_route import route_task

    plan = route_task(
        {
            "task": "List open PRs with gh and summarize CI status",
            "capabilities": ["tool_use"],
            "risk": "low",
            "files_touched_estimate": 0,
        }
    )
    assert plan["pattern"] == "single"
    assert plan["draft_category"] == "Quick"
    assert plan["critic"] is None
    assert plan["escalate_category"] is None
    assert plan["principles"]["bounded_execution"] is True


def test_cascade_for_implementation_with_gate() -> None:
    from hydrafusion_route import route_task

    plan = route_task(
        {
            "task": "Implement Play Billing Library 8 upgrade with unit tests",
            "capabilities": ["code_generation", "debugging"],
            "risk": "medium",
            "files_touched_estimate": 8,
        }
    )
    assert plan["pattern"] == "cascade"
    assert plan["draft_category"] == "Quick"
    assert plan["escalate_category"] in {"Deep", "UltraBrain"}
    assert plan["quality_gate"]["require_tests"] is True
    assert plan["quality_gate"]["require_evidence"] is True


def test_critique_for_security_or_store_publish() -> None:
    from hydrafusion_route import route_task

    plan = route_task(
        {
            "task": "Review store listing metadata and privacy claims before publish",
            "capabilities": ["reasoning", "code_generation"],
            "risk": "high",
            "files_touched_estimate": 12,
            "domain": "store_publishing",
        }
    )
    assert plan["pattern"] == "critique"
    assert plan["critic"]["isolated"] is True
    assert plan["critic"]["tool_less"] is True
    assert plan["critic"]["family"] != plan["draft_family"]
    assert plan["revise_once"] is True


def test_fail_safe_and_validated_routing_fields() -> None:
    from hydrafusion_route import route_task, validate_plan

    plan = route_task(
        {
            "task": "Refactor timer service teardown across Android and iOS",
            "capabilities": ["reasoning", "code_generation", "debugging"],
            "risk": "high",
            "files_touched_estimate": 20,
        }
    )
    errors = validate_plan(plan)
    assert errors == []
    assert plan["principles"]["fail_safe_application"] is True
    assert plan["principles"]["complete_accounting"] is True
    assert plan["principles"]["isolated_review"] == (plan["pattern"] == "critique")
    assert "legs" in plan and isinstance(plan["legs"], list)
    assert plan["legs"][0]["role"] == "draft"


def test_quality_gate_accept_vs_escalate() -> None:
    from hydrafusion_route import evaluate_quality_gate

    accept = evaluate_quality_gate(
        {
            "tests_passed": True,
            "evidence_present": True,
            "secrets_leaked": False,
            "patch_validated": True,
        }
    )
    assert accept["accepted"] is True
    assert accept["escalate"] is False

    reject = evaluate_quality_gate(
        {
            "tests_passed": False,
            "evidence_present": True,
            "secrets_leaked": False,
            "patch_validated": True,
        }
    )
    assert reject["accepted"] is False
    assert reject["escalate"] is True


def test_cli_json_output() -> None:
    payload = {
        "task": "Fix typo in README",
        "capabilities": ["code_generation"],
        "risk": "low",
        "files_touched_estimate": 1,
    }
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(payload)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    plan = json.loads(proc.stdout)
    assert plan["pattern"] == "single"
    assert "source" in plan
