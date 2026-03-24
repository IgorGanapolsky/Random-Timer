from pathlib import Path

from PIL import Image

from scripts import refresh_ios_screenshot_creatives as refresh


def _write_png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=(20, 20, 30))
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
    for filename in ("1_setup.png", "2_active.png", "3_alarm.png", "4_running.png"):
        _write_png(screenshots_dir / filename, (1290, 2796))
    for filename in ("5_ipad_setup.png", "6_ipad_running.png", "7_ipad_stopped.png"):
        _write_png(screenshots_dir / filename, ipad_size)
    (root / "PRIVACY_POLICY.md").write_text("Privacy policy", encoding="utf-8")
    _write_metadata(root)


def test_accepts_current_13_inch_ipad_size(tmp_path: Path) -> None:
    _write_required_assets(tmp_path, (2064, 2752))

    assert refresh.validate(tmp_path) == []


def test_accepts_legacy_13_inch_ipad_size(tmp_path: Path) -> None:
    _write_required_assets(tmp_path, (2048, 2732))

    assert refresh.validate(tmp_path) == []
