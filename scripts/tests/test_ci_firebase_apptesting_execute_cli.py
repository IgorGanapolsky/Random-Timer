"""Smoke tests for scripts/ci_firebase_apptesting_execute.sh (no Firebase network calls)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ci_firebase_apptesting_execute.sh"


def test_ci_firebase_apptesting_execute_help_exits_zero() -> None:
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Usage:" in proc.stdout


def test_ci_firebase_apptesting_execute_requires_firebase_app_id(tmp_path: Path) -> None:
    sa_path = tmp_path / "sa.json"
    sa_path.write_text(json.dumps({"project_id": "unit-test-project-only"}), encoding="utf-8")

    env = os.environ.copy()
    env["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_path)
    env.pop("FIREBASE_ANDROID_APP_ID", None)

    proc = subprocess.run(
        ["bash", str(SCRIPT), "--apk", str(tmp_path / "missing.apk")],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert proc.returncode == 1
    assert "FIREBASE_ANDROID_APP_ID" in proc.stderr
