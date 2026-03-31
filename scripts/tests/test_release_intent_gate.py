"""Tests for release_intent_gate (Native App Release iOS-only on release branches)."""

import os
import subprocess
import sys
from pathlib import Path

from scripts.release_intent_gate import should_block

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATE_SCRIPT = _REPO_ROOT / "scripts" / "release_intent_gate.py"


def test_release_branch_ios_without_confirm_blocks():
    block, msg = should_block(
        "refs/heads/release/v1.3.15",
        "ios",
        "false",
    )
    assert block is True
    assert "skips Android" in msg


def test_release_branch_ios_with_confirm_ok():
    block, _ = should_block(
        "refs/heads/release/v1.3.15",
        "ios",
        "true",
    )
    assert block is False


def test_release_branch_both_ok():
    block, _ = should_block(
        "refs/heads/release/v1.3.15",
        "both",
        "false",
    )
    assert block is False


def test_release_branch_android_ok():
    block, _ = should_block(
        "refs/heads/release/v1.3.15",
        "android",
        "false",
    )
    assert block is False


def test_develop_ios_ok_without_confirm():
    block, _ = should_block(
        "refs/heads/develop",
        "ios",
        "false",
    )
    assert block is False


def test_feature_branch_ios_ok():
    block, _ = should_block(
        "refs/heads/feat/foo",
        "ios",
        "false",
    )
    assert block is False


def test_main_cli_blocks_release_ios_without_confirm():
    env = {
        **os.environ,
        "GITHUB_REF": "refs/heads/release/v9.8.7",
        "RELEASE_INTENT_PLATFORM": "ios",
        "RELEASE_INTENT_CONFIRM_IOS_ONLY": "false",
    }
    proc = subprocess.run(
        [sys.executable, str(_GATE_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "skips Android" in (proc.stderr or "")


def test_main_cli_ok_release_both():
    env = {
        **os.environ,
        "GITHUB_REF": "refs/heads/release/v9.8.7",
        "RELEASE_INTENT_PLATFORM": "both",
        "RELEASE_INTENT_CONFIRM_IOS_ONLY": "false",
    }
    proc = subprocess.run(
        [sys.executable, str(_GATE_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "release_intent_gate: ok" in (proc.stdout or "")
