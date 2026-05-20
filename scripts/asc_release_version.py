#!/usr/bin/env python3
"""Release an approved iOS App Store version (manual release)."""

from __future__ import annotations

import argparse
import json
import sys

from scripts.asc.asc_client import ASCClient, AscClientError
from scripts.asc.asc_poll_version_state import find_app_store_version_id
from scripts.asc.asc_submit_for_review import die, get_app, get_version_state, info


def release_version(client: ASCClient, *, version_id: str) -> dict:
    return client.request(
        "POST",
        "/appStoreVersionReleaseRequests",
        json_body={
            "data": {
                "type": "appStoreVersionReleaseRequests",
                "relationships": {
                    "appStoreVersion": {
                        "data": {"type": "appStoreVersions", "id": version_id}
                    }
                },
            }
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--version", required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        client = ASCClient.from_env(timeout=30)
    except AscClientError as exc:
        die(str(exc), code=2)

    app = get_app(client, args.bundle_id)
    app_id = app["id"]
    version_id, state = find_app_store_version_id(client, app_id=app_id, version=args.version)
    if state == "READY_FOR_SALE":
        payload = {
            "app_id": app_id,
            "version_id": version_id,
            "version": args.version,
            "state": state,
            "released": False,
            "reason": "already_ready_for_sale",
        }
        if args.json:
            print(json.dumps(payload))
        else:
            info(f"Version {args.version} already READY_FOR_SALE; no release request sent.")
        return 0

    if state != "PENDING_DEVELOPER_RELEASE":
        die(f"Version {args.version} is {state}; expected PENDING_DEVELOPER_RELEASE or READY_FOR_SALE")

    response = release_version(client, version_id=version_id)
    final_state = get_version_state(client, version_id)
    payload = {
        "app_id": app_id,
        "version_id": version_id,
        "version": args.version,
        "prior_state": state,
        "state": final_state,
        "released": True,
        "response_id": ((response.get("data") or {}) if isinstance(response, dict) else {}).get("id"),
    }
    if args.json:
        print(json.dumps(payload))
    else:
        info(json.dumps(payload, indent=2))
    return 0 if final_state in ("READY_FOR_SALE", "PROCESSING_FOR_APP_STORE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
