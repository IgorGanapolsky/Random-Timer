#!/usr/bin/env python3
"""Validate release/hotfix branch naming and platform version alignment.

Rules:
1. Branch must be named `release/vX.Y.Z` or `hotfix/vX.Y.Z`.
2. Android `versionName` must equal iOS `MARKETING_VERSION`.
3. Both platform versions must match X.Y.Z from the branch name.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from scripts.source_versions import (
        VersionParseError,
        extract_android_version_name,
        extract_ios_version_name,
    )
except ModuleNotFoundError:
    from source_versions import VersionParseError, extract_android_version_name, extract_ios_version_name


class ValidationError(RuntimeError):
    """Raised when release branch validation fails."""


RELEASE_BRANCH_RE = re.compile(r"^(?:release|hotfix)/v(?P<version>\d+\.\d+\.\d+)$")
def validate_release_branch(repo_root: Path, head_ref: str) -> dict:
    branch_match = RELEASE_BRANCH_RE.match(head_ref.strip())
    if not branch_match:
        raise ValidationError(
            f"Only release/vX.Y.Z or hotfix/vX.Y.Z branches are allowed for main promotion. Received: '{head_ref}'"
        )

    expected_version = branch_match.group("version")
    try:
        android_text = (repo_root / "native-android" / "app" / "build.gradle.kts").read_text(
            encoding="utf-8",
            errors="replace",
        )
        ios_text = (repo_root / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj").read_text(
            encoding="utf-8",
            errors="replace",
        )
        android_version = extract_android_version_name(android_text)
        ios_version = extract_ios_version_name(ios_text)
    except (OSError, VersionParseError) as exc:
        raise ValidationError(str(exc)) from exc

    if android_version != ios_version:
        raise ValidationError(
            f"Version mismatch: Android versionName={android_version}, iOS MARKETING_VERSION={ios_version}"
        )

    if android_version != expected_version:
        raise ValidationError(
            f"Release branch mismatch: branch expects {expected_version}, app versions are {android_version}"
        )

    return {
        "head_ref": head_ref,
        "expected_version": expected_version,
        "android_version": android_version,
        "ios_version": ios_version,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate release branch vs app versions.")
    parser.add_argument("--head-ref", required=True, help="Branch name, e.g. release/v1.2.0 or hotfix/v1.2.1")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    try:
        result = validate_release_branch(repo_root=repo_root, head_ref=args.head_ref)
    except ValidationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print("[OK] Release branch validation passed")
    print(f"  branch:   {result['head_ref']}")
    print(f"  version:  {result['expected_version']}")
    print(f"  android:  {result['android_version']}")
    print(f"  ios:      {result['ios_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
