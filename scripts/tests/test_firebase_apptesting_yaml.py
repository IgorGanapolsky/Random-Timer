"""Contract tests for Firebase App Testing agent YAML (Android)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TEST_SUITE_DIR = ROOT / "firebase-apptesting" / "tests"
REQUIRED_SUITE = TEST_SUITE_DIR / "random-timer-smoke.yaml"


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must parse to a mapping"
    return data


def test_firebase_apptesting_smoke_suite_exists() -> None:
    assert REQUIRED_SUITE.is_file(), f"Missing {REQUIRED_SUITE.relative_to(ROOT)}"


def test_firebase_apptesting_smoke_suite_schema() -> None:
    if not REQUIRED_SUITE.is_file():
        pytest.fail("random-timer-smoke.yaml missing")

    doc = _load(REQUIRED_SUITE)
    tests = doc.get("tests")
    assert isinstance(tests, list) and tests, '"tests" must be a non-empty list'

    seen_ids: set[str] = set()
    for index, entry in enumerate(tests):
        assert isinstance(entry, dict), f"tests[{index}] must be a mapping"
        display = entry.get("displayName")
        tid = entry.get("id")
        steps = entry.get("steps")
        assert isinstance(display, str) and display.strip(), f"tests[{index}].displayName required"
        assert isinstance(tid, str) and tid.strip(), f"tests[{index}].id required"
        assert tid not in seen_ids, f"duplicate test id: {tid}"
        seen_ids.add(tid)
        assert isinstance(steps, list) and steps, f"tests[{index}].steps must be non-empty"

        for s_index, step in enumerate(steps):
            assert isinstance(step, dict), f"tests[{index}].steps[{s_index}] must be a mapping"
            goal = step.get("goal")
            final_assert = step.get("finalScreenAssertion")
            assert isinstance(goal, str) and goal.strip(), (
                f"tests[{index}].steps[{s_index}].goal required"
            )
            assert isinstance(final_assert, str) and final_assert.strip(), (
                f"tests[{index}].steps[{s_index}].finalScreenAssertion required"
            )

    prior_ids: set[str] = set()
    for index, entry in enumerate(tests):
        assert isinstance(entry, dict)
        tid = entry.get("id")
        assert isinstance(tid, str)
        prereq = entry.get("prerequisiteTestCaseId")
        if prereq is not None:
            assert isinstance(prereq, str) and prereq.strip()
            assert prereq in prior_ids, (
                f"tests[{index}].prerequisiteTestCaseId {prereq!r} must refer to an earlier test"
            )
        prior_ids.add(tid)


def test_all_yaml_files_under_firebase_apptesting_parse() -> None:
    if not TEST_SUITE_DIR.is_dir():
        pytest.skip("firebase-apptesting/tests not present")

    for path in sorted(TEST_SUITE_DIR.rglob("*.yaml")):
        _load(path)
    for path in sorted(TEST_SUITE_DIR.rglob("*.yml")):
        _load(path)
