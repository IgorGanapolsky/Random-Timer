from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def test_ios_appiconset_has_no_extra_or_missing_pngs() -> None:
    appiconset = Path("native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset")
    contents = json.loads((appiconset / "Contents.json").read_text(encoding="utf-8"))
    referenced = {img["filename"] for img in contents.get("images", []) if img.get("filename")}
    existing = {path.name for path in appiconset.glob("*.png")}

    missing = sorted(referenced - existing)
    extras = sorted(existing - referenced)

    assert not missing, f"Missing icon files referenced by Contents.json: {missing}"
    assert not extras, f"Unassigned icon files should be removed: {extras}"


def test_ios_marketing_icon_matches_android_source_artwork() -> None:
    android_icon = Image.open(
        "native-android/fastlane/metadata/android/en-US/images/icon.png"
    ).convert("RGB")
    ios_marketing = Image.open(
        "native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png"
    ).convert("RGB")
    ios_resized = ios_marketing.resize(android_icon.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(android_icon, ios_resized)
    mean_diff = sum(ImageStat.Stat(diff).mean) / 3.0

    assert mean_diff <= 0.5, (
        "iOS marketing icon artwork diverged from Android source icon "
        f"(mean RGB diff={mean_diff:.3f})"
    )
