#!/usr/bin/env python3
"""Fail fast when Native App Release is iOS-only on a release/v* branch without explicit confirmation.

Past incidents: Android was skipped because dispatch used platform=ios while the ref was
release/vX.Y.Z, so Google Play never received the AAB. This gate requires an explicit opt-in
to skip Android on release branches (develop/feature branches are unaffected).
"""

from __future__ import annotations

import os
import re
import sys

_RELEASE_BRANCH = re.compile(r"^refs/heads/release/v\d+\.\d+\.\d+$")


def should_block(ref: str, platform: str, confirm_ios_only: str) -> tuple[bool, str]:
    """Return (block, message)."""
    platform = (platform or "").strip().lower()
    confirm = (confirm_ios_only or "").strip().lower() in ("1", "true", "yes")

    if not _RELEASE_BRANCH.match(ref or ""):
        return False, ""

    if platform != "ios":
        return False, ""

    if confirm:
        return False, ""

    return (
        True,
        (
            "Blocked: platform=ios on a release/v* branch skips Android (no Play upload).\n"
            "To ship iOS-only intentionally, re-run with confirm_ios_only_release=true.\n"
            "To ship both stores (recommended for a versioned release), use platform=both (default)."
        ),
    )


def main() -> int:
    ref = os.environ.get("GITHUB_REF", "")
    platform = os.environ.get("RELEASE_INTENT_PLATFORM", "")
    confirm = os.environ.get("RELEASE_INTENT_CONFIRM_IOS_ONLY", "false")

    block, msg = should_block(ref, platform, confirm)
    if block:
        print(msg, file=sys.stderr)
        return 1
    print(
        f"release_intent_gate: ok ref={ref!r} platform={platform!r} "
        f"confirm_ios_only={confirm!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
