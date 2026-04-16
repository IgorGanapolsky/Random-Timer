#!/usr/bin/env python3
"""Read-only store ratings snapshot from App Store Connect and Play Developer APIs.

Writes JSON evidence with explicit semantics: averages are computed over **API
return samples**, not necessarily the same number as the public store listing
aggregate star display.

iOS: App Store Connect ``GET /v1/apps/{id}/customerReviews`` (paginated).
Android: ``androidpublisher.reviews.list`` (paginated). See ``review_count_metric_id``
fields in output and ``docs/OPERATIONAL_RELIABILITY.md``.

Usage:
  python scripts/store_ratings_snapshot.py --json-out marketing/data/store_ratings_snapshot.json
  python scripts/store_ratings_snapshot.py --json-out /tmp/out.json --no-dotenv --limit 500

Env (same as other store scripts):
  iOS: APPSTORE_KEY_ID, APPSTORE_ISSUER_ID, APPSTORE_PRIVATE_KEY (or path variants)
  Android: GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IOS_BUNDLE_ID_DEFAULT = "com.igorganapolsky.randomtimer"
ANDROID_PACKAGE_DEFAULT = "com.iganapolsky.randomtimer"

IOS_RATING_SAMPLE_METRIC_ID = "asc_customer_reviews_api_paginated_sample_mean_v1"
ANDROID_RATING_SAMPLE_METRIC_ID = "google_play_androidpublisher_reviews_list_paginated_sample_mean_v1"


def histogram_and_mean(ratings: list[int]) -> tuple[dict[str, int], float, int]:
    valid = [r for r in ratings if isinstance(r, int) and 1 <= r <= 5]
    hist = {str(i): 0 for i in range(1, 6)}
    for r in valid:
        hist[str(r)] += 1
    mean = round(sum(valid) / len(valid), 3) if valid else 0.0
    return hist, mean, len(valid)


def ios_rating_from_item(item: dict[str, Any]) -> int | None:
    attrs = item.get("attributes") or {}
    raw = attrs.get("rating") if attrs.get("rating") is not None else attrs.get("value")
    if raw is None:
        return None
    try:
        r = int(raw)
    except (TypeError, ValueError):
        return None
    if 1 <= r <= 5:
        return r
    return None


def play_star_from_review(review: dict[str, Any]) -> int | None:
    for block in review.get("comments") or []:
        if not isinstance(block, dict):
            continue
        uc = block.get("userComment")
        if not isinstance(uc, dict):
            continue
        sr = uc.get("starRating")
        if sr is None:
            continue
        try:
            r = int(sr)
        except (TypeError, ValueError):
            continue
        if 1 <= r <= 5:
            return r
    return None


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_ios_review_items(client: Any, app_id: str, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url: str | None = None
    first_params: dict[str, str] | None = {
        "limit": str(min(limit, 200)),
        "sort": "-createdDate",
        "fields[customerReviews]": "rating,title,body,territory,createdDate",
    }

    while True:
        if next_url:
            payload = client.get(next_url)
        else:
            payload = client.get(f"/apps/{app_id}/customerReviews", params=first_params)
            first_params = None

        for item in payload.get("data", []) or []:
            items.append(item)
            if len(items) >= limit:
                return items

        next_url = (payload.get("links") or {}).get("next")
        if not next_url:
            break

    return items


def fetch_play_reviews_capped(service: Any, package: str, cap: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    page_token: str | None = None
    while len(out) < cap:
        kwargs: dict[str, Any] = {"packageName": package, "maxResults": 100}
        if page_token:
            kwargs["token"] = page_token
        result = service.reviews().list(**kwargs).execute()
        revs = result.get("reviews") or []
        if not revs:
            break
        for r in revs:
            out.append(r)
            if len(out) >= cap:
                return out
        page_token = (result.get("tokenPagination") or {}).get("nextPageToken")
        if not page_token:
            break
    return out


def build_ios_ratings(bundle_id: str, limit: int) -> dict[str, Any]:
    from scripts.asc.asc_client import ASCClient, AscClientError

    base: dict[str, Any] = {
        "platform": "ios",
        "bundle_id": bundle_id,
        "review_count_metric_id": IOS_RATING_SAMPLE_METRIC_ID,
        "semantics": (
            "average_rating is the arithmetic mean of star ratings in the paginated "
            "App Store Connect customerReviews sample (see review_sample_size). It is NOT "
            "the public App Store listing lifetime aggregate unless that aggregate happens "
            "to match this sample."
        ),
    }
    try:
        client = ASCClient.from_env(timeout=60)
    except AscClientError as exc:
        return {**base, "status": "skipped", "reason": str(exc)}

    try:
        app_payload = client.get("/apps", params={"filter[bundleId]": bundle_id, "limit": 1})
        rows = app_payload.get("data") or []
        if not rows:
            return {**base, "status": "error", "reason": f"No ASC app for bundle_id={bundle_id}"}
        app_id = str(rows[0].get("id"))
        items = fetch_ios_review_items(client, app_id, limit)
        ratings: list[int] = []
        for it in items:
            r = ios_rating_from_item(it)
            if r is not None:
                ratings.append(r)
        hist, mean, n = histogram_and_mean(ratings)
        return {
            **base,
            "status": "ok",
            "app_id": app_id,
            "review_sample_size": len(items),
            "rated_in_sample_count": n,
            "average_rating_sample_mean": mean,
            "rating_histogram": hist,
        }
    except Exception as exc:
        return {**base, "status": "error", "reason": str(exc)}


def build_android_ratings(package: str, limit: int) -> dict[str, Any]:
    base: dict[str, Any] = {
        "platform": "android",
        "package_name": package,
        "review_count_metric_id": ANDROID_RATING_SAMPLE_METRIC_ID,
        "semantics": (
            "Play reviews.list returns a developer-API view of reviews; per Google, the "
            "reply-to-reviews surface can omit star-only ratings and applies recency rules. "
            "average_rating_sample_mean is over the paginated rows returned here only."
        ),
    }
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        return {**base, "status": "skipped", "reason": f"missing dependency: {exc}"}

    try:
        from pem_env import load_google_play_service_account_dict
    except ImportError as exc:
        return {**base, "status": "skipped", "reason": f"missing dependency: {exc}"}

    key_path = (os.environ.get("GOOGLE_PLAY_JSON_KEY") or "").strip() or (
        os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH") or ""
    ).strip()
    if not key_path:
        return {**base, "status": "skipped", "reason": "no GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH"}

    try:
        info = load_google_play_service_account_dict(key_path)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
        service = build("androidpublisher", "v3", credentials=credentials)
        reviews = fetch_play_reviews_capped(service, package, limit)
        ratings = []
        for rev in reviews:
            r = play_star_from_review(rev)
            if r is not None:
                ratings.append(r)
        hist, mean, n = histogram_and_mean(ratings)
        return {
            **base,
            "status": "ok",
            "review_sample_size": len(reviews),
            "rated_in_sample_count": n,
            "average_rating_sample_mean": mean,
            "rating_histogram": hist,
        }
    except Exception as exc:
        return {**base, "status": "error", "reason": str(exc)}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json-out", required=True, help="Path to write JSON evidence")
    p.add_argument("--limit", type=int, default=500, help="Max reviews to include per platform")
    p.add_argument("--ios-bundle-id", default=IOS_BUNDLE_ID_DEFAULT)
    p.add_argument("--android-package", default=ANDROID_PACKAGE_DEFAULT)
    p.add_argument(
        "--no-dotenv",
        action="store_true",
        help="Do not load repo-root .env (CI provides secrets via env)",
    )
    p.add_argument("--repo-root", type=Path, default=ROOT, help="Repository root for dotenv")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.no_dotenv:
        from scripts.repo_dotenv import load_repo_dotenv

        load_repo_dotenv(args.repo_root)

    out = {
        "generated_at": _iso_now(),
        "command_semantics": (
            "python scripts/store_ratings_snapshot.py read-only GETs; no store mutations."
        ),
        "ios": build_ios_ratings(args.ios_bundle_id, max(1, args.limit)),
        "android": build_android_ratings(args.android_package, max(1, args.limit)),
    }

    path = Path(args.json_out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "json_out": str(path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
