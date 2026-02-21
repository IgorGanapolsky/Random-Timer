#!/usr/bin/env python3
"""Store downloads tracker.

Fetches download/install counts from Google Play Console and
App Store Connect, stores rolling snapshots in marketing/data/,
and feeds into the Daily Metrics Dashboard via wiki-sync.

Data sources:
  - Google Play: gsutil CSV reports from GCS bucket (no API key needed
    if Cloud Storage bucket is configured), OR Play Developer Reporting API.
  - App Store Connect: Sales & Trends API via App Store Connect key.

When API credentials are unavailable, reads from cached data or
reports zeros — never fails.

Designed to run weekly via GitHub Actions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


DOWNLOADS_PATH = "marketing/data/store_downloads.json"


def load_downloads_history(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / DOWNLOADS_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "snapshots": [],
        "ios": {"total_downloads": 0, "downloads_30d": 0},
        "android": {"total_downloads": 0, "downloads_30d": 0, "active_installs": 0},
        "combined": {"total_downloads": 0, "downloads_30d": 0},
    }


def save_downloads_history(repo_root: Path, history: Dict[str, Any]) -> None:
    path = repo_root / DOWNLOADS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def fetch_android_downloads() -> Dict[str, Any]:
    """Fetch Android install counts.

    Priority:
    1. Google Play Developer Reporting API (needs GOOGLE_PLAY_SERVICE_ACCOUNT_JSON)
    2. GCS bucket CSV reports (needs GOOGLE_PLAY_BUCKET_NAME)
    3. Return zeros
    """
    sa_json = os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
    bucket = os.environ.get("GOOGLE_PLAY_BUCKET_NAME", "")

    if sa_json:
        return _fetch_android_from_api(sa_json)
    if bucket:
        return _fetch_android_from_gcs(bucket)

    return {"total_downloads": 0, "downloads_30d": 0, "active_installs": 0}


def _fetch_android_from_api(sa_json: str) -> Dict[str, Any]:
    """Fetch from Google Play Developer Reporting API."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_json),
            scopes=["https://www.googleapis.com/auth/playdeveloperreporting"],
        )
        service = build("playdeveloperreporting", "v1beta1", credentials=creds)
        # Query installs metric for the app
        package_name = "com.iganapolsky.randomtimer"
        end = dt.date.today()
        start = end - dt.timedelta(days=30)
        body = {
            "dimensions": [],
            "metrics": ["totalInstalls", "activeDeviceInstalls"],
            "timelineSpec": {
                "startTime": {"year": start.year, "month": start.month, "day": start.day},
                "endTime": {"year": end.year, "month": end.month, "day": end.day},
                "aggregationPeriod": "DAILY",
            },
        }
        result = (
            service.vitals()
            .storeperformance()
            .query(name=f"apps/{package_name}/storePerformanceStats", body=body)
            .execute()
        )
        rows = result.get("rows", [])
        total = sum(int(r.get("metrics", {}).get("totalInstalls", 0)) for r in rows)
        active = 0
        if rows:
            active = int(rows[-1].get("metrics", {}).get("activeDeviceInstalls", 0))
        return {"total_downloads": total, "downloads_30d": total, "active_installs": active}
    except Exception as e:
        print(f"[downloads] Google Play API error: {e}")
        return {"total_downloads": 0, "downloads_30d": 0, "active_installs": 0}


def _fetch_android_from_gcs(bucket: str) -> Dict[str, Any]:
    """Fetch from Google Cloud Storage CSV reports."""
    try:
        from google.cloud import storage

        client = storage.Client()
        bkt = client.bucket(bucket)
        # Play Console exports monthly stats as CSVs
        blobs = list(bkt.list_blobs(prefix="stats/installs/"))
        if not blobs:
            return {"total_downloads": 0, "downloads_30d": 0, "active_installs": 0}
        latest = sorted(blobs, key=lambda b: b.name)[-1]
        content = latest.download_as_text()
        # Parse CSV: Date,Package Name,Daily Device Installs,Daily User Installs,...
        lines = content.strip().split("\n")[1:]  # skip header
        total = 0
        for line in lines:
            cols = line.split(",")
            if len(cols) >= 4:
                total += int(cols[3])  # Daily User Installs
        return {"total_downloads": total, "downloads_30d": total, "active_installs": 0}
    except Exception as e:
        print(f"[downloads] GCS error: {e}")
        return {"total_downloads": 0, "downloads_30d": 0, "active_installs": 0}


