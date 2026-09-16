#!/usr/bin/env python3
"""Set App Store Connect releaseType (e.g. AFTER_APPROVAL) for a version."""

from __future__ import annotations

import argparse
import json
import sys

from scripts.asc.asc_client import ASCClient, AscClientError
from scripts.asc.asc_poll_version_state import find_app_store_version_id
from scripts.asc.asc_submit_for_review import die, get_app

DEFAULT_RELEASE_TYPE = "AFTER_APPROVAL"


def apply_release_type(
    client: ASCClient,
    *,
    version_id: str,
    release_type: str = DEFAULT_RELEASE_TYPE,
) -> dict[str, object]:
    current = client.get(
        f"/appStoreVersions/{version_id}",
        params={"fields[appStoreVersions]": "releaseType,versionString,appStoreState"},
    )
    data = current.get("data") or {}
    attrs = data.get("attributes") or {}
    prior = str(attrs.get("releaseType") or "")
    if prior == release_type:
        return {
            "version_id": version_id,
            "prior_release_type": prior,
            "release_type": release_type,
            "changed": False,
            "reason": "already_set",
        }

    response = client.request(
        "PATCH",
        f"/appStoreVersions/{version_id}",
        payload={
            "data": {
                "type": "appStoreVersions",
                "id": version_id,
                "attributes": {"releaseType": release_type},
            }
        },
    )
    updated = ((response.get("data") or {}) if isinstance(response, dict) else {}).get(
        "attributes"
    ) or {}
    final_type = str(updated.get("releaseType") or release_type)
    return {
        "version_id": version_id,
        "prior_release_type": prior,
        "release_type": final_type,
        "changed": True,
        "reason": "patched",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--release-type",
        default=DEFAULT_RELEASE_TYPE,
        help="ASC releaseType value (default: AFTER_APPROVAL).",
    )
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
    version_id, state = find_app_store_version_id(
        client, app_id=app_id, version=args.version
    )

    result = apply_release_type(
        client, version_id=version_id, release_type=args.release_type
    )
    payload = {
        "app_id": app_id,
        "version": args.version,
        "state": state,
        **result,
    }
    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
