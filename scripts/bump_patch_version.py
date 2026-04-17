#!/usr/bin/env python3
"""
Bump the patch version component across both Android (build.gradle.kts) and
iOS (project.pbxproj) source files, bump Android ``versionCode`` by one for the
next Play upload, then write the Android changelog for that new code (so the
previous release's changelog file is never overwritten).

Example: 1.3.19 → 1.3.20

Usage
-----
    python scripts/bump_patch_version.py [--dry-run] [--changelog-message "..."]

The script exits non-zero if versions are out of sync between platforms so the
pipeline can catch accidental drift early.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]

ANDROID_GRADLE = REPO_ROOT / "native-android" / "app" / "build.gradle.kts"
IOS_PBXPROJ = REPO_ROOT / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"
ANDROID_CHANGELOG_DIR = (
    REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "changelogs"
)
IOS_RELEASE_NOTES = (
    REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "release_notes.txt"
)

# ---------------------------------------------------------------------------
# Version parsing
# ---------------------------------------------------------------------------


def _parse_semver(version_str: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version_str.strip())
    if not m:
        raise ValueError(f"Not a semver string: {version_str!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump_patch(major: int, minor: int, patch: int) -> tuple[int, int, int]:
    return major, minor, patch + 1


def _semver_str(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


# ---------------------------------------------------------------------------
# Android helpers
# ---------------------------------------------------------------------------


def read_android_version(gradle_text: str) -> str:
    """Return the versionName string from build.gradle.kts content."""
    for line in gradle_text.splitlines():
        if "versionName" in line and "=" in line:
            rhs = line.split("=", 1)[1]
            candidate = rhs.strip().strip('"')
            if re.fullmatch(r"\d+\.\d+\.\d+", candidate):
                return candidate
    raise ValueError("Could not parse versionName from build.gradle.kts")


def read_android_version_code(gradle_text: str) -> int:
    """Return the concrete fallback versionCode from build.gradle.kts content."""
    for line in gradle_text.splitlines():
        if "versionCode" not in line or "=" not in line:
            continue
        rhs = line.split("=", 1)[1].split("//", 1)[0].strip()
        if "?:" in rhs:
            rhs = rhs.rsplit("?:", 1)[1].strip()
        if rhs.isdigit():
            return int(rhs)
    raise ValueError("Could not parse versionCode from build.gradle.kts")


def write_android_version(gradle_text: str, new_version: str) -> str:
    """Return gradle_text with versionName updated to new_version."""
    pattern = re.compile(r'(versionName\s*=\s*")\d+\.\d+\.\d+(")')
    replacement = rf'\g<1>{new_version}\g<2>'
    new_text, n = pattern.subn(replacement, gradle_text)
    if n == 0:
        raise ValueError("Could not update versionName in build.gradle.kts")
    return new_text


def write_android_version_code(gradle_text: str, new_code: int) -> str:
    """Return gradle_text with defaultConfig versionCode literal updated to new_code.

    Supports ``versionCode = ciVersionCode ?: N`` and plain ``versionCode = N``.
    """
    pattern = re.compile(r"(versionCode\s*=\s*(?:[^\n]*?\?:\s*)?)(\d+)")
    new_text, n = pattern.subn(rf"\g<1>{new_code}", gradle_text, count=1)
    if n != 1:
        raise ValueError("Could not update versionCode in build.gradle.kts (expected exactly one match)")
    return new_text


# ---------------------------------------------------------------------------
# iOS helpers
# ---------------------------------------------------------------------------


def read_ios_version(pbxproj_text: str) -> str:
    """Return the MARKETING_VERSION string from project.pbxproj content."""
    for line in pbxproj_text.splitlines():
        if "MARKETING_VERSION" in line and "=" in line:
            rhs = line.split("=", 1)[1]
            candidate = rhs.strip().rstrip(";").strip()
            if re.fullmatch(r"\d+\.\d+\.\d+", candidate):
                return candidate
    raise ValueError("Could not parse MARKETING_VERSION from project.pbxproj")


def write_ios_version(pbxproj_text: str, new_version: str) -> str:
    """Return pbxproj_text with all MARKETING_VERSION entries updated."""
    pattern = re.compile(r"(MARKETING_VERSION\s*=\s*)\d+\.\d+\.\d+(;)")
    replacement = rf"\g<1>{new_version}\g<2>"
    new_text, n = pattern.subn(replacement, pbxproj_text)
    if n == 0:
        raise ValueError("Could not update MARKETING_VERSION in project.pbxproj")
    print(f"  Updated {n} MARKETING_VERSION occurrence(s) in project.pbxproj")
    return new_text


# ---------------------------------------------------------------------------
# Changelog helpers
# ---------------------------------------------------------------------------


def _build_changelog_message(base_message: str | None) -> str:
    if base_message:
        return base_message
    month_year = datetime.now(tz=timezone.utc).strftime("%B %Y")
    return f"Monthly Pro content update — {month_year}"


def update_android_changelog(version_code: int, message: str, dry_run: bool) -> Path:
    """Write a new Android changelog file for the given versionCode."""
    ANDROID_CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)
    dest = ANDROID_CHANGELOG_DIR / f"{version_code}.txt"
    if dry_run:
        print(f"  [dry-run] Would write Android changelog: {dest.relative_to(REPO_ROOT)}")
    else:
        dest.write_text(message + "\n", encoding="utf-8")
        print(f"  ✅ Wrote Android changelog: {dest.relative_to(REPO_ROOT)}")
    return dest


def update_ios_release_notes(message: str, dry_run: bool) -> Path:
    """Overwrite the iOS release_notes.txt with the changelog message."""
    IOS_RELEASE_NOTES.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"  [dry-run] Would write iOS release notes: {IOS_RELEASE_NOTES.relative_to(REPO_ROOT)}")
    else:
        IOS_RELEASE_NOTES.write_text(message + "\n", encoding="utf-8")
        print(f"  ✅ Wrote iOS release notes: {IOS_RELEASE_NOTES.relative_to(REPO_ROOT)}")
    return IOS_RELEASE_NOTES


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def bump(
    dry_run: bool = False,
    changelog_message: str | None = None,
    skip_changelog: bool = False,
) -> str:
    """Perform the version bump. Returns the new version string."""

    # Read current versions
    gradle_text = ANDROID_GRADLE.read_text(encoding="utf-8")
    pbxproj_text = IOS_PBXPROJ.read_text(encoding="utf-8")

    android_ver = read_android_version(gradle_text)
    android_version_code = read_android_version_code(gradle_text)
    ios_ver = read_ios_version(pbxproj_text)

    print(f"Current Android version : {android_ver}")
    print(f"Current iOS version     : {ios_ver}")

    if android_ver != ios_ver:
        print(
            f"❌ Version mismatch: Android={android_ver}, iOS={ios_ver}. "
            "Resolve drift before bumping.",
            file=sys.stderr,
        )
        sys.exit(1)

    major, minor, patch = _parse_semver(android_ver)
    new_major, new_minor, new_patch = _bump_patch(major, minor, patch)
    new_version = _semver_str(new_major, new_minor, new_patch)
    next_version_code = android_version_code + 1
    print(f"Bumping {android_ver} → {new_version}")
    print(f"Android versionCode {android_version_code} → {next_version_code} (Play changelog filename)")

    if dry_run:
        print("[dry-run] No files written.")
    else:
        # Write Android (semver + monotonic versionCode for the new upload)
        new_gradle = write_android_version(gradle_text, new_version)
        new_gradle = write_android_version_code(new_gradle, next_version_code)
        ANDROID_GRADLE.write_text(new_gradle, encoding="utf-8")
        print(f"  ✅ Updated {ANDROID_GRADLE.relative_to(REPO_ROOT)}")

        # Write iOS
        new_pbxproj = write_ios_version(pbxproj_text, new_version)
        IOS_PBXPROJ.write_text(new_pbxproj, encoding="utf-8")

    if skip_changelog:
        print("  Skipped store changelog updates.")
    else:
        message = _build_changelog_message(changelog_message)
        update_android_changelog(next_version_code, message, dry_run)
        update_ios_release_notes(message, dry_run)

    return new_version


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bump patch version in Android + iOS source and update changelogs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing any files.",
    )
    parser.add_argument(
        "--changelog-message",
        default=None,
        help='Override the default "Monthly Pro content update — Month YYYY" message.',
    )
    parser.add_argument(
        "--skip-changelog",
        action="store_true",
        help="Only bump source versions; do not modify store release notes.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    new_version = bump(
        dry_run=args.dry_run,
        changelog_message=args.changelog_message,
        skip_changelog=args.skip_changelog,
    )
    print(f"\nNew version: {new_version}")
    if not args.dry_run:
        # Write the new version to stdout in a format the shell can capture
        print(f"::set-output name=new_version::{new_version}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
