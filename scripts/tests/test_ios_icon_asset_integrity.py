from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageStat

from scripts import sync_ios_icon_from_source as syncer


def test_ios_appiconset_has_no_extra_or_missing_pngs() -> None:
    appiconset = Path("native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset")
    contents = json.loads((appiconset / "Contents.json").read_text(encoding="utf-8"))
    referenced = {img["filename"] for img in contents.get("images", []) if img.get("filename")}
    existing = {path.name for path in appiconset.glob("*.png")}

    missing = sorted(referenced - existing)
    extras = sorted(existing - referenced)

    assert not missing, f"Missing icon files referenced by Contents.json: {missing}"
    assert not extras, f"Unassigned icon files should be removed: {extras}"


def test_ios_appiconset_pngs_are_fully_opaque() -> None:
    appiconset = Path("native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset")
    for path in sorted(appiconset.glob("*.png")):
        image = Image.open(path)
        assert image.mode == "RGB", f"{path.name} should be flattened to RGB for App Store upload"
        assert "A" not in image.getbands(), f"{path.name} still contains an alpha channel"


def test_ios_marketing_icon_matches_android_source_artwork() -> None:
    if not Path("branding/app-icon-source.png").exists():
        pytest.skip("branding/app-icon-source.png not in checkout (untracked asset)")
    canonical_icon = syncer._flatten_to_opaque_rgb(Image.open("branding/app-icon-source.png"))
    android_icon = syncer._flatten_to_opaque_rgb(
        Image.open("native-android/fastlane/metadata/android/en-US/images/icon.png")
    )
    ios_marketing = Image.open(
        "native-ios/RandomTimer/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png"
    ).convert("RGB")
    ios_resized = ios_marketing.resize(canonical_icon.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(canonical_icon, ios_resized)
    mean_diff = sum(ImageStat.Stat(diff).mean) / 3.0

    assert mean_diff <= 1.0, (
        "iOS marketing icon artwork diverged from canonical source icon "
        f"(mean RGB diff={mean_diff:.3f})"
    )
    canonical_at_play_size = canonical_icon.resize(
        android_icon.size, Image.Resampling.LANCZOS
    )
    play_diff = ImageChops.difference(canonical_at_play_size, android_icon)
    play_mean = sum(ImageStat.Stat(play_diff).mean) / 3.0
    assert play_mean <= 1.0, (
        "Android Play icon artwork diverged from canonical source icon "
        f"(mean RGB diff={play_mean:.3f})"
    )
