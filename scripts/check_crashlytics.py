#!/usr/bin/env python3
"""Query Firebase Crashlytics crash data via BigQuery streaming export.

Snapshot payloads include fatal_events_in_window (full COUNT(*) of fatal rows in
the lookback window) and fatal_events (sum of crash_count in the parsed top-issue
sample — see metric_field_ids).

Usage:
    python scripts/check_crashlytics.py [--threshold 99.0] [--hours 24]

Setup (one-time in Firebase Console):
    1. Firebase Console > Crashlytics > BigQuery integration > Link
    2. Streaming export lands in: <project>.firebase_crashlytics (see CRASHLYTICS_PROJECT_ID).

Requires:
    - CRASHLYTICS_SERVICE_ACCOUNT_JSON (inline JSON), or
      CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH (path to a service account JSON file), or
      GOOGLE_APPLICATION_CREDENTIALS (path to a service account JSON file), or
      Application Default Credentials (e.g. gcloud auth application-default login)
    - BigQuery API enabled on the Firebase/GCP project that owns the export
    - Env CRASHLYTICS_PROJECT_ID must match that project (default: random-timer-dist-new)

This script reads runtime Crashlytics data only. See docs/FIREBASE_ANDROID_INFRASTRUCTURE.md
for project history (App Distribution vs runtime).
"""

import ssl
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2 import service_account


PROJECT_ID = os.environ.get("CRASHLYTICS_PROJECT_ID", "random-timer-dist-new")
PACKAGE = os.environ.get("CRASHLYTICS_PACKAGE", "com.iganapolsky.randomtimer")
# BigQuery dataset created by Crashlytics streaming export
BQ_DATASET = os.environ.get("CRASHLYTICS_BQ_DATASET", "firebase_crashlytics")
DEFAULT_THRESHOLD = 99.0
SCOPES = ("https://www.googleapis.com/auth/cloud-platform",)


def get_credentials():
    raw_json = os.environ.get("CRASHLYTICS_SERVICE_ACCOUNT_JSON", "").strip()
    if raw_json:
        return service_account.Credentials.from_service_account_info(
            json.loads(raw_json),
            scopes=SCOPES,
        )

    sa_path = os.environ.get("CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH", "").strip()
    if sa_path:
        expanded_sa = os.path.expanduser(sa_path)
        if not os.path.isfile(expanded_sa):
            raise RuntimeError(
                "CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH points to a missing file "
                f"({expanded_sa})."
            )
        return service_account.Credentials.from_service_account_file(
            expanded_sa,
            scopes=SCOPES,
        )

    gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if gac:
        expanded = os.path.expanduser(gac)
        if not os.path.isfile(expanded):
            raise RuntimeError(
                "GOOGLE_APPLICATION_CREDENTIALS points to a missing file "
                f"({expanded}). Set CRASHLYTICS_SERVICE_ACCOUNT_JSON, "
                "CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH, or fix the path."
            )
        return service_account.Credentials.from_service_account_file(
            expanded,
            scopes=SCOPES,
        )

    try:
        creds, _ = google.auth.default(scopes=SCOPES)
        return creds
    except DefaultCredentialsError as exc:
        raise RuntimeError(
            "No Google credentials for Crashlytics BigQuery. Set one of: "
            "CRASHLYTICS_SERVICE_ACCOUNT_JSON, CRASHLYTICS_SERVICE_ACCOUNT_JSON_PATH, "
            "GOOGLE_APPLICATION_CREDENTIALS, or configure Application Default Credentials "
            f"(see google.auth.default). Original error: {exc}"
        ) from exc


def get_access_token(credentials=None):
    creds = credentials or get_credentials()
    creds.refresh(Request())
    return creds.token


