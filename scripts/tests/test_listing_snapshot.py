import json
from pathlib import Path

from PIL import Image

from scripts import listing_snapshot


def _write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=color).save(path, format="PNG")


def _seed_versions(repo: Path) -> None:
    (repo / "native-android/app").mkdir(parents=True, exist_ok=True)
    (repo / "native-android/app/build.gradle.kts").write_text(
        'versionName = "1.3.14"\nversionCode = 1773900042\n',
        encoding="utf-8",
    )
    (repo / "native-ios/RandomTimer.xcodeproj").mkdir(parents=True, exist_ok=True)
    (repo / "native-ios/RandomTimer.xcodeproj/project.pbxproj").write_text(
        "MARKETING_VERSION = 1.3.14;\nCURRENT_PROJECT_VERSION = 42;\n",
        encoding="utf-8",
    )


def test_build_android_snapshot_includes_expected_inventory(tmp_path: Path) -> None:
    _seed_versions(tmp_path)
    (tmp_path / "native-android/fastlane/metadata/android/en-US").mkdir(parents=True, exist_ok=True)
    (tmp_path / "native-android/fastlane/metadata/android/en-US/title.txt").write_text(
        "Random Tactical Timer",
        encoding="utf-8",
    )
    _write_png(tmp_path / "native-android/fastlane/metadata/android/en-US/images/icon.png", (1024, 1024), (1, 2, 3))
    _write_png(
        tmp_path / "native-android/fastlane/metadata/android/en-US/images/featureGraphic/feature-graphic.png",
        (1024, 500),
        (4, 5, 6),
    )
    _write_png(
        tmp_path / "native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/1_setup.png",
        (1344, 2992),
        (7, 8, 9),
    )

    payload = listing_snapshot.build_android_snapshot(
        tmp_path,
        source_run_id="123",
        source_run_url="https://example.com/run/123",
        track="internal",
        version_code="1773900042",
    )

    assert payload["platform"] == "android"
    assert payload["track"] == "internal"
    assert payload["version_code"] == "1773900042"
    assert payload["screenshots"][0]["file"] == "1_setup.png"


def test_build_ios_snapshot_includes_expected_inventory(tmp_path: Path) -> None:
    _seed_versions(tmp_path)
    (tmp_path / "native-ios/fastlane/metadata/en-US").mkdir(parents=True, exist_ok=True)
    (tmp_path / "native-ios/fastlane/metadata/en-US/name.txt").write_text(
        "Random Tactical Timer",
        encoding="utf-8",
    )
    _write_png(
        tmp_path / "native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png",
        (1024, 1024),
        (12, 13, 14),
    )
    _write_png(tmp_path / "native-ios/fastlane/screenshots/en-US/1_setup.png", (1290, 2796), (15, 16, 17))

    payload = listing_snapshot.build_ios_snapshot(
        tmp_path,
        source_run_id="987",
        source_run_url="https://example.com/run/987",
        locale="en-US",
        app_store_version="1.3.14",
    )

    assert payload["platform"] == "ios"
    assert payload["app_store_version"] == "1.3.14"
    assert payload["screenshots"][0]["file"] == "1_setup.png"


def test_listing_snapshot_main_writes_json_output(tmp_path: Path, monkeypatch) -> None:
    _seed_versions(tmp_path)
    (tmp_path / "native-android/fastlane/metadata/android/en-US").mkdir(parents=True, exist_ok=True)
    (tmp_path / "native-android/fastlane/metadata/android/en-US/title.txt").write_text(
        "Random Tactical Timer",
        encoding="utf-8",
    )
    _write_png(tmp_path / "native-android/fastlane/metadata/android/en-US/images/icon.png", (1024, 1024), (1, 1, 1))
    _write_png(
        tmp_path / "native-android/fastlane/metadata/android/en-US/images/featureGraphic/feature-graphic.png",
        (1024, 500),
        (2, 2, 2),
    )
    _write_png(
        tmp_path / "native-android/fastlane/metadata/android/en-US/images/phoneScreenshots/1_setup.png",
        (1344, 2992),
        (3, 3, 3),
    )
    output = tmp_path / "snapshot.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "listing_snapshot.py",
            "--platform",
            "android",
            "--repo-root",
            str(tmp_path),
            "--output",
            str(output),
        ],
    )
    assert listing_snapshot.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["platform"] == "android"
