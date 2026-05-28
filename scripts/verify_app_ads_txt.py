#!/usr/bin/env python3
"""Verify hosted app-ads.txt contains the AdMob publisher authorization line."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://igorganapolsky.github.io/Random-Timer/app-ads.txt"
EXPECTED_PUBLISHER = "pub-5173650670360699"
EXPECTED_LINE = f"google.com, {EXPECTED_PUBLISHER}, DIRECT, f08c47fec0942fa0"


def fetch(url: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Random-Timer-app-ads-verify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def verify_app_ads_txt(
    *,
    url: str,
    publisher_id: str = EXPECTED_PUBLISHER,
    timeout: int = 30,
) -> tuple[bool, str]:
    try:
        body = fetch(url, timeout)
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code} for {url}"
    except urllib.error.URLError as exc:
        return False, f"fetch failed: {exc.reason}"

    lines = [ln.strip() for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    pattern = re.compile(
        rf"^google\.com,\s*{re.escape(publisher_id)},\s*DIRECT,\s*f08c47fec0942fa0\s*$",
        re.IGNORECASE,
    )
    if any(pattern.match(ln) for ln in lines):
        return True, f"ok: found authorized line for {publisher_id} at {url}"
    return False, f"missing line for {publisher_id} at {url} (got {len(lines)} non-comment lines)"


def main() -> int:
    p = argparse.ArgumentParser(description="Verify app-ads.txt is published and authorized.")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--publisher-id", default=EXPECTED_PUBLISHER)
    p.add_argument("--timeout", type=int, default=30)
    args = p.parse_args()
    ok, msg = verify_app_ads_txt(url=args.url, publisher_id=args.publisher_id, timeout=args.timeout)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
