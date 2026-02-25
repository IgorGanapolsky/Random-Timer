#!/usr/bin/env python3
"""Query Firebase Crashlytics crash data via BigQuery streaming export.

Usage:
    python scripts/check_crashlytics.py [--threshold 99.0] [--hours 24]

Setup (one-time in Firebase Console):
    1. Firebase Console > Crashlytics > BigQuery integration > Link
    2. This enables streaming export to: random-timer-486213.firebase_crashlytics.{app_id}

Requires:
    - gcloud auth (or GOOGLE_APPLICATION_CREDENTIALS)
    - BigQuery API enabled on random-timer-486213
    - Firebase project: random-timer-486213
"""

import argparse
import json
import subprocess
import sys
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone


PROJECT_ID = "random-timer-486213"
PACKAGE = "com.iganapolsky.randomtimer"
# BigQuery dataset created by Crashlytics streaming export
BQ_DATASET = "firebase_crashlytics"
DEFAULT_THRESHOLD = 99.0


def get_access_token():
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: gcloud auth failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def bq_query(token, sql):
    """Execute a BigQuery SQL query."""
    ctx = ssl.create_default_context()
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT_ID}/queries"
    body = json.dumps({
        "query": sql,
        "useLegacySql": False,
        "maxResults": 100,
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        resp = urllib.request.urlopen(req, context=ctx)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            msg = json.loads(error_body).get("error", {}).get("message", "")
        except Exception:
            msg = error_body[:300]
        return {"error": msg, "code": e.code}


def check_bigquery_export(token):
    """Check if Crashlytics BQ export is set up by listing tables."""
    ctx = ssl.create_default_context()
    url = (
        f"https://bigquery.googleapis.com/bigquery/v2"
        f"/projects/{PROJECT_ID}/datasets/{BQ_DATASET}/tables?maxResults=10"
    )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        resp = urllib.request.urlopen(req, context=ctx)
        data = json.loads(resp.read())
        tables = [t["tableReference"]["tableId"] for t in data.get("tables", [])]
        return tables
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # Dataset doesn't exist
        error_body = e.read().decode()
        print(f"WARNING: BigQuery API returned {e.code}: {error_body[:200]}", file=sys.stderr)
        return None


def query_crash_summary(token, hours):
    """Query crash summary from BigQuery."""
    # Crashlytics BQ export table naming: {sanitized_app_id}
    # For com.iganapolsky.randomtimer -> com_iganapolsky_randomtimer
    table_suffix = PACKAGE.replace(".", "_")

    sql = f"""
    SELECT
      COUNT(*) as crash_count,
      COUNT(DISTINCT installation_uuid) as affected_users,
      error_type,
      SUBSTR(blame_frame.file, 1, 80) as file,
      blame_frame.line as line,
      SUBSTR(exception_type, 1, 60) as exception,
      SUBSTR(exception_message, 1, 100) as message,
      app_version as version,
    FROM `{PROJECT_ID}.{BQ_DATASET}.{table_suffix}`
    WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
      AND error_type = 'FATAL'
    GROUP BY error_type, file, line, exception, message, version
    ORDER BY crash_count DESC
    LIMIT 20
    """
    return bq_query(token, sql)


def query_crash_free_rate(token, hours):
    """Calculate crash-free user rate from BigQuery."""
    table_suffix = PACKAGE.replace(".", "_")

    sql = f"""
    WITH sessions AS (
      SELECT
        installation_uuid,
        MAX(CASE WHEN error_type = 'FATAL' THEN 1 ELSE 0 END) as had_crash
      FROM `{PROJECT_ID}.{BQ_DATASET}.{table_suffix}`
      WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
      GROUP BY installation_uuid
    )
    SELECT
      COUNT(*) as total_users,
      SUM(CASE WHEN had_crash = 0 THEN 1 ELSE 0 END) as crash_free_users,
      ROUND(100.0 * SUM(CASE WHEN had_crash = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as crash_free_pct
    FROM sessions
    """
    return bq_query(token, sql)


def main():
    parser = argparse.ArgumentParser(description="Check Crashlytics stability via BigQuery")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Crash-free %% threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--hours", type=int, default=24,
                        help="Look-back window in hours (default: 24)")
    args = parser.parse_args()

    token = get_access_token()

    # Check if BQ export exists
    tables = check_bigquery_export(token)
    if tables is None:
        print("Crashlytics BigQuery export not set up.")
        print("To enable: Firebase Console > Crashlytics > BigQuery integration > Link")
        print("This is required for automated crash monitoring in CI.")
        sys.exit(0)

    print(f"BigQuery tables found: {tables}")

    # Query crash summary
    print(f"\n--- Crash summary (last {args.hours}h) ---")
    result = query_crash_summary(token, args.hours)
    if "error" in result:
        print(f"Query error: {result['error']}")
    elif result.get("rows"):
        for row in result["rows"]:
            vals = [f.get("v", "") for f in row["f"]]
            count, users, err_type, file, line, exc, msg, ver = vals
            print(f"  {count} crashes ({users} users) v{ver}: {exc} - {msg}")
            print(f"    at {file}:{line}")
    else:
        print("  No crashes found!")

    # Query crash-free rate
    print(f"\n--- Crash-free rate (last {args.hours}h) ---")
    rate_result = query_crash_free_rate(token, args.hours)
    if "error" in rate_result:
        print(f"Query error: {rate_result['error']}")
    elif rate_result.get("rows"):
        vals = [f.get("v", "") for f in rate_result["rows"][0]["f"]]
        total, crash_free, pct = vals
        print(f"  Total users: {total}")
        print(f"  Crash-free: {crash_free} ({pct}%)")
        if float(pct or 100) < args.threshold:
            print(f"  FAIL: Below {args.threshold}% threshold")
            sys.exit(1)
        else:
            print(f"  PASS: Above {args.threshold}% threshold")
    else:
        print("  No session data found.")

    print("\nDone.")


if __name__ == "__main__":
    main()
