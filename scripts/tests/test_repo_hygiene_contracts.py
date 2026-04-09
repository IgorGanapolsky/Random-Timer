from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / ".github/settings.yml"
ISSUE_MANAGEMENT = ROOT / ".github/issue-management.yml"
PROJECT = ROOT / ".github/project.yml"
BUG_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/bug_report.md"
FEATURE_TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE/feature_request.md"
MAIN_WORKFLOW = ROOT / ".github/workflows/main.yml"


def test_operational_reliability_contract_doc_exists() -> None:
    path = ROOT / "docs" / "OPERATIONAL_RELIABILITY.md"
    text = path.read_text(encoding="utf-8")
    assert path.is_file()
    for marker in (
        "Ground truth vs proxy",
        "Contradiction protocol",
        "review_count_metric_id",
    ):
        assert marker in text, f"{path} must document {marker}"


def test_instruction_docs_do_not_claim_unwired_memory_backends() -> None:
    for relative_path in ("CLAUDE.md", "AGENTS.md"):
        contents = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "mcp-memory-gateway" not in contents
        assert "Langsmith" not in contents


def test_marketing_post_index_uses_repo_relative_paths() -> None:
    posts_path = ROOT / "marketing" / "data" / "posts.jsonl"
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
    expected_markers = {
        "scripts/shell/capture_ios_store_screenshots.sh": (
            "APPSTORE_SCREENSHOT_OUTPUT_DIR",
            "TMPDIR",
        ),
        "native-ios/RandomTimerUITests/RandomTimerUITests.swift": (
            "APPSTORE_SCREENSHOT_OUTPUT_DIR",
            "NSTemporaryDirectory",
        ),
        "scripts/device-tests/adb/lib/common.sh": (
            "TMPDIR",
            "NOTIF_DUMP",
        ),
        "native-android/fastlane/Appfile": (
            "GOOGLE_PLAY_JSON_KEY_PATH",
            "Dir.tmpdir",
        ),
        "native-ios/upload_to_testflight.py": (
            "RANDOM_TIMER_UPLOAD_TMPDIR",
            "tempfile.gettempdir",
        ),
    }

    for relative_path, required_markers in expected_markers.items():
        contents = (ROOT / relative_path).read_text(encoding="utf-8")
        for marker in required_markers:
            assert marker in contents, f"{relative_path} must stay environment-backed via {marker}"


def test_hygiene_check_matches_current_repo_policy() -> None:
    contents = (ROOT / "scripts" / "shell" / "hygiene-check.sh").read_text(encoding="utf-8")
    assert '"GEMINI.md"' in contents
    assert '"BUGBOT.md"' in contents
    assert "Possible secret or temp-path leak" not in contents


def test_gitignore_covers_known_local_artifact_buckets() -> None:
    contents = (ROOT / ".gitignore").read_text(encoding="utf-8")
    expected_entries = (
        ".venv-chatterbox/",
        "native-android/.venv-chatterbox/",
        ".rlhf/feedback.jsonl",
        ".rlhf/rejection-ledger.jsonl",
        "evidence/",
    )
    for entry in expected_entries:
        assert entry in contents, f".gitignore must ignore {entry}"


def test_settings_define_canonical_labels_used_by_automation():
    source = SETTINGS.read_text(encoding="utf-8")

    for label in (
        "triage",
        "type: bug",
        "type: enhancement",
        "priority: critical",
        "priority: high",
        "priority: medium",
        "priority: low",
        "status: blocked",
        "status: in-progress",
        "status: needs-review",
        "status: stale",
        "pr-state:draft",
        "pr-state:ci_running",
        "pr-state:ci_green",
        "pr-state:blocked",
    ):
        assert f'- name: "{label}"' in source


def test_issue_templates_use_canonical_type_labels():
    assert "labels: type: bug, triage" in BUG_TEMPLATE.read_text(encoding="utf-8")
    assert "labels: type: enhancement, triage" in FEATURE_TEMPLATE.read_text(encoding="utf-8")


def test_main_workflow_labeling_matches_settings_taxonomy():
    source = MAIN_WORKFLOW.read_text(encoding="utf-8")

    assert "labels.push('type: bug', 'triage');" in source
    assert "labels.push('type: enhancement');" in source


def test_issue_management_and_project_configs_use_enhancement_not_feature_alias():
    assert '"type: enhancement"' in ISSUE_MANAGEMENT.read_text(encoding="utf-8")
    project_source = PROJECT.read_text(encoding="utf-8")
    assert 'name: "type: enhancement"' in project_source
    assert 'name: "type: feature"' not in project_source


def test_project_description_is_not_stale():
    source = PROJECT.read_text(encoding="utf-8")

    assert "password management" not in source.lower()
    assert "tactical timer app" in source
