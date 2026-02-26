from __future__ import annotations

import pytest

from scripts.validate_release_branch import ValidationError, validate_release_branch


def _write_version_files(repo_root, android_version: str, ios_version: str) -> None:
    android_file = repo_root / "native-android" / "app" / "build.gradle.kts"
    ios_file = repo_root / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"

    android_file.parent.mkdir(parents=True, exist_ok=True)
    ios_file.parent.mkdir(parents=True, exist_ok=True)

    android_file.write_text(
        f'android {{\n  defaultConfig {{\n    versionName = "{android_version}"\n  }}\n}}\n',
        encoding="utf-8",
    )
    ios_file.write_text(
        f"MARKETING_VERSION = {ios_version};\n",
        encoding="utf-8",
    )


def test_validate_release_branch_passes_when_versions_match(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    result = validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.3")
    assert result["expected_version"] == "1.2.3"
    assert result["android_version"] == "1.2.3"
    assert result["ios_version"] == "1.2.3"


def test_validate_release_branch_rejects_invalid_branch_name(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    with pytest.raises(ValidationError, match="release/vX.Y.Z"):
        validate_release_branch(repo_root=tmp_path, head_ref="develop")


def test_validate_release_branch_rejects_platform_version_mismatch(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.4")
    with pytest.raises(ValidationError, match="Version mismatch"):
        validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.3")


def test_validate_release_branch_rejects_branch_version_mismatch(tmp_path):
    _write_version_files(tmp_path, android_version="1.2.3", ios_version="1.2.3")
    with pytest.raises(ValidationError, match="branch expects 1.2.4"):
        validate_release_branch(repo_root=tmp_path, head_ref="release/v1.2.4")
