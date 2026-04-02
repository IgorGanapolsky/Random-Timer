#!/usr/bin/env python3
"""Check store listing parity between iOS App Store and Google Play Store.

Ensures both platforms have consistent metadata, screenshot counts,
and marketing creative quality. Runs in CI to prevent listing drift.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

IOS_META = "native-ios/fastlane/metadata/en-US"
IOS_SCREENSHOTS = "native-ios/fastlane/screenshots/en-US"
ANDROID_META = "native-android/fastlane/metadata/android/en-US"
ANDROID_SCREENSHOTS = f"{ANDROID_META}/images/phoneScreenshots"

MIN_PHONE_SCREENSHOTS = 3
MIN_SCREENSHOT_SIZE_KB = 100  # Marketing overlays should be >100KB


def check_metadata_files(root: Path) -> list[str]:
    """Verify required metadata files exist on both platforms."""
    errors: list[str] = []

    ios_required = {
        "name.txt": "App name",
        "subtitle.txt": "Subtitle",
        "description.txt": "Description",
        "keywords.txt": "Keywords",
        "release_notes.txt": "Release notes",
    }
    android_required = {
        "title.txt": "App name",
        "short_description.txt": "Short description",
        "full_description.txt": "Full description",
    }

    for fname, label in ios_required.items():
        path = root / IOS_META / fname
        if not path.exists():
            errors.append(f"iOS missing {label}: {fname}")
        elif path.stat().st_size < 5:
            errors.append(f"iOS {label} is empty: {fname}")

    for fname, label in android_required.items():
        path = root / ANDROID_META / fname
        if not path.exists():
            errors.append(f"Android missing {label}: {fname}")
        elif path.stat().st_size < 5:
            errors.append(f"Android {label} is empty: {fname}")

    return errors


def check_description_parity(root: Path) -> list[str]:
    """Check that descriptions share key selling points."""
    errors: list[str] = []

    ios_desc = (root / IOS_META / "description.txt").read_text(errors="ignore") if (root / IOS_META / "description.txt").exists() else ""
    android_desc = (root / ANDROID_META / "full_description.txt").read_text(errors="ignore") if (root / ANDROID_META / "full_description.txt").exists() else ""

    if not ios_desc or not android_desc:
        return errors  # Missing file errors caught elsewhere

    # Key phrases that should appear in both
    key_phrases = ["random", "timer", "drill", "reaction"]
    for phrase in key_phrases:
        ios_has = phrase.lower() in ios_desc.lower()
        android_has = phrase.lower() in android_desc.lower()
        if ios_has and not android_has:
            errors.append(f"Android description missing key phrase '{phrase}' (present in iOS)")

    return errors


def check_screenshot_counts(root: Path) -> list[str]:
    """Verify minimum screenshot counts on both platforms."""
    errors: list[str] = []

    ios_dir = root / IOS_SCREENSHOTS
    android_dir = root / ANDROID_SCREENSHOTS

    ios_pngs = sorted(ios_dir.glob("*.png")) if ios_dir.exists() else []
    android_pngs = sorted(android_dir.glob("*.png")) if android_dir.exists() else []

    # Filter out subdirectory content — only count root-level PNGs
    ios_phone = [p for p in ios_pngs if not p.name.startswith("_") and "ipad" not in p.name.lower()]
    android_phone = android_pngs

    if len(ios_phone) < MIN_PHONE_SCREENSHOTS:
        errors.append(f"iOS has only {len(ios_phone)} phone screenshots (minimum: {MIN_PHONE_SCREENSHOTS})")
    if len(android_phone) < MIN_PHONE_SCREENSHOTS:
        errors.append(f"Android has only {len(android_phone)} phone screenshots (minimum: {MIN_PHONE_SCREENSHOTS})")

    # Parity check
    diff = abs(len(ios_phone) - len(android_phone))
    if diff > 2:
        errors.append(
            f"Screenshot count imbalance: iOS={len(ios_phone)}, Android={len(android_phone)} "
            f"(diff={diff}, max allowed=2)"
        )

    return errors


def check_screenshot_quality(root: Path) -> list[str]:
    """Check that screenshots have marketing overlays (file size heuristic)."""
    errors: list[str] = []

    for platform, screenshot_dir in [("iOS", IOS_SCREENSHOTS), ("Android", ANDROID_SCREENSHOTS)]:
        sdir = root / screenshot_dir
        if not sdir.exists():
            continue

        pngs = sorted(sdir.glob("*.png"))
        for png in pngs:
            if png.name.startswith("_"):
                continue
            size_kb = png.stat().st_size / 1024
            if size_kb < MIN_SCREENSHOT_SIZE_KB:
                errors.append(
                    f"{platform} screenshot '{png.name}' is only {size_kb:.0f}KB "
                    f"(minimum {MIN_SCREENSHOT_SIZE_KB}KB — likely missing marketing overlay)"
                )

    return errors


def check_screenshot_dimensions(root: Path) -> list[str]:
    """Check screenshot dimensions meet store requirements."""
    errors: list[str] = []

    try:
        from PIL import Image
    except ImportError:
        # Pillow not available — skip dimension checks
        return errors

    # Valid iPhone dimensions (width x height)
    valid_iphone = {
        (1290, 2796),  # iPhone 6.7" (15 Pro Max)
        (1320, 2868),  # iPhone 6.9" (16 Pro Max)
        (1284, 2778),  # iPhone 6.5" (14 Plus)
        (1242, 2688),  # iPhone 6.5" (11 Pro Max)
    }
    # Valid Android phone dimensions (common)
    valid_android_widths = range(1080, 1440 + 1)

    ios_dir = root / IOS_SCREENSHOTS
    if ios_dir.exists():
        for png in sorted(ios_dir.glob("*.png")):
            if png.name.startswith("_") or "ipad" in png.name.lower():
                continue
            img = Image.open(png)
            w, h = img.size
            if (w, h) not in valid_iphone and (h, w) not in valid_iphone:
                errors.append(f"iOS '{png.name}' has non-standard dimensions {w}x{h}")

    android_dir = root / ANDROID_SCREENSHOTS
    if android_dir.exists():
        for png in sorted(android_dir.glob("*.png")):
            if png.name.startswith("_"):
                continue
            img = Image.open(png)
            w, h = img.size
            if w < 320 or h < 320:
                errors.append(f"Android '{png.name}' is too small: {w}x{h}")
            if h <= w:
                errors.append(f"Android '{png.name}' appears landscape ({w}x{h}) — phone screenshots should be portrait")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check store listing parity between iOS and Android")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    args = parser.parse_args()

    root = Path(args.repo_root)
    all_errors: list[str] = []
    all_warnings: list[str] = []

    print("=" * 60)
    print("  STORE LISTING PARITY CHECK")
    print("=" * 60)

    # Metadata
    meta_errors = check_metadata_files(root)
    all_errors.extend(meta_errors)

    # Description parity
    desc_warnings = check_description_parity(root)
    all_warnings.extend(desc_warnings)

    # Screenshot counts
    count_errors = check_screenshot_counts(root)
    all_errors.extend(count_errors)

    # Screenshot quality
    quality_errors = check_screenshot_quality(root)
    all_errors.extend(quality_errors)

    # Screenshot dimensions
    dim_errors = check_screenshot_dimensions(root)
    all_errors.extend(dim_errors)

    # Report
    for w in all_warnings:
        print(f"  ⚠️  {w}")
    for e in all_errors:
        print(f"  ❌ {e}")

    if not all_errors and not all_warnings:
        print("  ✅ All parity checks passed")

    print("=" * 60)
    print(f"  Errors: {len(all_errors)} | Warnings: {len(all_warnings)}")
    print("=" * 60)

    if all_errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
