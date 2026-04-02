#!/usr/bin/env python3
"""Validate iOS App Store screenshot and metadata assets.

Checks dimensions, file presence, report consistency, and metadata text lengths.
Run before any metadata sync to catch issues early.

Usage:
    python scripts/refresh_ios_screenshot_creatives.py
"""

from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

SCREENSHOT_SPECS: dict[str, set[tuple[int, int]]] = {
    "1_setup.png": {(1290, 2796), (1320, 2868)},
    "2_active.png": {(1290, 2796), (1320, 2868)},
    "3_alarm.png": {(1290, 2796), (1320, 2868)},
    "4_running.png": {(1290, 2796), (1320, 2868)},
    "5_ipad_setup.png": {(2048, 2732), (2064, 2752)},
    "6_ipad_running.png": {(2048, 2732), (2064, 2752)},
    "7_ipad_stopped.png": {(2048, 2732), (2064, 2752)},
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
    expected_names = set(SCREENSHOT_SPECS)
    digests: dict[str, list[str]] = {}

    for name, allowed_sizes in SCREENSHOT_SPECS.items():
        path = screenshots_dir / name
        if not path.is_file():
            errors.append(f"missing screenshot: {name}")
            continue
        img = Image.open(path)
        if img.size not in allowed_sizes:
            expected = " or ".join(f"{w}x{h}" for (w, h) in sorted(allowed_sizes))
            errors.append(f"{name}: {img.size[0]}x{img.size[1]}, expected {expected}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digests.setdefault(digest, []).append(name)

    legacy_paywall = screenshots_dir / "3_pro.png"
    if legacy_paywall.exists():
        errors.append("disallowed storefront screenshot present: 3_pro.png")

    actual_pngs = {path.name for path in screenshots_dir.glob("*.png")}
    unexpected_pngs = sorted(actual_pngs - expected_names)
    if unexpected_pngs:
        errors.append(f"unexpected iOS screenshot files: {', '.join(unexpected_pngs)}")

    duplicate_groups = [sorted(names) for names in digests.values() if len(names) > 1]
    for group in duplicate_groups:
        errors.append(f"duplicate screenshot bytes: {', '.join(group)}")

    report_path = screenshots_dir / "report.json"
    if not report_path.is_file():
        errors.append("missing screenshot report: report.json")
    else:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid screenshot report JSON: {exc}")
        else:
            written = {Path(path).name for path in report.get("written_files", [])}
            if written != expected_names:
                errors.append(
                    "report.json written_files does not match expected storefront set: "
                    f"{sorted(written)}"
                )
            sources = set((report.get("source_files") or {}).keys())
            if sources and sources != expected_names:
                errors.append(
                    "report.json source_files does not match expected storefront set: "
                    f"{sorted(sources)}"
                )

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
