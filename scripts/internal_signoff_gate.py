#!/usr/bin/env python3
"""Block production release unless required internal signoff statuses exist on the exact SHA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_CONTEXTS = {
    "ios": ("internal-signoff/testflight",),
    "android": ("internal-signoff/firebase",),
    "both": ("internal-signoff/testflight", "internal-signoff/firebase"),
}


def _latest_status_by_context(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for status in payload.get("statuses", []):
        context = str(status.get("context") or "").strip()
        if not context or context in latest:
            continue
        latest[context] = status
    return latest


def evaluate_signoff(platform: str, payload: dict[str, Any]) -> tuple[bool, list[str]]:
    normalized_platform = (platform or "").strip().lower()
    required = REQUIRED_CONTEXTS.get(normalized_platform)
    if required is None:
        raise ValueError(f"Unsupported platform: {platform!r}")

    latest = _latest_status_by_context(payload)
    problems: list[str] = []
    for context in required:
        status = latest.get(context)
        if status is None:
            problems.append(f"missing required status: {context}")
            continue
        state = str(status.get("state") or "").strip().lower()
        if state != "success":
            problems.append(f"{context} is {state or 'unknown'}")
    return (not problems, problems)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=("ios", "android", "both"))
    parser.add_argument("--statuses-json", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.statuses_json.read_text(encoding="utf-8"))
    passed, problems = evaluate_signoff(args.platform, payload)
    if not passed:
        print("Blocked: missing required internal signoff proof for this release SHA.", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    required = ", ".join(REQUIRED_CONTEXTS[args.platform])
    print(f"internal_signoff_gate: ok platform={args.platform} required={required}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
