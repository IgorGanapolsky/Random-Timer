#!/usr/bin/env python3
"""List App Store Connect iOS App Store versions and their states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from scripts.asc_client import ASCClient, AscClientError
from scripts.asc_resolve_version import _list_ios_versions
from scripts.asc_submit_for_review import die, get_app


def _normalize_versions(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for item in items:
        attrs = item.get("attributes") or {}
        normalized.append(
            {
                "id": str(item.get("id") or ""),
                "version": str(attrs.get("versionString") or ""),
                "state": str(attrs.get("appStoreState") or "UNKNOWN"),
                "createdDate": str(attrs.get("createdDate") or ""),
            }
        )
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List App Store Connect iOS App Store versions.")
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--json-out", help="Write the resolved version inventory JSON to this path.")
    parser.add_argument("--json", action="store_true", help="Print compact JSON instead of a text table.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        client = ASCClient.from_env(timeout=30)
    except AscClientError as exc:
        die(str(exc), code=2)

    app = get_app(client, args.bundle_id)
    app_id = str(app.get("id") or "")
    if not app_id:
        die(f"Could not resolve app id for bundleId={args.bundle_id}", code=2)

    versions = _normalize_versions(_list_ios_versions(client, app_id))
    payload = {
        "bundle_id": args.bundle_id,
        "app_id": app_id,
        "count": len(versions),
        "versions": versions,
    }

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
        return 0

    print(f"App: {args.bundle_id} (id={app_id})")
    print(f"Versions: {len(versions)}")
    for item in versions:
        print(
            f"- {item['version'] or '?'} | state={item['state']} | "
            f"createdDate={item['createdDate'] or '?'} | id={item['id'] or '?'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
