#!/usr/bin/env python3
"""Guard Play foreground-service declaration acknowledgement before release."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


SPECIAL_USE_SERVICE_TYPE = re.compile(r'android:foregroundServiceType\s*=\s*"[^"]*\bspecialUse\b[^"]*"')


def manifest_requires_special_use_declaration(manifest_path: Path) -> bool:
    text = manifest_path.read_text(encoding="utf-8")
    return "android.permission.FOREGROUND_SERVICE_SPECIAL_USE" in text or bool(SPECIAL_USE_SERVICE_TYPE.search(text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--require-ack-env", default="PLAY_FGS_DECLARATION_ACK")
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    if not manifest_requires_special_use_declaration(args.manifest):
        print("OK: no Play foreground-service special-use declaration required.")
        return 0

    ack = os.environ.get(args.require_ack_env, "").strip()
    if not ack:
        print(
            f"ERROR: manifest uses foregroundServiceType=specialUse; set {args.require_ack_env} "
            "after confirming the matching Play Console foreground-service declaration.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: Play foreground-service special-use declaration acknowledged by {args.require_ack_env}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
