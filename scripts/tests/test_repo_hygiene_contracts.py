"""Regression checks for repository hygiene contracts."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_instruction_docs_do_not_claim_unwired_memory_backends() -> None:
    for relative_path in ("CLAUDE.md", "AGENTS.md"):
        contents = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "mcp-memory-gateway" not in contents
        assert "Langsmith" not in contents


def test_marketing_post_index_uses_repo_relative_paths() -> None:
    posts_path = REPO_ROOT / "marketing" / "data" / "posts.jsonl"
    records = [
        json.loads(line)
        for line in posts_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert records, "posts.jsonl should contain at least one record"
    for record in records:
        for key in ("diagram_svg_path", "markdown_path"):
            assert not record[key].startswith("/"), f"{key} must stay repo-relative"


def test_runtime_temp_paths_are_environment_backed() -> None:
    expected_absent = {
        "scripts/capture_ios_store_screenshots.sh": "/tmp/appstore_screenshots",
        "native-ios/RandomTimerUITests/RandomTimerUITests.swift": "/tmp/appstore_screenshots",
        "scripts/device-tests/adb/lib/common.sh": "/tmp/device_test_notif_dump.txt",
        "native-android/fastlane/Appfile": "/tmp/play-service-account.json",
        "native-ios/upload_to_testflight.py": "/tmp/RandomTimer.xcarchive",
    }

    for relative_path, forbidden_snippet in expected_absent.items():
        contents = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert forbidden_snippet not in contents, f"{relative_path} still hardcodes {forbidden_snippet}"


def test_hygiene_check_matches_current_repo_policy() -> None:
    contents = (REPO_ROOT / "scripts" / "hygiene-check.sh").read_text(encoding="utf-8")
    assert '"GEMINI.md"' in contents
    assert '"BUGBOT.md"' in contents
    assert "Possible secret or temp-path leak" not in contents
    forbidden_pattern = r"PRIVATE_KEY\|SECRET_KEY\|password.*=\|" + "/private" + "/tmp/" + r"\|/tmp/"
    assert forbidden_pattern not in contents
