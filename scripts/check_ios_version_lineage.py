#!/usr/bin/env python3
"""Prevent iOS TestFlight uploads from regressing behind live ASC pre-release versions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

try:
    from scripts.asc_client import ASCClient, AscClientError
    from scripts.source_versions import VersionParseError, read_source_versions
except ModuleNotFoundError:
    from asc_client import ASCClient, AscClientError
    from source_versions import VersionParseError, read_source_versions


SEMVER_RE = re.compile(r"^\s*(\d+)\.(\d+)\.(\d+)\s*$")
APP_STORE_CLOSED_STATES = {
    "ACCEPTED",
    "APPROVED",
    "IN_REVIEW",
    "PENDING_APPLE_RELEASE",
    "PENDING_DEVELOPER_RELEASE",
    "PENDING_DEVELOPER_RELEASE_REJECTED",
    "PENDING_RELEASE",
    "PREORDER_READY_FOR_SALE",
    "PROCESSING_FOR_DISTRIBUTION",
    "READY_FOR_DISTRIBUTION",
    "READY_FOR_SALE",
    "REMOVED_FROM_SALE",
    "REPLACED_WITH_NEW_VERSION",
    "WAITING_FOR_EXPORT_COMPLIANCE",
    "WAITING_FOR_REVIEW",
}


class LineageError(RuntimeError):
    """Raised when local iOS versioning regresses behind App Store Connect."""


@dataclass
class LineageReport:
    bundle_id: str
    local_version: str
    local_build: int
    highest_remote_version: Optional[str]
    highest_remote_app_store_version: Optional[str]
    highest_remote_app_store_state: Optional[str]
    highest_closed_app_store_version: Optional[str]
    highest_remote_build_for_highest_version: Optional[int]
    highest_remote_build_for_local_version: Optional[int]
    passed: bool
    reason: str


def _parse_semver(value: str) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(value or "")
    if not match:
        raise ValueError(f"Invalid semantic version: {value!r} (expected X.Y.Z)")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _semver_or_none(value: str) -> Optional[tuple[int, int, int]]:
    try:
        return _parse_semver(value)
    except ValueError:
        return None


def _highest_semver(versions: list[str]) -> Optional[str]:
    ranked: list[tuple[tuple[int, int, int], str]] = []
    for version in versions:
        parsed = _semver_or_none(version)
        if parsed is None:
            continue
        ranked.append((parsed, version.strip()))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def _build_int_or_none(value: object) -> Optional[int]:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _highest_build(build_numbers: list[int]) -> Optional[int]:
    return max(build_numbers) if build_numbers else None


def _highest_version_by_state(version_states: dict[str, str]) -> tuple[Optional[str], Optional[str]]:
    ranked: list[tuple[tuple[int, int, int], str, str]] = []
    for version, state in version_states.items():
        parsed = _semver_or_none(version)
        if parsed is None:
            continue
        ranked.append((parsed, version.strip(), str(state or "").strip().upper()))
    if not ranked:
        return None, None
    ranked.sort(key=lambda item: item[0], reverse=True)
    _, version, state = ranked[0]
    return version, state


def _get_app_id(client: ASCClient, bundle_id: str) -> str:
    data = client.get("/apps", params={"filter[bundleId]": bundle_id})
    apps = data.get("data", [])
    if not apps:
        raise LineageError(f"No App Store Connect app found for bundleId={bundle_id}")
    return str(apps[0].get("id") or "")


def _list_remote_pre_release_versions(client: ASCClient, app_id: str) -> list[str]:
    items = client.get_all(
        "/preReleaseVersions",
        params={
            "filter[app]": app_id,
            "limit": 200,
            "fields[preReleaseVersions]": "version,platform",
        },
    )
    versions: list[str] = []
    for item in items:
        attrs = item.get("attributes") or {}
        if str(attrs.get("platform") or "").upper() != "IOS":
            continue
        version = str(attrs.get("version") or "").strip()
        if version:
            versions.append(version)
    return versions


def _list_remote_app_store_versions(client: ASCClient, app_id: str) -> dict[str, str]:
    items = client.get_all(
        f"/apps/{app_id}/appStoreVersions",
        params={
            "filter[platform]": "IOS",
            "limit": 200,
            "fields[appStoreVersions]": "versionString,appStoreState",
        },
    )
    versions: dict[str, str] = {}
    for item in items:
        attrs = item.get("attributes") or {}
        version = str(attrs.get("versionString") or "").strip()
        if not version:
            continue
        versions[version] = str(attrs.get("appStoreState") or "UNKNOWN").strip().upper()
    return versions


def _list_remote_builds_by_marketing_version(client: ASCClient, app_id: str) -> dict[str, list[int]]:
    data = client.get(
        "/builds",
        params={
            "filter[app]": app_id,
            "include": "preReleaseVersion",
            "sort": "-uploadedDate",
            "limit": 200,
            "fields[builds]": "version,preReleaseVersion",
            "fields[preReleaseVersions]": "version",
        },
    )

    pre_release_versions: dict[str, str] = {}
    for item in data.get("included", []):
        if item.get("type") != "preReleaseVersions":
            continue
        version = str((item.get("attributes") or {}).get("version") or "").strip()
        if version:
            pre_release_versions[str(item.get("id") or "")] = version

    builds_by_version: dict[str, list[int]] = {}
    for build in data.get("data", []):
        rel = (
            (build.get("relationships") or {})
            .get("preReleaseVersion", {})
            .get("data")
            or {}
        )
        marketing_version = pre_release_versions.get(str(rel.get("id") or ""))
        build_number = _build_int_or_none((build.get("attributes") or {}).get("version"))
        if marketing_version is None or build_number is None:
            continue
        builds_by_version.setdefault(marketing_version, []).append(build_number)
    return builds_by_version


def evaluate_lineage(
    *,
    bundle_id: str,
    local_version: str,
    local_build: int,
    remote_versions: list[str],
    remote_app_store_versions: dict[str, str],
    remote_builds_by_version: dict[str, list[int]],
) -> LineageReport:
    highest_remote_pre_release_version = _highest_semver(remote_versions)
    highest_remote_app_store_version, highest_remote_app_store_state = _highest_version_by_state(
        remote_app_store_versions
    )
    highest_closed_app_store_version, _ = _highest_version_by_state(
        {
            version: state
            for version, state in remote_app_store_versions.items()
            if state in APP_STORE_CLOSED_STATES
        }
    )
    highest_remote_version = _highest_semver(
        remote_versions + list(remote_app_store_versions.keys())
    )
    highest_remote_build_for_local_version = _highest_build(remote_builds_by_version.get(local_version, []))
    highest_remote_build_for_highest_version = (
        _highest_build(remote_builds_by_version.get(highest_remote_version, []))
        if highest_remote_version is not None
        else None
    )

    if highest_remote_version is None:
        return LineageReport(
            bundle_id=bundle_id,
            local_version=local_version,
            local_build=local_build,
            highest_remote_version=None,
            highest_remote_app_store_version=highest_remote_app_store_version,
            highest_remote_app_store_state=highest_remote_app_store_state,
            highest_closed_app_store_version=highest_closed_app_store_version,
            highest_remote_build_for_highest_version=None,
            highest_remote_build_for_local_version=highest_remote_build_for_local_version,
            passed=True,
            reason="no_remote_ios_versions_found",
        )

    if _parse_semver(local_version) < _parse_semver(highest_remote_version):
        return LineageReport(
            bundle_id=bundle_id,
            local_version=local_version,
            local_build=local_build,
            highest_remote_version=highest_remote_version,
            highest_remote_app_store_version=highest_remote_app_store_version,
            highest_remote_app_store_state=highest_remote_app_store_state,
            highest_closed_app_store_version=highest_closed_app_store_version,
            highest_remote_build_for_highest_version=highest_remote_build_for_highest_version,
            highest_remote_build_for_local_version=highest_remote_build_for_local_version,
            passed=False,
            reason=(
                f"Local iOS marketing version {local_version} regresses behind "
                f"App Store Connect version {highest_remote_version}"
            ),
        )

    if (
        highest_closed_app_store_version is not None
        and _parse_semver(local_version) <= _parse_semver(highest_closed_app_store_version)
    ):
        return LineageReport(
            bundle_id=bundle_id,
            local_version=local_version,
            local_build=local_build,
            highest_remote_version=highest_remote_version,
            highest_remote_app_store_version=highest_remote_app_store_version,
            highest_remote_app_store_state=highest_remote_app_store_state,
            highest_closed_app_store_version=highest_closed_app_store_version,
            highest_remote_build_for_highest_version=highest_remote_build_for_highest_version,
            highest_remote_build_for_local_version=highest_remote_build_for_local_version,
            passed=False,
            reason=(
                f"Local iOS marketing version {local_version} is blocked by closed App Store "
                f"version {highest_closed_app_store_version}; bump the marketing version first"
            ),
        )

    if highest_remote_build_for_local_version is not None and local_build < highest_remote_build_for_local_version:
        reason = (
            f"Local iOS build {local_build} trails ASC build {highest_remote_build_for_local_version} "
            f"for version {local_version}; next TestFlight upload will auto-increment."
        )
    else:
        reason = "local_ios_version_lineage_is_current"

    return LineageReport(
        bundle_id=bundle_id,
        local_version=local_version,
        local_build=local_build,
        highest_remote_version=highest_remote_version,
        highest_remote_app_store_version=highest_remote_app_store_version,
        highest_remote_app_store_state=highest_remote_app_store_state,
        highest_closed_app_store_version=highest_closed_app_store_version,
        highest_remote_build_for_highest_version=highest_remote_build_for_highest_version,
        highest_remote_build_for_local_version=highest_remote_build_for_local_version,
        passed=True,
        reason=reason,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate local iOS source version against live App Store Connect pre-release versions."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--json-out", default="", help="Optional JSON report output path")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()

    try:
        versions = read_source_versions(repo_root)
    except (OSError, VersionParseError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    try:
        client = ASCClient.from_env(timeout=30)
        app_id = _get_app_id(client, args.bundle_id)
        remote_versions = _list_remote_pre_release_versions(client, app_id)
        remote_app_store_versions = _list_remote_app_store_versions(client, app_id)
        remote_builds_by_version = _list_remote_builds_by_marketing_version(client, app_id)
    except (AscClientError, LineageError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    report = evaluate_lineage(
        bundle_id=args.bundle_id,
        local_version=str(versions["ios"]["version_name"]),
        local_build=int(versions["ios"]["build_number"]),
        remote_versions=remote_versions,
        remote_app_store_versions=remote_app_store_versions,
        remote_builds_by_version=remote_builds_by_version,
    )

    print(f"Local iOS source version: {report.local_version} ({report.local_build})")
    print(f"ASC highest pre-release version: {report.highest_remote_version or 'none'}")
    if report.highest_remote_app_store_version is not None:
        print(
            "ASC highest App Store version: "
            f"{report.highest_remote_app_store_version} "
            f"(state={report.highest_remote_app_store_state or 'UNKNOWN'})"
        )
    if report.highest_closed_app_store_version is not None:
        print(
            "ASC highest closed App Store version: "
            f"{report.highest_closed_app_store_version}"
        )
    if report.highest_remote_build_for_highest_version is not None:
        print(
            "ASC highest build for highest version: "
            f"{report.highest_remote_build_for_highest_version}"
        )
    if report.highest_remote_build_for_local_version is not None:
        print(
            f"ASC highest build for local version {report.local_version}: "
            f"{report.highest_remote_build_for_local_version}"
        )
    print(report.reason)

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(asdict(report), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