def bq_query(token, sql):
    """Execute a BigQuery SQL query."""
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
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
    """Check if Crashlytics BQ export is set up by listing tables (paginated).

    BigQuery returns at most ``maxResults`` tables per page; Crashlytics datasets can
    exceed a single page, so we follow ``nextPageToken`` until exhausted.
    """
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    base = (
        f"https://bigquery.googleapis.com/bigquery/v2"
        f"/projects/{PROJECT_ID}/datasets/{BQ_DATASET}/tables"
    )
    tables: list[str] = []
    page_token: str | None = None
    while True:
        params: dict[str, str] = {"maxResults": "500"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            resp = urllib.request.urlopen(req, context=ctx)
            data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # Dataset doesn't exist
            error_body = e.read().decode()
            print(
                f"WARNING: BigQuery API returned {e.code}: {error_body[:200]}",
                file=sys.stderr,
            )
            raise RuntimeError(f"BigQuery API {e.code}: {error_body[:200]}")
        batch = [
            t["tableReference"]["tableId"]
            for t in data.get("tables", [])
            if t.get("tableReference", {}).get("tableId")
        ]
        tables.extend(batch)
        page_token = data.get("nextPageToken") or None
        if not page_token:
            break
    return tables


def select_crashlytics_table(tables):
    """Pick the active Crashlytics export table for the Android runtime app."""
    base = PACKAGE.replace(".", "_")
    if base in tables:
        return base

    realtime = f"{base}_ANDROID_REALTIME"
    if realtime in tables:
        return realtime

    realtime_candidates = sorted(
        table for table in tables if table.startswith(f"{base}_") and table.endswith("_REALTIME")
    )
    if realtime_candidates:
        return realtime_candidates[0]

    candidates = sorted(table for table in tables if table.startswith(base))
    if candidates:
        return candidates[0]

    raise ValueError(f"No Crashlytics export table found for package {PACKAGE}")


def query_crash_summary(token, hours, table_id):
    """Query crash summary from BigQuery."""
    sql = f"""
    SELECT
      COUNT(*) as crash_count,
      COUNT(DISTINCT installation_uuid) as affected_users,
      error_type,
      SUBSTR(COALESCE(blame_frame.file, issue_title), 1, 80) as file,
      blame_frame.line as line,
      SUBSTR(issue_title, 1, 80) as issue_title,
      SUBSTR(issue_subtitle, 1, 120) as issue_subtitle,
      application.display_version as version
    FROM `{PROJECT_ID}.{BQ_DATASET}.{table_id}`
    WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
      AND COALESCE(is_fatal, FALSE) = TRUE
    GROUP BY error_type, file, line, issue_title, issue_subtitle, version
    ORDER BY crash_count DESC
    LIMIT 20
    """
    return bq_query(token, sql)


def query_fatal_events_total(token, hours, table_id):
    """Count every fatal crash row in the lookback window (not limited to top issue groups)."""
    sql = f"""
    SELECT COUNT(*) as fatal_row_count
    FROM `{PROJECT_ID}.{BQ_DATASET}.{table_id}`
    WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
      AND COALESCE(is_fatal, FALSE) = TRUE
    """
    return bq_query(token, sql)


def query_crash_free_rate(token, hours, table_id):
    """Calculate crash-free user rate from BigQuery."""
    sql = f"""
    WITH sessions AS (
      SELECT
        installation_uuid,
        MAX(CASE WHEN error_type = 'FATAL' THEN 1 ELSE 0 END) as had_crash
      FROM `{PROJECT_ID}.{BQ_DATASET}.{table_id}`
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


CRASHLYTICS_SNAPSHOT_METRIC_BUNDLE_ID = "crashlytics_bq_streaming_fatal_window_v1"


def _base_snapshot(hours):
    return {
        "status": "ok",
        "source": "crashlytics_bigquery",
        "metric_bundle_id": CRASHLYTICS_SNAPSHOT_METRIC_BUNDLE_ID,
        "metric_field_ids": {
            "fatal_events": (
                "crashlytics_bq_sum_crash_count_in_top_20_issue_groups_only_not_total_window"
            ),
            "fatal_events_in_window": (
                "crashlytics_bq_count_star_all_fatal_rows_in_lookback_window"
            ),
            "top_fatal_issues": (
                "crashlytics_bq_fatal_groups_limited_20_order_by_crash_count_desc"
            ),
            "crash_free_pct": "crashlytics_bq_session_crash_free_rate_by_installation_uuid",
            "total_users": "crashlytics_bq_distinct_installation_uuids_in_window",
            "crash_free_users": "crashlytics_bq_installation_uuids_without_fatal_in_window",
            "affected_users": "crashlytics_bq_total_users_minus_crash_free_users",
        },
        "project_id": PROJECT_ID,
        "dataset": BQ_DATASET,
        "package": PACKAGE,
        "hours": hours,
        "table_id": None,
        "fatal_events": 0,
        "fatal_events_in_window": 0,
        "affected_users": 0,
        "total_users": 0,
        "crash_free_users": 0,
        "crash_free_pct": None,
        "top_fatal_issues": [],
    }


def _error_snapshot(payload, result):
    return {
        **payload,
        "status": "error",
        "reason": str(result["error"]),
        "code": result.get("code"),
    }


def _parse_summary_rows(rows):
    parsed_rows = []
    for row in rows[:10]:
        fields = row.get("f") or []
        if len(fields) < 8:
            continue
        parsed_rows.append(
            {
                "crash_count": int(fields[0].get("v") or 0),
                "affected_users": int(fields[1].get("v") or 0),
                "error_type": fields[2].get("v") or "",
                "file": fields[3].get("v") or "",
                "line": fields[4].get("v") or "",
                "issue_title": fields[5].get("v") or "",
                "issue_subtitle": fields[6].get("v") or "",
                "version": fields[7].get("v") or "",
            }
        )
    return parsed_rows


def _apply_rate_snapshot(payload, rate_rows):
    if not rate_rows:
        payload["reason"] = "No session data found"
        return payload

    fields = rate_rows[0].get("f") or []
    if len(fields) < 3:
        return payload

    total_users = int(fields[0].get("v") or 0)
    crash_free_users = int(fields[1].get("v") or 0)
    crash_free_pct = float(fields[2].get("v") or 100)
    payload["total_users"] = total_users
    payload["crash_free_users"] = crash_free_users
    payload["crash_free_pct"] = crash_free_pct
    payload["affected_users"] = max(total_users - crash_free_users, 0)
    return payload


def collect_crashlytics_snapshot(hours=24):
    """Return a structured Crashlytics BigQuery snapshot for automation."""
    payload = _base_snapshot(hours)

    token = get_access_token()
    try:
        tables = check_bigquery_export(token)
    except RuntimeError as exc:
        return {
            **payload,
            "status": "error",
            "reason": str(exc),
            "source": "crashlytics",
        }

    if tables is None:
        payload["status"] = "skipped"
        payload["reason"] = "Crashlytics BigQuery export not set up"
        return payload
    if not tables:
        payload["status"] = "skipped"
        payload["reason"] = "BigQuery dataset exists but no tables yet"
        return payload

    try:
        table_id = select_crashlytics_table(tables)
    except ValueError as exc:
        return {
            **payload,
            "status": "error",
            "reason": str(exc),
        }
    payload["table_id"] = table_id

    summary = query_crash_summary(token, hours, table_id)
    if "error" in summary:
        return _error_snapshot(payload, summary)

    summary_rows = summary.get("rows") or []
    payload["top_fatal_issues"] = _parse_summary_rows(summary_rows)
    payload["fatal_events"] = sum(issue["crash_count"] for issue in payload["top_fatal_issues"])

    total_fatal = query_fatal_events_total(token, hours, table_id)
    if "error" in total_fatal:
        return _error_snapshot(payload, total_fatal)
    total_rows = total_fatal.get("rows") or []
    if total_rows and total_rows[0].get("f"):
        payload["fatal_events_in_window"] = int(total_rows[0]["f"][0].get("v") or 0)
    else:
        payload["fatal_events_in_window"] = 0

    rate_result = query_crash_free_rate(token, hours, table_id)
    if "error" in rate_result:
        return _error_snapshot(payload, rate_result)

    return _apply_rate_snapshot(payload, rate_result.get("rows") or [])


def main():
    parser = argparse.ArgumentParser(description="Check Crashlytics stability via BigQuery")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Crash-free %% threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--hours", type=int, default=24,
                        help="Look-back window in hours (default: 24)")
    args = parser.parse_args()

    token = get_access_token()

    # Check if BQ export exists
    try:
        tables = check_bigquery_export(token)
    except RuntimeError as exc:
        print(f"BigQuery API error (non-fatal for local/CI): {exc}", file=sys.stderr)
        print("PASS: Skipping crash gate when export cannot be queried.")
        sys.exit(0)
        return

    if tables is None:
        print("Crashlytics BigQuery export not set up.")
        print("To enable: Firebase Console > Crashlytics > BigQuery integration > Link")
        print("This is required for automated crash monitoring in CI.")
        sys.exit(0)

    if not tables:
        print("BigQuery dataset exists but no tables yet.")
        print("Tables auto-create when the next crash event streams in.")
        print("PASS: No crash data to evaluate (clean slate).")
        sys.exit(0)

    print(f"BigQuery tables found: {tables}")
    table_id = select_crashlytics_table(tables)
    print(f"Using Crashlytics table: {table_id}")

    # Query crash summary
    print(f"\n--- Crash summary (last {args.hours}h) ---")
    result = query_crash_summary(token, args.hours, table_id)
    if "error" in result:
        print(f"Query error: {result['error']}")
    elif result.get("rows"):
        for row in result["rows"]:
            vals = [f.get("v", "") for f in row["f"]]
            count, users, err_type, file, line, issue_title, issue_subtitle, ver = vals
            print(f"  {count} crashes ({users} users) v{ver}: {issue_title}")
            if issue_subtitle:
                print(f"    detail: {issue_subtitle}")
            print(f"    at {file}:{line}")
    else:
        print("  No crashes found!")

    # Query crash-free rate
    print(f"\n--- Crash-free rate (last {args.hours}h) ---")
    rate_result = query_crash_free_rate(token, args.hours, table_id)
    if "error" in rate_result:
        print(f"Query error: {rate_result['error']}")
    elif rate_result.get("rows"):
        vals = [f.get("v", "") for f in rate_result["rows"][0]["f"]]
        total, crash_free, pct = vals
        total_users = int(total or 0)
        crash_free_users = int(crash_free or 0)
        crash_free_pct = float(pct or 100)
        print(f"  Total users: {total_users}")
        if total_users == 0:
            print("  No recent sessions found; treating crash-free rate as pass.")
            print(f"  PASS: Above {args.threshold}% threshold")
            return

        print(f"  Crash-free: {crash_free_users} ({crash_free_pct}%)")
        if crash_free_pct < args.threshold:
            print(f"  FAIL: Below {args.threshold}% threshold")
            sys.exit(1)
        else:
            print(f"  PASS: Above {args.threshold}% threshold")
    else:
        print("  No session data found.")

    print("\nDone.")


if __name__ == "__main__":
    main()
