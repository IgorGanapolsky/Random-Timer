from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts import regression_guards as guards


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "regression_guards.py"


def test_relevant_paths_detects_release_and_voice_regression_surfaces():
    paths = guards.relevant_paths(
        [
            ".github/workflows/android-production-retry.yml",
            "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt",
            "native-ios/RandomTimer.xcodeproj/project.pbxproj",
            "README.md",
        ]
    )

    assert ".github/workflows/android-production-retry.yml" in paths
    assert "native-android/app/src/main/java/com/iganapolsky/randomtimer/ui/screens/TimerSetupScreen.kt" in paths
    assert "native-ios/RandomTimer.xcodeproj/project.pbxproj" in paths
    assert "README.md" not in paths


def test_relevant_paths_skips_unrelated_files():
    assert guards.relevant_paths(["README.md", "docs/foo.md"]) == []


def test_run_checks_passes_on_current_repo():
    assert guards.run_checks(ROOT, include_voice=True, include_ios_firebase=True) == []


def test_cli_skips_unrelated_paths():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--mode", "staged", "--paths", "README.md"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "skip" in result.stdout


def test_cli_runs_for_release_guard_paths():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(ROOT),
            "--mode",
            "staged",
            "--paths",
            ".github/workflows/android-production-retry.yml",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "regression_guards: ok" in result.stdout


def test_pre_commit_invokes_regression_guards():
    source = (ROOT / "scripts" / "pre-commit").read_text(encoding="utf-8")

    assert "python3 scripts/regression_guards.py --mode staged" in source