def fetch_ios_downloads() -> Dict[str, Any]:
    """Fetch iOS download counts from App Store Connect Sales API.

    Needs: APPSTORE_KEY_ID, APPSTORE_ISSUER_ID, APPSTORE_PRIVATE_KEY
    """
    key_id = os.environ.get("APPSTORE_KEY_ID", "")
    issuer_id = os.environ.get("APPSTORE_ISSUER_ID", "")
    private_key = os.environ.get("APPSTORE_PRIVATE_KEY", "")

    if not all([key_id, issuer_id, private_key]):
        return {"total_downloads": 0, "downloads_30d": 0}

    try:
        import jwt
        import requests

        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "iss": issuer_id,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(minutes=20)).timestamp()),
            "aud": "appstoreconnect-v1",
        }
        token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": key_id})
        headers = {"Authorization": f"Bearer {token}"}

        end = dt.date.today()
        start = end - dt.timedelta(days=30)
        url = (
            "https://api.appstoreconnect.apple.com/v1/salesReports"
            f"?filter[frequency]=DAILY"
            f"&filter[reportSubType]=SUMMARY"
            f"&filter[reportType]=SALES"
            f"&filter[vendorNumber]={os.environ.get('APPSTORE_VENDOR_NUMBER', '')}"
            f"&filter[reportDate]={end.isoformat()}"
        )
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.ok:
            # Parse TSV sales report
            lines = resp.text.strip().split("\n")[1:]
            total = 0
            for line in lines:
                cols = line.split("\t")
                if len(cols) >= 8 and cols[6] in ("1", "1F", "1T"):  # Product Type = App
                    total += int(cols[7])  # Units
            return {"total_downloads": total, "downloads_30d": total}
        else:
            print(f"[downloads] ASC API error: {resp.status_code}")
            return {"total_downloads": 0, "downloads_30d": 0}
    except Exception as e:
        print(f"[downloads] ASC error: {e}")
        return {"total_downloads": 0, "downloads_30d": 0}


def fetch_posthog_active_users() -> Dict[str, Any]:
    """Fetch active user counts from PostHog.

    Needs: POSTHOG_PERSONAL_API_KEY, POSTHOG_PROJECT_ID
    """
    api_key = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "")

    if not all([api_key, project_id]):
        return {"dau": 0, "wau": 0, "mau": 0}

    try:
        import requests

        headers = {"Authorization": f"Bearer {api_key}"}
        base = f"https://us.i.posthog.com/api/projects/{project_id}"

        # Query unique users in last 1, 7, 30 days
        results = {}
        for label, days in [("dau", 1), ("wau", 7), ("mau", 30)]:
            end = dt.date.today()
            start = end - dt.timedelta(days=days)
            query = {
                "query": {
                    "kind": "HogQLQuery",
                    "query": (
                        f"SELECT count(DISTINCT distinct_id) as users "
                        f"FROM events "
                        f"WHERE timestamp >= '{start.isoformat()}' "
                        f"AND timestamp < '{end.isoformat()}' "
                        f"AND event NOT LIKE '$%'"
                    ),
                }
            }
            resp = requests.post(f"{base}/query/", json=query, headers=headers, timeout=30)
            if resp.ok:
                data = resp.json()
                rows = data.get("results", [[0]])
                results[label] = int(rows[0][0]) if rows and rows[0] else 0
            else:
                results[label] = 0

        return results
    except Exception as e:
        print(f"[downloads] PostHog active users error: {e}")
        return {"dau": 0, "wau": 0, "mau": 0}


def record_snapshot(repo_root: Path) -> Dict[str, Any]:
    """Take a point-in-time snapshot of download metrics."""
    history = load_downloads_history(repo_root)

    android = fetch_android_downloads()
    ios = fetch_ios_downloads()
    active_users = fetch_posthog_active_users()

    snapshot = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "ios_downloads_30d": ios["downloads_30d"],
        "android_downloads_30d": android["downloads_30d"],
        "android_active_installs": android.get("active_installs", 0),
        "dau": active_users.get("dau", 0),
        "wau": active_users.get("wau", 0),
        "mau": active_users.get("mau", 0),
    }

    history["snapshots"].append(snapshot)
    # Keep last 90 snapshots
    history["snapshots"] = history["snapshots"][-90:]

    combined_30d = ios["downloads_30d"] + android["downloads_30d"]
    history["ios"] = ios
    history["android"] = android
    history["active_users"] = active_users
    history["combined"] = {
        "total_downloads": ios.get("total_downloads", 0) + android.get("total_downloads", 0),
        "downloads_30d": combined_30d,
    }

    save_downloads_history(repo_root, history)
    return history


def main() -> int:
    parser = argparse.ArgumentParser(description="Track store downloads")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    history = record_snapshot(repo_root)

    ios = history["ios"]
    android = history["android"]
    users = history.get("active_users", {})
    print(f"[downloads] iOS 30d: {ios['downloads_30d']}")
    print(f"[downloads] Android 30d: {android['downloads_30d']}")
    print(f"[downloads] Android active installs: {android.get('active_installs', 0)}")
    print(f"[downloads] PostHog DAU: {users.get('dau', 0)} | WAU: {users.get('wau', 0)} | MAU: {users.get('mau', 0)}")
    print(f"[downloads] Combined 30d: {history['combined']['downloads_30d']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
