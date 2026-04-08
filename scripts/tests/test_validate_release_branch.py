from __future__ import annotations

import pytest

from scripts.validate_release_branch import ValidationError, validate_release_branch


def _write_version_files(repo_root, android_version: str, ios_version: str) -> None:
    android_file = repo_root / "native-android" / "app" / "build.gradle.kts"
    ios_file = repo_root / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"

    android_file.parent.mkdir(parents=True, exist_ok=True)
    ios_file.parent.mkdir(parents=True, exist_ok=True)

    android_file.write_text(
        f'android {{\n  defaultConfig {{\n    versionCode = 1\n    versionName = "{android_version}"\n  }}\n}}\n',
        encoding="utf-8",
    )
    ios_file.write_text(
        f"MARKETING_VERSION = {ios_version};\nCURRENT_PROJECT_VERSION = 1;\n",
        encoding="utf-8",
    )


def _write_release_notes(repo_root, version: str, body: str | None = None) -> None:
    notes_file = repo_root / "release-notes" / f"{version}.md"
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    notes_file.write_text(
        body or f"# Release {version}\n\n## Summary\nShipped fixes.\n",
        encoding="utf-8",
    )


def test_validate_release_branch_passes_when_versions_match(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    _write_release_notes(tmp_path, version="1.2.3")
    result = validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.3")
    assert result["expected_version"] == "1.2.3"
    assert result["android_version"] == "1.2.3"
    assert result["ios_version"] == "1.2.3"
    assert result["release_notes_path"] == "release-notes/1.2.3.md"


def test_validate_release_branch_rejects_invalid_branch_name(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    with pytest.raises(ValidationError, match="release/vX.Y.Z or hotfix/vX.Y.Z"):
        validate_release_branch(repo_root=tmp_path, head_ref="develop")


def test_validate_release_branch_rejects_platform_version_mismatch(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.4")
    _write_release_notes(tmp_path, version="1.2.3")
    with pytest.raises(ValidationError, match="Version mismatch"):
        validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.3")


def test_validate_release_branch_rejects_branch_version_mismatch(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    _write_release_notes(tmp_path, version="1.2.3")
    with pytest.raises(ValidationError, match="branch expects 1.2.4"):
        validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.4")


def test_validate_hotfix_branch_passes_when_versions_match(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.4", ios_version="1.2.4")
    _write_release_notes(tmp_path, version="1.2.4")
    result = validate_release_branch(repo_root=tmp_path, head_ref="hotfix/v1.2.4")
    assert result["expected_version"] == "1.2.4"
    assert result["android_version"] == "1.2.4"
    assert result["ios_version"] == "1.2.4"


def test_validate_hotfix_branch_rejects_platform_version_mismatch(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.4", ios_version="1.2.5")
    _write_release_notes(tmp_path, version="1.2.4")
    with pytest.raises(ValidationError, match="Version mismatch"):
        validate_release_branch(repo_root=tmp_path, head_ref="hotfix/v1.2.4")


def test_validate_hotfix_branch_rejects_branch_version_mismatch(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.4", ios_version="1.2.4")
    _write_release_notes(tmp_path, version="1.2.4")
    with pytest.raises(ValidationError, match="branch expects 1.2.5"):
        validate_release_branch(repo_root=tmp_path, head_ref="hotfix/v1.2.5")


def test_validate_release_branch_rejects_bare_hotfix_prefix(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.4", ios_version="1.2.4")
    with pytest.raises(ValidationError, match="release/vX.Y.Z or hotfix/vX.Y.Z"):
        validate_release_branch(repo_root=tmp_path, head_ref="hotfix")


def test_validate_release_branch_rejects_missing_versioned_release_notes(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    with pytest.raises(ValidationError, match="Versioned release notes missing"):
        validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.3")


def test_validate_release_branch_rejects_placeholder_versioned_release_notes(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    _write_release_notes(tmp_path, version="1.2.3", body="# Release 1.2.3\n\nTODO: fill this in.\n")
    with pytest.raises(ValidationError, match="placeholder"):
        validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.3")
