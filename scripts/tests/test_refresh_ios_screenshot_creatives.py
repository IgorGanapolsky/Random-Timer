from pathlib import Path

from PIL import Image

from scripts import refresh_ios_screenshot_creatives as refresh


def _write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int] = (20, 20, 30)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=color)
    image.save(path)


def _write_metadata(root: Path) -> None:
    metadata_dir = root / "native-ios" / "fastlane" / "metadata" / "en-US"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    values = {
        "name.txt": "Random Tactical Timer",
        "subtitle.txt": "Reaction Training",
        "description.txt": "A tactical reaction timer for pressure drills and interval focus.",
        "keywords.txt": "dry fire,boxing,mma,bjj,hiit,sparring,shooting,agility,drills,range,interval,beep",
        "promotional_text.txt": "Build speed and discipline with randomized drills.",
        "release_notes.txt": "App Store creative overhaul.",
        "privacy_url.txt": "https://igorganapolsky.com/privacy",
        "support_url.txt": "https://igorganapolsky.com/support",
        "marketing_url.txt": "https://igorganapolsky.com/random-tactical-timer",
    }
    for name, content in values.items():
        (metadata_dir / name).write_text(content, encoding="utf-8")


def _write_required_assets(root: Path, ipad_size: tuple[int, int]) -> None:
    screenshots_dir = root / "native-ios" / "fastlane" / "screenshots" / "en-US"
    iphone_sizes = {
        "1_setup.png": ((1320, 2868), (20, 20, 30)),
        "2_active.png": ((1320, 2868), (30, 20, 40)),
        "3_alarm.png": ((1320, 2868), (40, 20, 50)),
        "4_running.png": ((1320, 2868), (50, 20, 60)),
    }
    for filename, (size, color) in iphone_sizes.items():
        _write_png(screenshots_dir / filename, size, color)

    ipad_colors = {
        "5_ipad_setup.png": (60, 20, 70),
        "6_ipad_running.png": (70, 20, 80),
        "7_ipad_stopped.png": (80, 20, 90),
    }
    for filename, color in ipad_colors.items():
        _write_png(screenshots_dir / filename, ipad_size, color)
    (screenshots_dir / "report.json").write_text(
        """{
  "written_files": [
    "native-ios/fastlane/screenshots/en-US/1_setup.png",
    "native-ios/fastlane/screenshots/en-US/2_active.png",
    "native-ios/fastlane/screenshots/en-US/3_alarm.png",
    "native-ios/fastlane/screenshots/en-US/4_running.png",
    "native-ios/fastlane/screenshots/en-US/5_ipad_setup.png",
    "native-ios/fastlane/screenshots/en-US/6_ipad_running.png",
    "native-ios/fastlane/screenshots/en-US/7_ipad_stopped.png"
  ],
  "source_files": {
    "1_setup.png": "src/1_setup.png",
    "2_active.png": "src/2_active.png",
    "3_alarm.png": "src/3_alarm.png",
    "4_running.png": "src/4_running.png",
    "5_ipad_setup.png": "src/5_ipad_setup.png",
    "6_ipad_running.png": "src/6_ipad_running.png",
    "7_ipad_stopped.png": "src/7_ipad_stopped.png"
  }
}""",
        encoding="utf-8",
    )
    (root / "PRIVACY_POLICY.md").write_text("Privacy policy", encoding="utf-8")
    _write_metadata(root)


def test_accepts_current_13_inch_ipad_size(tmp_path: Path) -> None:
    _write_required_assets(tmp_path, (2064, 2752))

    assert refresh.validate(tmp_path) == []


def test_accepts_legacy_13_inch_ipad_size(tmp_path: Path) -> None:
    _write_required_assets(tmp_path, (2048, 2732))

    assert refresh.validate(tmp_path) == []


def test_rejects_paywall_screenshot_and_unexpected_png(tmp_path: Path) -> None:
    _write_required_assets(tmp_path, (2064, 2752))
    screenshots_dir = tmp_path / "native-ios" / "fastlane" / "screenshots" / "en-US"
    _write_png(screenshots_dir / "3_pro.png", (1290, 2796))

    errors = refresh.validate(tmp_path)

    assert any("3_pro.png" in err for err in errors)
    assert any("unexpected iOS screenshot files" in err for err in errors)
