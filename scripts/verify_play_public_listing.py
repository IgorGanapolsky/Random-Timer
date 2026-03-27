#!/usr/bin/env python3
"""Verify that a Google Play app listing is publicly visible."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

import requests


DEFAULT_TIMEOUT = 900
DEFAULT_POLL_INTERVAL = 60


@dataclass
class PublicListingResult:
    passed: bool
    status: str
    details: str


def build_store_url(package: str, country: str) -> str:
    normalized = (country or "US").strip().upper()
    return f"https://play.google.com/store/apps/details?id={package}&hl=en_{normalized}&gl={normalized}"


def verify_public_listing(url: str) -> PublicListingResult:
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=30,
            headers={"User-Agent": "Random-Timer-Release-Verification/1.0"},
        )
    except requests.RequestException as exc:
        return PublicListingResult(False, "ERROR", f"Play public listing request failed: {exc}")

    status = response.status_code
    date_header = response.headers.get("date", "unknown")
    if status == 200:
        return PublicListingResult(True, "PUBLIC", f"HTTP 200 on {date_header}")
    return PublicListingResult(False, f"HTTP_{status}", f"HTTP {status} on {date_header}")


def poll_until_visible(url: str, timeout: int, poll_interval: int) -> PublicListingResult:
    deadline = time.time() + timeout

    while True:
        result = verify_public_listing(url)
        if result.passed:
            return result

        remaining = deadline - time.time()
        if remaining <= 0:
            return PublicListingResult(
                False,
                "TIMEOUT",
                f"{result.details} (timed out after {timeout}s)",
            )

        time.sleep(min(poll_interval, max(0, remaining)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that the Google Play public listing is visible."
    )
    parser.add_argument("--package", required=True, help="Android package name")
    parser.add_argument("--country", default="US", help="Two-letter storefront country code")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    parser.add_argument(
        "--url",
        help="Explicit store URL. If omitted, generated from --package and --country.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = args.url or build_store_url(args.package, args.country)
    result = poll_until_visible(url, timeout=args.timeout, poll_interval=args.poll_interval)

    print()
    print("══ Play Public Listing Verification ═════════════════")
    print(f"URL:    {url}")
    print(f"Status: {result.status}")
    print(f"Detail: {result.details}")
    print("══════════════════════════════════════════════════════")
    print()

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
