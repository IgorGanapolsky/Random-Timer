#!/usr/bin/env python3
"""Semver patch bump helper for monthly storefront releases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def bump_semver_patch(version: str) -> str:
    """Return X.Y.(Z+1) for valid X.Y.Z; all parts must be non-negative integers."""
    parts = version.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"expected X.Y.Z, got {version!r}")
    nums: list[int] = []
    for p in parts:
        if not p.isdigit():
            raise ValueError(f"non-integer segment in {version!r}")
        nums.append(int(p))
    nums[2] += 1
    return ".".join(str(n) for n in nums)


def next_patch_from_repo(repo_root: Path) -> str:
    from source_versions import read_source_versions

    data = read_source_versions(repo_root)
    android_name = data["android"]["version_name"]
    ios_name = data["ios"]["version_name"]
    if android_name != ios_name:
        raise ValueError(
            f"Android versionName {android_name!r} != iOS MARKETING_VERSION {ios_name!r}; align before release"
        )
    return bump_semver_patch(android_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute next patch version from repo sources")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        nxt = next_patch_from_repo(root)
    except Exception as exc:
        print(f"monthly_release_utils: {exc}", file=sys.stderr)
        return 1
    print(nxt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
