#!/usr/bin/env python3
"""Pull REAL download/install numbers from Google Play and App Store Connect APIs.

Unlike store_downloads_snapshot.py (PostHog proxy), this queries the actual store APIs:
- Google Play: androidpublisher v3 reviews endpoint (review count as install proxy)
  and acquisitions data via the Play Developer Reporting API
- App Store Connect: Sales and Trends reports for units sold/downloaded

Requires:
  Android: GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH
  iOS: APPSTORE_KEY_ID + APPSTORE_ISSUER_ID + APPSTORE_PRIVATE_KEY

Usage:
  python scripts/real_store_downloads.py [--repo-root .] [--days 30]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ANDROID_PACKAGE = "com.iganapolsky.randomtimer"
IOS_BUNDLE_ID = "com.igorganapolsky.randomtimer"
IOS_APP_ID = "6758355312"

_SCRIPTS_DIR = Path(__file__).resolve().parent
_ASC_DIR = _SCRIPTS_DIR / "asc"
for _p in (_SCRIPTS_DIR, _ASC_DIR):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)


def _asc_get_with_retries(
    requests_mod: Any,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
    *,
    attempts: int = 3,
    timeout: float = 60.0,
) -> Any:
    """App Store Connect can spike with connect timeouts; retry with backoff."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return requests_mod.get(url, headers=headers, params=params, timeout=timeout)
        except requests_mod.RequestException as exc:
            last_exc = exc
            if i < attempts - 1:
                time.sleep(2.0 * (i + 1))
    assert last_exc is not None
    raise last_exc

# Google Play Reply-to-Reviews API: list only includes reviews with user *comments*
# (star-only ratings are omitted), and only those created or modified in the last 7 days.
# Public Play Store totals can be higher. See:
# https://developers.google.com/android-publisher/reply-to-reviews

ANDROID_REVIEW_COUNT_METRIC_ID = (
    "google_play_androidpublisher_reviews_list_7d_commented_paginated"
)
ANDROID_REFUND_COUNT_METRIC_ID = (
    "google_play_androidpublisher_voidedpurchases_list_window_paginated"
)
IOS_REVIEW_COUNT_METRIC_ID = (
    "app_store_connect_customer_reviews_sort_created_desc_limit_50"
)
IOS_REFUND_COUNT_METRIC_ID = (
    "app_store_connect_sales_reports_daily_summary_negative_units_sum"
)


def _fetch_all_play_reviews_list(service: Any, package_name: str) -> list[dict[str, Any]]:
    """Paginate reviews.list (max 100 per page per API)."""
    accumulated: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"packageName": package_name, "maxResults": 100}
        if page_token:
            kwargs["token"] = page_token
        result = service.reviews().list(**kwargs).execute()
        accumulated.extend(result.get("reviews", []))
        page_token = (result.get("tokenPagination") or {}).get("nextPageToken")
        if not page_token:
            break
    return accumulated


def _fetch_all_android_voided_purchases(
    service: Any,
    package_name: str,
    days: int,
) -> list[dict[str, Any]]:
    """Paginate purchases.voidedpurchases.list for the trailing window."""
    window_days = max(1, min(int(days), 29))
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - int(window_days * 24 * 60 * 60 * 1000)
    accumulated: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {
            "packageName": package_name,
            "startTime": str(start_ms),
            "endTime": str(end_ms),
            "maxResults": 1000,
        }
        if page_token:
            kwargs["token"] = page_token
        result = service.purchases().voidedpurchases().list(**kwargs).execute()
        accumulated.extend(result.get("voidedPurchases", []))
        page_token = (result.get("tokenPagination") or {}).get("nextPageToken")
        if not page_token:
            break
    return accumulated


