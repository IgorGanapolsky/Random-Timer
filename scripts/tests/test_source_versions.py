from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import source_versions


def _write_repo_version_files(repo_root: Path, android_line: str = "versionCode = 11") -> None:
    android_file = repo_root / "native-android" / "app" / "build.gradle.kts"
    ios_file = repo_root / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"
    android_file.parent.mkdir(parents=True, exist_ok=True)
    ios_file.parent.mkdir(parents=True, exist_ok=True)

    android_file.write_text(
        f'android {{\n  defaultConfig {{\n    {android_line}\n    versionName = "1.2.2"\n  }}\n}}\n',
        encoding="utf-8",
    )
    ios_file.write_text(
        "MARKETING_VERSION = 1.2.2;\nCURRENT_PROJECT_VERSION = 14;\n",
        encoding="utf-8",
    )


def test_extract_android_version_code_handles_elvis_fallback():
    text = 'versionCode = ciVersionCode ?: 11\nversionName = "1.2.2"\n'
    assert source_versions.extract_android_version_code(text) == 11


def test_read_source_versions_returns_all_expected_values(tmp_path: Path):
    _write_repo_version_files(tmp_path, android_line="versionCode = ciVersionCode ?: 11")
    versions = source_versions.read_source_versions(tmp_path)

    assert versions == {
        "android": {"version_name": "1.2.2", "version_code": 11},
        "ios": {"version_name": "1.2.2", "build_number": 14},
    }


def test_cli_shell_output_is_sourceable(tmp_path: Path):
    _write_repo_version_files(tmp_path)
    script = Path(__file__).resolve().parents[1] / "source_versions.py"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--format", "shell"],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = dict(line.split("=", 1) for line in result.stdout.strip().splitlines())
    assert lines["ANDROID_VERSION_NAME"] == "1.2.2"
    assert lines["ANDROID_VERSION_CODE"] == "11"
    assert lines["IOS_VERSION_NAME"] == "1.2.2"
    assert lines["IOS_BUILD_NUMBER"] == "14"


def test_cli_json_output_matches_reader(tmp_path: Path):
    _write_repo_version_files(tmp_path)
    script = Path(__file__).resolve().parents[1] / "source_versions.py"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["android"]["version_code"] == 11
    assert payload["ios"]["build_number"] == 14
