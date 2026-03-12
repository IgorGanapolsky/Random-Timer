import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
INTERNAL_DISTRIBUTION_WORKFLOW = ROOT / ".github/workflows/internal-distribution.yml"
NORTH_STAR_GUARDRAIL_WORKFLOW = ROOT / ".github/workflows/north-star-guardrail.yml"
NORTH_STAR_OPS_WORKFLOW = ROOT / ".github/workflows/north-star-ops.yml"
WEEKLY_EXPERIMENT_WORKFLOW = ROOT / ".github/workflows/weekly-north-star-experiment.yml"
WORKFLOW_CONTRACT = ROOT / "docs/workflow.md"


def test_ci_workflow_uses_real_python_suite_and_has_no_legacy_skip_path():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "python -m pytest scripts/tests/ -q" in source
    assert "pytest -q tests/python" not in source
    assert "No tests/python directory found; skipping legacy pytest suite." not in source


def test_ci_workflow_only_fails_north_star_on_real_guardrail_enforcement_conditions():
    source = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "--enforce-guardrail" in source
    assert "--require-posthog-when-active" in source
    assert re.search(r"(?<!-when-active)\b--require-posthog\b", source) is None


def test_internal_distribution_workflow_verifies_store_uploads_and_uploads_evidence():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/verify_release.py" in source
    assert "internal-distribution-verification" in source


def test_internal_distribution_workflow_emits_platform_specific_release_artifacts():
    source = INTERNAL_DISTRIBUTION_WORKFLOW.read_text(encoding="utf-8")

    assert "scripts/verify_release.py --platform ios" in source
    assert "scripts/verify_release.py --platform android" in source
    assert "--json-out /tmp/ios-release-verification.json" in source
    assert "--json-out /tmp/android-release-verification.json" in source
    assert "ios-release-verification" in source
    assert "android-release-verification" in source


def test_north_star_guardrail_workflow_runs_daily_ops_pipeline():
    source = NORTH_STAR_GUARDRAIL_WORKFLOW.read_text(encoding="utf-8")

    assert "scripts/north_star_guardrail.py" in source
    assert "scripts/attribution_feedback.py" in source
    assert "scripts/north_star_ops.py" in source
    assert "marketing/data/north_star_ops.json" in source
    assert "marketing/data/north_star_ops.md" in source


def test_north_star_ops_workflow_exists_and_runs_report_script():
    source = NORTH_STAR_OPS_WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/north_star_ops.py" in source
    assert "north-star-ops-report" in source


def test_weekly_experiment_workflow_builds_a_single_experiment_brief():
    source = WEEKLY_EXPERIMENT_WORKFLOW.read_text(encoding="utf-8")

    assert "python scripts/north_star_guardrail.py" in source
    assert "python scripts/attribution_feedback.py" in source
    assert "python scripts/north_star_ops.py" in source
    assert "python scripts/north_star_experiment.py" in source
    assert "marketing/data/north_star_experiment.json" in source
    assert "marketing/data/north_star_experiment.md" in source


def test_workflow_contract_exists_and_points_at_canonical_proof_commands():
    source = WORKFLOW_CONTRACT.read_text(encoding="utf-8")

    assert "python3 -m pytest -q scripts/tests/" in source
    assert "cd native-android" in source
    assert "./gradlew testDebugUnitTest" in source
    assert "xcodebuild test -project RandomTimer.xcodeproj -scheme RandomTimer" in source
    assert "maestro test .maestro/ios-smoke-test.yaml" in source
    assert "scripts/tests" in source
    assert "tests/python" not in source


def test_dead_play_precondition_stub_is_removed():
    assert not (ROOT / "scripts/play_precondition_triage.py").exists()