def _summarize_voided_purchases(voided: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize refund/void records returned by Android Publisher API."""
    reason_counts: dict[str, int] = {}
    for item in voided:
        reason = str(item.get("voidedReason", "unknown"))
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "refund_requests_30d": len(voided),
        "voided_purchase_reason_counts": reason_counts,
    }


def _parse_asc_sales_report_rows(raw: bytes) -> list[dict[str, str]]:
    """Parse ASC sales report bytes (gzip TSV or plain TSV) into row dicts."""
    if not raw:
        return []
    try:
        decoded = gzip.decompress(raw).decode("utf-8", errors="replace")
    except Exception:
        decoded = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(decoded), delimiter="\t")
    rows: list[dict[str, str]] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        rows.append({str(k or ""): str(v or "") for k, v in row.items()})
    return rows


def _summarize_ios_refunds_from_sales_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Treat negative Units rows as refund units in ASC daily sales summaries."""
    refund_units = 0.0
    gross_units = 0.0
    for row in rows:
        units_raw = (row.get("Units") or "").strip()
        if not units_raw:
            continue
        try:
            units = float(units_raw)
        except ValueError:
            continue
        if units < 0:
            refund_units += abs(units)
        elif units > 0:
            gross_units += units
    return {
        "ios_refund_units_30d": int(round(refund_units)),
        "ios_gross_units_30d": int(round(gross_units)),
        "ios_net_units_30d": int(round(gross_units - refund_units)),
    }


def _fetch_asc_sales_report_bytes(
    requests_mod: Any,
    headers: dict[str, str],
    vendor_number: str,
    report_date: dt.date,
) -> bytes | None:
    """Fetch one daily ASC sales summary report as raw bytes."""
    resp = _asc_get_with_retries(
        requests_mod,
        f"{APP_STORE_CONNECT_API}/salesReports",
        headers=headers,
        params={
            "filter[frequency]": "DAILY",
            "filter[reportDate]": report_date.strftime("%Y-%m-%d"),
            "filter[reportSubType]": "SUMMARY",
            "filter[reportType]": "SALES",
            "filter[vendorNumber]": vendor_number,
            "filter[version]": "1_0",
        },
        timeout=90.0,
    )
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise RuntimeError(f"ASC salesReports HTTP {resp.status_code}")
    return resp.content or b""


def _get_android_data(days: int) -> dict[str, Any]:
    """Query Google Play Developer API for real install data."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from pem_env import load_google_play_service_account_dict
    except ImportError:
        return {"status": "skipped", "reason": "google-api-python-client not installed"}

    key_path = os.environ.get("GOOGLE_PLAY_JSON_KEY", "").strip()
    if not key_path:
        key_path = os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH", "").strip()
    if not key_path:
        return {"status": "skipped", "reason": "no GOOGLE_PLAY_JSON_KEY"}

    try:
        info = load_google_play_service_account_dict(key_path)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
    except Exception as e:
        return {"status": "error", "reason": f"credential error: {e}"}

    try:
        service = build("androidpublisher", "v3", credentials=credentials)

        # Recent, comment-bearing reviews only (Google API rules — not public listing total).
        reviews = _fetch_all_play_reviews_list(service, ANDROID_PACKAGE)
        review_count = len(reviews)

        # Get the current track info to confirm we're live
        edit_id = service.edits().insert(
            packageName=ANDROID_PACKAGE, body={},
        ).execute()["id"]

        tracks = service.edits().tracks().list(
            packageName=ANDROID_PACKAGE,
            editId=edit_id,
        ).execute().get("tracks", [])

        production_track = None
        for track in tracks:
            if track.get("track") == "production":
                production_track = track
                break

        service.edits().delete(
            packageName=ANDROID_PACKAGE,
            editId=edit_id,
        ).execute()

        production_version = None
        if production_track and production_track.get("releases"):
            latest = production_track["releases"][0]
            production_version = {
                "version_codes": latest.get("versionCodes", []),
                "status": latest.get("status"),
                "name": latest.get("name"),
            }

        refund_summary: dict[str, Any] = {}
        try:
            voided = _fetch_all_android_voided_purchases(service, ANDROID_PACKAGE, days)
            refund_summary = _summarize_voided_purchases(voided)
            refund_summary["refund_count_metric_id"] = ANDROID_REFUND_COUNT_METRIC_ID
            refund_summary["refund_window_days"] = max(1, min(int(days), 29))
        except Exception as exc:
            refund_summary = {
                "refund_requests_30d": None,
                "refund_count_metric_id": ANDROID_REFUND_COUNT_METRIC_ID,
                "refund_window_days": max(1, min(int(days), 29)),
                "refund_error": str(exc),
            }

        return {
            "status": "ok",
            "review_count": review_count,
            "review_count_metric_id": ANDROID_REVIEW_COUNT_METRIC_ID,
            "production_release": production_version,
            **refund_summary,
            "note": (
                "Play reviews.list: comment-bearing reviews created or modified in the last "
                "7 days only; star-only ratings are excluded. Not equal to public Play "
                "review totals. No per-app download count in this API."
            ),
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def _get_ios_data(days: int) -> dict[str, Any]:
    """Query App Store Connect API for app info and sales data."""
    try:
        from asc_client import ASCAuth, AscClientError, APP_STORE_CONNECT_API
    except ImportError:
        return {"status": "skipped", "reason": "asc_client not importable"}

    try:
        import requests
    except ImportError:
        return {"status": "skipped", "reason": "requests not installed"}

    try:
        auth = ASCAuth.from_env()
    except Exception as e:
        return {"status": "skipped", "reason": str(e)}

    headers = {
        "Authorization": f"Bearer {auth.jwt()}",
        "Content-Type": "application/json",
    }

    result: dict[str, Any] = {"status": "ok"}

    # Get app info
    try:
        resp = _asc_get_with_retries(
            requests,
            f"{APP_STORE_CONNECT_API}/apps/{IOS_APP_ID}",
            headers=headers,
        )
        if resp.status_code == 200:
            app_data = resp.json().get("data", {}).get("attributes", {})
            result["app_name"] = app_data.get("name")
            result["bundle_id"] = app_data.get("bundleId")
            result["sku"] = app_data.get("sku")
        else:
            result["app_info_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["app_info_error"] = str(e)

    # Get current version state
    try:
        resp = _asc_get_with_retries(
            requests,
            f"{APP_STORE_CONNECT_API}/apps/{IOS_APP_ID}/appStoreVersions",
            headers=headers,
            params={"filter[platform]": "IOS", "limit": 5},
        )
        if resp.status_code == 200:
            versions = resp.json().get("data", [])
            result["versions"] = [
                {
                    "version": v["attributes"].get("versionString"),
                    "state": v["attributes"].get("appStoreState"),
                    "created": v["attributes"].get("createdDate"),
                }
                for v in versions
            ]
        else:
            result["versions_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["versions_error"] = str(e)

    # Get customer reviews (real users only)
    try:
        resp = _asc_get_with_retries(
            requests,
            f"{APP_STORE_CONNECT_API}/apps/{IOS_APP_ID}/customerReviews",
            headers=headers,
            params={"limit": 50, "sort": "-createdDate"},
        )
        if resp.status_code == 200:
            reviews = resp.json().get("data", [])
            result["review_count"] = len(reviews)
            result["review_count_metric_id"] = IOS_REVIEW_COUNT_METRIC_ID
            result["review_count_request_limit"] = 50
            result["reviews"] = [
                {
                    "rating": r["attributes"].get("rating"),
                    "title": r["attributes"].get("title"),
                    "body": (r["attributes"].get("body") or "")[:100],
                    "date": r["attributes"].get("createdDate"),
                }
                for r in reviews[:10]
            ]
        else:
            result["reviews_error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["reviews_error"] = str(e)

    # Note: Sales and Trends API requires a separate report request
    # and may be unavailable for the current date until processing catches up.
    vendor_number = (os.environ.get("APPSTORE_VENDOR_NUMBER") or "").strip()
    if vendor_number:
        try:
            all_rows: list[dict[str, str]] = []
            days_with_data = 0
            today_utc = dt.datetime.now(dt.timezone.utc).date()
            for offset in range(1, max(1, int(days)) + 1):
                report_day = today_utc - dt.timedelta(days=offset)
                blob = _fetch_asc_sales_report_bytes(
                    requests,
                    headers,
                    vendor_number,
                    report_day,
                )
                if not blob:
                    continue
                rows = _parse_asc_sales_report_rows(blob)
                if rows:
                    days_with_data += 1
                    all_rows.extend(rows)
            refund_summary = _summarize_ios_refunds_from_sales_rows(all_rows)
            result.update(refund_summary)
            result["refund_count_metric_id"] = IOS_REFUND_COUNT_METRIC_ID
            result["sales_report_vendor_number_present"] = True
            result["sales_report_days_scanned"] = int(days)
            result["sales_report_days_with_data"] = days_with_data
        except Exception as e:
            result["refund_error"] = str(e)
            result["refund_count_metric_id"] = IOS_REFUND_COUNT_METRIC_ID
            result["sales_report_vendor_number_present"] = True
    else:
        result["refund_count_metric_id"] = IOS_REFUND_COUNT_METRIC_ID
        result["sales_report_vendor_number_present"] = False

    result["note"] = (
        "App Store Connect Sales reports require async report generation. "
        "customerReviews count is the first page only (limit 50, newest first), "
        "not total lifetime App Store reviews. Version state is live from the API. "
        "iOS refund units are derived from negative Units rows in ASC daily SALES/SUMMARY "
        "reports when APPSTORE_VENDOR_NUMBER is configured."
    )

    return result


def run(repo_root: Path, days: int = 30) -> dict:
    output_path = repo_root / "marketing" / "data" / "real_store_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    android = _get_android_data(days)
    ios = _get_ios_data(days)

    payload = {
        "generated_at": generated_at,
        "source": "store_apis",
        "reliability_contract_doc": "docs/OPERATIONAL_RELIABILITY.md",
        "note": "Real store API data, not PostHog proxy",
        "android": android,
        "ios": ios,
    }

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Print summary
    print("=" * 60)
    print("  REAL STORE DATA (from APIs, not PostHog)")
    print("=" * 60)
    print(f"  Android: {android.get('status')}")
    if android.get("review_count") is not None:
        mid = android.get("review_count_metric_id") or ""
        suffix = f" [{mid}]" if mid else ""
        print(f"    Reviews: {android['review_count']}{suffix}")
    if android.get("production_release"):
        pr = android["production_release"]
        print(f"    Production: {pr.get('name')} ({pr.get('status')})")
    print(f"  iOS: {ios.get('status')}")
    if ios.get("review_count") is not None:
        mid = ios.get("review_count_metric_id") or ""
        suffix = f" [{mid}]" if mid else ""
        print(f"    Reviews: {ios['review_count']}{suffix}")
    if ios.get("versions"):
        for v in ios["versions"][:3]:
            print(f"    Version {v['version']}: {v['state']}")
    print(f"  Output: {output_path}")
    print("=" * 60)

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull real store download data")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--days", type=int, default=30, help="Lookback window")
    parser.add_argument("--json", action="store_true", help="JSON output only")
    args = parser.parse_args()

    result = run(Path(args.repo_root).resolve(), days=args.days)
    if args.json:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
