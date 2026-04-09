#!/usr/bin/env python3
"""Remove an App Store version submission from review and wait until editable."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from scripts.asc.asc_client import ASCClient, AscClientError
from scripts.asc.asc_poll_version_state import find_app_store_version_id
from scripts.asc.asc_resolve_version import _is_editable_state
from scripts.asc.asc_submit_for_review import die, get_app, get_version_state, info


def _submission_id(payload: dict[str, object]) -> str:
    data = payload.get("data")
    if isinstance(data, dict):
        return str(data.get("id") or "")
    return ""


def _wait_for_editable_state(
    client: ASCClient,
    *,
    version_id: str,
    timeout: int,
    poll_interval: int,
) -> str:
    deadline = time.time() + timeout
    state = get_version_state(client, version_id)
    while True:
        if _is_editable_state(state):
            return state
        if time.time() >= deadline:
            return state
        time.sleep(poll_interval)
        state = get_version_state(client, version_id)


@dataclass
class RemovalResult:
    bundle_id: str
    app_id: str
    version: str
    version_id: str
    initial_state: str
    final_state: str
    submission_id: str
    removed: bool
    became_editable: bool
    reason: str


def remove_from_review(
    client: ASCClient,
    *,
    bundle_id: str,
    version: str,
    wait: bool,
    timeout: int,
    poll_interval: int,
) -> RemovalResult:
    app = get_app(client, bundle_id)
    app_id = str(app.get("id") or "")
    if not app_id:
        die(f"Could not resolve app id for bundleId={bundle_id}", code=2)

    version_id, initial_state = find_app_store_version_id(client, app_id=app_id, version=version)
    submission_payload = client.request("GET", f"/appStoreVersions/{version_id}/appStoreVersionSubmission")
    submission_id = _submission_id(submission_payload)

    if not submission_id:
        final_state = get_version_state(client, version_id)
        return RemovalResult(
            bundle_id=bundle_id,
            app_id=app_id,
            version=version,
            version_id=version_id,
            initial_state=initial_state,
            final_state=final_state,
            submission_id="",
            removed=False,
            became_editable=_is_editable_state(final_state),
            reason="no_submission_found",
        )

    client.request("DELETE", f"/appStoreVersionSubmissions/{submission_id}")

    if wait:
        final_state = _wait_for_editable_state(
            client,
            version_id=version_id,
            timeout=timeout,
            poll_interval=poll_interval,
        )
    else:
        final_state = get_version_state(client, version_id)

    return RemovalResult(
        bundle_id=bundle_id,
        app_id=app_id,
        version=version,
        version_id=version_id,
        initial_state=initial_state,
        final_state=final_state,
        submission_id=submission_id,
        removed=True,
        became_editable=_is_editable_state(final_state),
        reason="submission_deleted",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove an App Store version submission from review.")
    parser.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    parser.add_argument("--version", required=True, help="Marketing version to remove from review (e.g. 1.2.6)")
    parser.add_argument("--wait", action="store_true", help="Wait until the App Store version becomes editable.")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--json-out", help="Write the result JSON to this path.")
    parser.add_argument("--json", action="store_true", help="Print compact JSON instead of human-readable text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        client = ASCClient.from_env(timeout=30)
    except AscClientError as exc:
        die(str(exc), code=2)

    result = remove_from_review(
        client,
        bundle_id=args.bundle_id,
        version=args.version,
        wait=args.wait,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
    )
    payload = asdict(result)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        info(
            f"version={result.version} initial={result.initial_state} final={result.final_state} "
            f"removed={result.removed} editable={result.became_editable} reason={result.reason}"
        )

    if args.wait and not result.became_editable:
        die(
            f"App Store version {result.version} is still not editable after remove-from-review "
            f"(final state={result.final_state}).",
            code=1,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
