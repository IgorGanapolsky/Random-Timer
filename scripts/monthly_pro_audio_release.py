#!/usr/bin/env python3
"""Prepare customer-facing release notes for monthly Pro audio releases."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.source_versions import read_source_versions
except ModuleNotFoundError:
    from source_versions import read_source_versions


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "content" / "pro_audio" / "monthly_pro_audio_packs.json"
IOS_RELEASE_NOTES_PATH = REPO_ROOT / "native-ios" / "fastlane" / "metadata" / "en-US" / "release_notes.txt"
ANDROID_CHANGELOG_DIR = REPO_ROOT / "native-android" / "fastlane" / "metadata" / "android" / "en-US" / "changelogs"
VERSIONED_RELEASE_NOTES_DIR = REPO_ROOT / "release-notes"
SEMVER_RE = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$")


class MonthlyReleaseError(RuntimeError):
    """Raised when the monthly release payload cannot be prepared."""


def _parse_semver(version: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(version.strip())
    if not match:
        raise MonthlyReleaseError(f"Expected semantic version X.Y.Z, got {version!r}")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def next_patch_version(current_version: str) -> str:
    major, minor, patch = _parse_semver(current_version)
    return f"{major}.{minor}.{patch + 1}"


def resolve_release_version(repo_root: Path, requested_version: str = "") -> str:
    versions = read_source_versions(repo_root)
    android_version = str(versions["android"]["version_name"])
    ios_version = str(versions["ios"]["version_name"])
    if android_version != ios_version:
        raise MonthlyReleaseError(
            f"Android/iOS version mismatch: android={android_version} ios={ios_version}"
        )

    if requested_version.strip():
        requested = _parse_semver(requested_version)
        current = _parse_semver(android_version)
        if requested <= current:
            raise MonthlyReleaseError(
                f"Requested version {requested_version} must be greater than current version {android_version}"
            )
        return requested_version.strip()
    return next_patch_version(android_version)


def _load_active_pack(repo_root: Path) -> dict[str, Any]:
    manifest = json.loads((repo_root / "content/pro_audio/monthly_pro_audio_packs.json").read_text(encoding="utf-8"))
    active_pack_id = manifest.get("activePackId")
    for pack in manifest.get("packs", []):
        if pack.get("id") == active_pack_id:
            return pack
    raise MonthlyReleaseError(f"Active Pro audio pack {active_pack_id!r} is missing from manifest.")


def _customer_month(release_month: str) -> str:
    year, month = (int(part) for part in release_month.split("-"))
    names = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    return f"{names[month - 1]} {year}"


def render_versioned_release_notes(version: str, pack: dict[str, Any]) -> str:
    release_month = str(pack["releaseMonth"])
    active_pack_id = str(pack["id"])
    theme = str(pack.get("theme") or "Monthly Pro audio")
    customer_month = _customer_month(release_month)
    return f"""# Release {version}

## Summary
Monthly Pro audio release for {customer_month}: {theme}.

## Customer-visible changes
- Adds a new Pro voice callout pack for {customer_month}.
- Refreshes bundled Pro Sound Arsenal audio for iOS and Android.
- Keeps the hosted Pro audio manifest current for entitlement restore, purchase, and app foreground refresh.

## Release operations
- Generated from active Pro audio pack `{active_pack_id}`.
- Bundles iOS and Android audio assets so store builds carry the monthly fallback sounds.
- Preserves hosted runtime delivery for existing Pro users where the app can safely refresh remote voice assets.
"""


def render_store_release_notes(pack: dict[str, Any]) -> str:
    customer_month = _customer_month(str(pack["releaseMonth"]))
    theme = str(pack.get("theme") or "Monthly Pro audio")
    return "\n".join(
        [
            f"Monthly Pro audio refresh for {customer_month}.",
            f"New voice callouts: {theme}.",
            "Refreshed bundled Pro Sound Arsenal audio for iOS and Android.",
            "Reliability improvements for hosted Pro audio delivery.",
        ]
    )


def write_release_notes(repo_root: Path, version: str, *, json_out: Path | None = None) -> dict[str, Any]:
    _parse_semver(version)
    versions = read_source_versions(repo_root)
    pack = _load_active_pack(repo_root)
    android_code = int(versions["android"]["version_code"])

    versioned_path = repo_root / "release-notes" / f"{version}.md"
    android_changelog_path = (
        repo_root
        / "native-android"
        / "fastlane"
        / "metadata"
        / "android"
        / "en-US"
        / "changelogs"
        / f"{android_code}.txt"
    )
    ios_release_notes_path = repo_root / "native-ios" / "fastlane" / "metadata" / "en-US" / "release_notes.txt"

    versioned_path.parent.mkdir(parents=True, exist_ok=True)
    android_changelog_path.parent.mkdir(parents=True, exist_ok=True)
    ios_release_notes_path.parent.mkdir(parents=True, exist_ok=True)

    versioned_text = render_versioned_release_notes(version, pack)
    store_text = render_store_release_notes(pack)
    versioned_path.write_text(versioned_text, encoding="utf-8")
    android_changelog_path.write_text(store_text + "\n", encoding="utf-8")
    ios_release_notes_path.write_text(store_text + "\n", encoding="utf-8")

    payload = {
        "version": version,
        "android_version_code": android_code,
        "ios_version": versions["ios"]["version_name"],
        "active_pack_id": pack["id"],
        "release_month": pack["releaseMonth"],
        "files": [
            str(versioned_path.relative_to(repo_root)),
            str(android_changelog_path.relative_to(repo_root)),
            str(ios_release_notes_path.relative_to(repo_root)),
        ],
    }
    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    next_parser = subparsers.add_parser("next-version", help="Print the next monthly release version.")
    next_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    next_parser.add_argument("--version", default="", help="Explicit version override.")

    notes_parser = subparsers.add_parser("write-notes", help="Write store and GitHub release notes.")
    notes_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    notes_parser.add_argument("--version", required=True)
    notes_parser.add_argument("--json-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    try:
        if args.command == "next-version":
            print(resolve_release_version(repo_root, args.version))
            return 0
        if args.command == "write-notes":
            payload = write_release_notes(repo_root, args.version, json_out=args.json_out)
            print(json.dumps(payload, indent=2))
            return 0
    except MonthlyReleaseError as exc:
        print(f"[ERROR] {exc}")
        return 1
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
