"""TDD: HydraFusion cascade cost sim + runtime gate (InfoQ high-ROI)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "hydrafusion_route.py"

sys.path.insert(0, str(ROOT / "scripts"))


def test_cascade_expected_cost_beats_always_frontier() -> None:
    from hydrafusion_route import estimate_cascade_cost

    # InfoQ-aligned: ~65% cost cut vs always-Opus when cheap drafts often pass.
    result = estimate_cascade_cost(
        draft_cost=1.0,
        frontier_cost=10.0,
        gate_cost=0.2,
        pass_rate=0.8,
    )
    assert result["pattern"] == "cascade"
    assert result["always_frontier_cost"] == 10.0
    assert result["expected_cost"] < 4.0
    assert result["savings_pct"] >= 0.60
    assert result["beats_always_frontier"] is True


def test_cascade_low_pass_rate_does_not_claim_infoq_savings() -> None:
    from hydrafusion_route import estimate_cascade_cost

    result = estimate_cascade_cost(
        draft_cost=1.0,
        frontier_cost=10.0,
        gate_cost=0.2,
        pass_rate=0.5,
    )
    assert result["beats_always_frontier"] is True
    assert result["savings_pct"] < 0.60
    assert result["meets_infoq_savings_proxy"] is False


def test_critique_cost_accounts_all_legs() -> None:
    from hydrafusion_route import estimate_critique_cost

    result = estimate_critique_cost(
        draft_cost=8.0,
        critic_cost=1.5,
        revision_cost=4.0,
        frontier_cost=10.0,
    )
    assert result["expected_cost"] == pytest.approx(13.5)
    assert result["legs_accounted"] == ["draft", "critique", "revision"]
    assert result["complete_cost_accounting"] is True


def test_run_cascade_accepts_passing_draft() -> None:
    from hydrafusion_route import run_cascade

    out = run_cascade(
        {
            "draft_artifact": "patch",
            "draft_cost": 1.0,
            "escalate_cost": 10.0,
            "gate_cost": 0.1,
            "gate_signals": {
                "tests_passed": True,
                "evidence_present": True,
                "secrets_leaked": False,
                "patch_validated": True,
            },
        }
    )
    assert out["accepted"] is True
    assert out["escalated"] is False
    assert out["total_cost"] == pytest.approx(1.1)
    assert out["fail_safe"] is True


def test_run_cascade_escalates_on_gate_reject() -> None:
    from hydrafusion_route import run_cascade

    out = run_cascade(
        {
            "draft_artifact": "patch",
            "draft_cost": 1.0,
            "escalate_cost": 10.0,
            "gate_cost": 0.1,
            "gate_signals": {
                "tests_passed": False,
                "evidence_present": True,
                "secrets_leaked": False,
                "patch_validated": True,
            },
        }
    )
    assert out["accepted"] is False
    assert out["escalated"] is True
    assert out["total_cost"] == pytest.approx(11.1)
    assert "tests_passed" in out["gate"]["reasons"]


def test_run_cascade_fail_safe_on_cancel() -> None:
    from hydrafusion_route import run_cascade

    out = run_cascade(
        {
            "draft_artifact": "patch",
            "draft_cost": 1.0,
            "escalate_cost": 10.0,
            "gate_cost": 0.1,
            "cancelled": True,
            "gate_signals": {
                "tests_passed": True,
                "evidence_present": True,
                "secrets_leaked": False,
                "patch_validated": True,
            },
        }
    )
    assert out["accepted"] is False
    assert out["escalated"] is False
    assert out["apply_patch"] is False
    assert out["fail_safe"] is True


def test_capability_signals_drive_pattern() -> None:
    from hydrafusion_route import score_capability_signals

    signals = score_capability_signals(
        {
            "capabilities": [
                "multi_step_reasoning",
                "code_generation",
                "structured_debugging",
                "advanced_tool_use",
            ],
            "risk": "medium",
            "files_touched_estimate": 6,
        }
    )
    assert signals["capability_count"] == 4
    assert signals["recommended_pattern"] in {"cascade", "critique"}


def test_route_plan_includes_cost_estimate_for_cascade() -> None:
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
    assert "cost_estimate" in plan
    assert plan["cost_estimate"]["beats_always_frontier"] is True
    assert plan["cost_estimate"]["savings_pct"] >= 0.5


def test_cli_simulate_cost() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--simulate-cost",
            json.dumps(
                {
                    "pattern": "cascade",
                    "draft_cost": 1.0,
                    "frontier_cost": 10.0,
                    "gate_cost": 0.2,
                    "pass_rate": 0.8,
                }
            ),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["meets_infoq_savings_proxy"] is True
    assert payload["savings_pct"] >= 0.60


def test_cli_run_cascade() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-cascade",
            json.dumps(
                {
                    "draft_cost": 1.0,
                    "escalate_cost": 9.0,
                    "gate_cost": 0.1,
                    "gate_signals": {
                        "tests_passed": True,
                        "evidence_present": True,
                        "secrets_leaked": False,
                        "patch_validated": True,
                    },
                }
            ),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["accepted"] is True
    assert payload["total_cost"] == pytest.approx(1.1)
