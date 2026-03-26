import json
from pathlib import Path

from PIL import Image

from scripts import generate_android_store_creatives as creatives


def _write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=color).save(path, format="PNG")


def test_generate_android_store_creatives_writes_expected_outputs(tmp_path: Path) -> None:
    _write_png(tmp_path / "branding" / "app-icon-source.png", (1024, 1024), (20, 30, 40))

    raw_colors = {
        "android-setup.png": (10, 40, 70),
        "android-active.png": (40, 70, 100),
        "android-settings.png": (70, 100, 130),
        "android-loop.png": (100, 130, 160),
    }
    for name, color in raw_colors.items():
        _write_png(tmp_path / "screenshots" / name, (1080, 2340), color)

    report = creatives.generate(tmp_path)

    assert report["status"] == "success"
    report_path = Path(report["report_path"])
    assert report_path.is_file()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["source_icon"].endswith("branding/app-icon-source.png")

    play_icon = tmp_path / "native-android/fastlane/metadata/android/en-US/images/icon.png"
    assert Image.open(play_icon).size == (1024, 1024)

    screenshots_dir = tmp_path / "native-android/fastlane/metadata/android/en-US/images/phoneScreenshots"
    for filename in creatives.SCREENSHOT_MAP:
        assert Image.open(screenshots_dir / filename).size == creatives.PLAY_SCREENSHOT_SIZE

    feature_graphic = (
        tmp_path / "native-android/fastlane/metadata/android/en-US/images/featureGraphic/feature-graphic.png"
    )
    assert Image.open(feature_graphic).size == creatives.FEATURE_GRAPHIC_SIZE


def test_generate_android_store_creatives_fails_without_canonical_icon(tmp_path: Path) -> None:
    for name in creatives.SCREENSHOT_MAP.values():
        _write_png(tmp_path / "screenshots" / name, (1080, 2340), (12, 34, 56))

    try:
        creatives.generate(tmp_path)
    except FileNotFoundError as exc:
        assert "Canonical icon source missing" in str(exc)
    else:
        raise AssertionError("Expected generate() to fail without canonical icon source")
