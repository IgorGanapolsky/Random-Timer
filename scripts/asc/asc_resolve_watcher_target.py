#!/usr/bin/env python3
"""Resolve the marketing version store-release-watcher should track."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from scripts.asc.asc_client import ASCClient, AscClientError
from scripts.asc.asc_submit_for_review import die, get_app

IN_FLIGHT_STATES = frozenset(
    {
        "WAITING_FOR_REVIEW",
        "IN_REVIEW",
        "PENDING_DEVELOPER_RELEASE",
        "PENDING_APPLE_RELEASE",
        "PROCESSING_FOR_APP_STORE",
    }
)


def _parse_semver(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"\s*(\d+)\.(\d+)\.(\d+)\s*", value or "")
    if not match:
        raise ValueError(f"Invalid semantic version: {value!r} (expected X.Y.Z)")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def pick_watcher_target(
    *,
    versions: list[dict[str, Any]],
    develop_tip: str,
) -> dict[str, str]:
    """Prefer the highest semver among in-flight ASC versions; else develop tip."""
    candidates: list[tuple[tuple[int, int, int], str, str]] = []
    for item in versions:
        attrs = item.get("attributes") or {}
        version = str(attrs.get("versionString") or "")
        state = str(attrs.get("appStoreState") or "UNKNOWN")
        if state not in IN_FLIGHT_STATES:
            continue
        try:
            parsed = _parse_semver(version)
        except ValueError:
            continue
        candidates.append((parsed, version, state))

    if candidates:
        candidates.sort(key=lambda row: row[0], reverse=True)
        _, target_version, state = candidates[0]
        return {
            "target_version": target_version,
            "state": state,
            "reason": "in_flight_highest",
            "develop_tip": develop_tip,
        }

    return {
        "target_version": develop_tip,
        "state": "",
        "reason": "develop_tip_fallback",
        "develop_tip": develop_tip,
    }


def _list_ios_versions(client: ASCClient, app_id: str) -> list[dict[str, Any]]:
    return client.get_all(
        f"/apps/{app_id}/appStoreVersions",
        params={
            "filter[platform]": "IOS",
            "limit": 200,
            "fields[appStoreVersions]": "versionString,appStoreState",
        },
    )


def _read_develop_tip(repo_root: Path) -> str:
    from scripts.source_versions import read_source_versions

    return str(read_source_versions(repo_root)["ios"]["version_name"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--develop-tip",
        help="Override develop marketing version (defaults to source_versions.py ios.version_name).",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    develop_tip = (args.develop_tip or "").strip() or _read_develop_tip(repo_root)

    try:
        _parse_semver(develop_tip)
    except ValueError as exc:
        die(str(exc), code=2)

    try:
        client = ASCClient.from_env(timeout=30)
        app = get_app(client, args.bundle_id)
        versions = _list_ios_versions(client, str(app["id"]))
    except AscClientError as exc:
        die(str(exc), code=2)

    payload = pick_watcher_target(versions=versions, develop_tip=develop_tip)
    payload["bundle_id"] = args.bundle_id

    if args.json:
        print(json.dumps(payload))
    else:
        print(payload["target_version"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
