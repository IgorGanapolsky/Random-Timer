#!/usr/bin/env python3
"""Bump iOS + Android versions in a consistent, SemVer-driven way.

Intended usage:
  - Run on `develop` before opening the `develop -> main` release PR.
  - Ensures Android/iOS SemVer match, and increments build numbers.
  - Writes Play Console release notes file for the new versionCode.
  - Updates iOS fastlane release_notes.txt.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from scripts.versioning import (
    SEMVER_RE,
    bump_semver,
    read_repo_versions,
    update_android_build_gradle_kts,
    update_ios_pbxproj,
)


def _write_if_exists(path: Path, content: str) -> None:
    if path.exists():
        path.write_text(content, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--bump", choices=["major", "minor", "patch"])
    g.add_argument("--version", help="Set explicit SemVer (e.g., 1.2.3)")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument("--no-notes", action="store_true", help="Do not write release notes files")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    cur = read_repo_versions(repo_root)

    if args.version:
        new_version = args.version.strip()
        if not SEMVER_RE.match(new_version):
            raise SystemExit(f"Invalid SemVer: {new_version}")
    else:
        new_version = bump_semver(cur.version, args.bump)

    if new_version == cur.version:
        raise SystemExit("New version is the same as current version")

    new_android_code = cur.android_version_code + 1
    new_ios_build = cur.ios_build_number + 1

    update_android_build_gradle_kts(
        repo_root / "native-android/app/build.gradle.kts",
        version=new_version,
        version_code=new_android_code,
    )
    update_ios_pbxproj(
        repo_root / "native-ios/RandomTimer.xcodeproj/project.pbxproj",
        version=new_version,
        build_number=new_ios_build,
    )

    if not args.no_notes:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        notes = f"Release {new_version} ({now})\n"

        play_notes = (
            repo_root
            / "native-android/fastlane/metadata/android/en-US/changelogs"
            / f"{new_android_code}.txt"
        )
        play_notes.parent.mkdir(parents=True, exist_ok=True)
        play_notes.write_text(notes, encoding="utf-8")

        ios_notes = repo_root / "native-ios/fastlane/metadata/en-US/release_notes.txt"
        _write_if_exists(ios_notes, notes)

    print(
        f"Updated to version={new_version} "
        f"(android versionCode={new_android_code}, iOS build={new_ios_build})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
