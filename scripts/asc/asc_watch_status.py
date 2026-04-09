#!/usr/bin/env python3
"""Watch App Store Connect status for a specific iOS version.

This watcher uses ASC API key auth (no browser state required) and appends a
JSONL entry whenever the target version state changes.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.asc.asc_client import ASCClient, AscClientError
from scripts.asc.asc_poll_version_state import find_app_store_version_id
from scripts.asc.asc_submit_for_review import die, get_app


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def poll_state(client: ASCClient, *, bundle_id: str, version: str) -> Dict[str, str]:
    app = get_app(client, bundle_id)
    app_id = app["id"]
    version_id, state = find_app_store_version_id(client, app_id=app_id, version=version)
    return {
        "iso": utc_iso_now(),
        "bundle_id": bundle_id,
        "app_id": app_id,
        "version": version,
        "version_id": version_id,
        "state": state,
    }


def _read_last_jsonl(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def append_if_changed(path: Path, record: Dict[str, str]) -> bool:
    last = _read_last_jsonl(path)
    changed = (
        last is None
        or last.get("state") != record.get("state")
        or last.get("version_id") != record.get("version_id")
        or last.get("version") != record.get("version")
    )
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
    return changed


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Watch App Store Connect state changes for a target iOS version.")
    p.add_argument("--bundle-id", default="com.igorganapolsky.randomtimer")
    p.add_argument("--version", required=True, help="Marketing version to watch, e.g. 1.1.2")
    p.add_argument("--jsonl", default=".artifacts/asc-status-history.jsonl", help="Output JSONL path.")
    p.add_argument("--interval", type=int, default=300, help="Polling interval seconds.")
    p.add_argument("--max-polls", type=int, default=1, help="Number of polls (1 for one-shot).")
    p.add_argument("--print-json", action="store_true", help="Print each polled record as JSON.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_polls <= 0:
        raise SystemExit("max-polls must be >= 1")

    out_path = Path(args.jsonl).resolve()
    try:
        client = ASCClient.from_env(timeout=30)
    except AscClientError as exc:
        die(str(exc), code=2)

    for idx in range(args.max_polls):
        record = poll_state(client, bundle_id=args.bundle_id, version=args.version)
        changed = append_if_changed(out_path, record)
        if args.print_json:
            print(json.dumps({"changed": changed, **record}, ensure_ascii=True))
        else:
            print(
                f"[{record['iso']}] version={record['version']} state={record['state']} "
                f"changed={str(changed).lower()} jsonl={out_path}"
            )

        if idx < args.max_polls - 1:
            time.sleep(args.interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
