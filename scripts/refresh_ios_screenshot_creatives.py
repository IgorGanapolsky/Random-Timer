#!/usr/bin/env python3
"""Validate iOS App Store screenshot and metadata assets.

Checks dimensions, file presence, metadata text lengths, and keyword limits.
Run before any metadata sync to catch issues early.

Usage:
    python scripts/refresh_ios_screenshot_creatives.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

SCREENSHOT_SPECS: dict[str, tuple[int, int]] = {
    "1_setup.png": (1290, 2796),
    "2_active.png": (1290, 2796),
    "3_alarm.png": (1290, 2796),
    "4_running.png": (1290, 2796),
    "5_ipad_setup.png": (2048, 2732),
    "6_ipad_running.png": (2048, 2732),
    "7_ipad_stopped.png": (2048, 2732),
}

METADATA_LIMITS: dict[str, tuple[int, int]] = {
    "name.txt": (1, 30),
    "subtitle.txt": (1, 30),
    "description.txt": (10, 4000),
    "keywords.txt": (1, 100),
    "promotional_text.txt": (1, 170),
    "release_notes.txt": (1, 4000),
    "privacy_url.txt": (1, 500),
    "support_url.txt": (1, 500),
    "marketing_url.txt": (1, 500),
}


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    screenshots_dir = root / "native-ios" / "fastlane" / "screenshots" / "en-US"
    metadata_dir = root / "native-ios" / "fastlane" / "metadata" / "en-US"

    for name, (exp_w, exp_h) in SCREENSHOT_SPECS.items():
        path = screenshots_dir / name
        if not path.is_file():
            errors.append(f"missing screenshot: {name}")
            continue
        img = Image.open(path)
        if img.size != (exp_w, exp_h):
            errors.append(f"{name}: {img.size[0]}x{img.size[1]}, expected {exp_w}x{exp_h}")

    for name, (min_len, max_len) in METADATA_LIMITS.items():
        path = metadata_dir / name
        if not path.is_file():
            errors.append(f"missing metadata: {name}")
            continue
        content = path.read_text().strip()
        if len(content) < min_len:
            errors.append(f"{name}: empty or too short")
        if len(content) > max_len:
            errors.append(f"{name}: {len(content)} chars exceeds {max_len} limit")

    privacy = root / "PRIVACY_POLICY.md"
    if not privacy.is_file():
        errors.append("missing PRIVACY_POLICY.md")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
