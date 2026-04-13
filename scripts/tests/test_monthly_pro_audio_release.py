import json
from pathlib import Path

import pytest

from scripts.monthly_pro_audio_release import (
    MonthlyReleaseError,
    next_patch_version,
    render_store_release_notes,
    render_versioned_release_notes,
    resolve_release_version,
    write_release_notes,
)


def _write_minimal_repo(root: Path, *, android_version: str = "1.2.3", ios_version: str = "1.2.3") -> None:
    (root / "native-android/app").mkdir(parents=True)
    (root / "native-ios/RandomTimer.xcodeproj").mkdir(parents=True)
    (root / "content/pro_audio").mkdir(parents=True)
    (root / "native-android/app/build.gradle.kts").write_text(
        f'''
android {{
    defaultConfig {{
        versionCode = ciVersionCode ?: 123
        versionName = "{android_version}"
    }}
}}
''',
        encoding="utf-8",
    )
    (root / "native-ios/RandomTimer.xcodeproj/project.pbxproj").write_text(
        f"""
MARKETING_VERSION = {ios_version};
CURRENT_PROJECT_VERSION = 456;
""",
        encoding="utf-8",
    )
    manifest = {
        "activePackId": "2026-05_combat_sports_cadence",
        "packs": [
            {
                "id": "2026-05_combat_sports_cadence",
                "releaseMonth": "2026-05",
                "theme": "Combat sports cadence (2026-05 content window)",
            }
        ],
    }
    (root / "content/pro_audio/monthly_pro_audio_packs.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def test_next_patch_version() -> None:
    assert next_patch_version("1.3.19") == "1.3.20"


def test_resolve_release_version_defaults_to_next_patch(tmp_path: Path) -> None:
    _write_minimal_repo(tmp_path)

    assert resolve_release_version(tmp_path) == "1.2.4"


def test_resolve_release_version_rejects_platform_mismatch(tmp_path: Path) -> None:
    _write_minimal_repo(tmp_path, android_version="1.2.3", ios_version="1.2.4")

    with pytest.raises(MonthlyReleaseError, match="version mismatch"):
        resolve_release_version(tmp_path)


def test_resolve_release_version_rejects_non_incrementing_override(tmp_path: Path) -> None:
    _write_minimal_repo(tmp_path)

    with pytest.raises(MonthlyReleaseError, match="must be greater"):
        resolve_release_version(tmp_path, requested_version="1.2.3")


def test_render_release_notes_are_customer_facing_without_placeholders() -> None:
    pack = {
        "id": "2026-05_combat_sports_cadence",
        "releaseMonth": "2026-05",
        "theme": "Combat sports cadence (2026-05 content window)",
    }

    versioned = render_versioned_release_notes("1.3.20", pack)
    store = render_store_release_notes(pack)

    assert "TODO" not in versioned
    assert "TODO" not in store
    assert "Monthly Pro audio release for May 2026" in versioned
    assert "New voice callouts" in store
    assert "Pro Sound Arsenal" in store


def test_write_release_notes_updates_store_and_versioned_files(tmp_path: Path) -> None:
    _write_minimal_repo(tmp_path)

    payload = write_release_notes(tmp_path, "1.2.4", json_out=tmp_path / "evidence.json")

    assert payload["version"] == "1.2.4"
    assert payload["android_version_code"] == 123
    assert (tmp_path / "release-notes/1.2.4.md").is_file()
    assert (tmp_path / "native-android/fastlane/metadata/android/en-US/changelogs/123.txt").is_file()
    assert (tmp_path / "native-ios/fastlane/metadata/en-US/release_notes.txt").is_file()
    assert "TODO" not in (tmp_path / "release-notes/1.2.4.md").read_text(encoding="utf-8")
    assert (tmp_path / "evidence.json").is_file()
