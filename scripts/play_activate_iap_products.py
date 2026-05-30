#!/usr/bin/env python3
"""Activate required Google Play monetization products for Random Timer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.play_monetization_client import (
    PACKAGE,
    TARGET_ONE_TIME,
    activate_one_time_product,
    build_android_publisher_service,
    resolve_play_credentials,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", default="", help="Optional JSON output path")
    parser.add_argument("--dry-run", action="store_true", help="Inspect only; do not mutate")
    args = parser.parse_args()

    key_value = resolve_play_credentials()
    if not key_value:
        print("Missing GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH", file=sys.stderr)
        return 2

    service = build_android_publisher_service(key_value)
    report: dict = {
        "package": PACKAGE,
        "dry_run": args.dry_run,
        "target_one_time": TARGET_ONE_TIME,
    }

    if args.dry_run:
        from scripts.play_monetization_client import list_one_time_products

        report["one_time_products"] = list_one_time_products(service)
    else:
        report["activation"] = activate_one_time_product(service, TARGET_ONE_TIME)

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)

    activation = report.get("activation") or {}
    errors = [item for item in activation.get("actions") or [] if item.get("action") == "error"]
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
