#!/usr/bin/env python3
"""Generate store_downloads.json from live PostHog analytics.

This snapshot feeds wiki_sync.py so dashboard download/user sections stay populated.
When store console export data is unavailable, we use PostHog lifecycle events as
the source of truth for current growth reporting.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

LIVE_EVENTS_PREDICATE = """
(
  (
    lower(coalesce(properties.environment, '')) IN ('production', 'live')
    OR lower(coalesce(properties.build_audience, '')) = 'live'
  )
  AND lower(coalesce(properties.build_type, 'release')) != 'debug'
  AND lower(coalesce(properties.runtime_target, 'device')) NOT IN ('simulator', 'emulator')
)
"""


def _requests_module():
    try:
        import requests

        return requests
    except ImportError:
        return None


def posthog_query(query: str, api_key: str, project_id: str, errors: List[str]) -> Optional[Dict[str, Any]]:
    """Execute a HogQL query and return JSON payload."""
    requests = _requests_module()
    if requests is None:
        errors.append("missing_dependency: requests")
        return None

    try:
        response = requests.post(
            f"https://us.posthog.com/api/projects/{project_id}/query/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"query": {"kind": "HogQLQuery", "query": query}},
            timeout=30,
        )
    except requests.RequestException as exc:
        errors.append(f"request_error: {exc}")
        return None

    if response.status_code >= 300:
        errors.append(f"http_{response.status_code}")
        return None
    try:
        return response.json()
    except Exception as exc:
        errors.append(f"invalid_json: {exc}")
        return None


def query_scalar(query: str, api_key: str, project_id: str, errors: List[str]) -> int:
    result = posthog_query(query, api_key, project_id, errors)
    if not result or not result.get("results"):
        return 0
    row = result["results"][0]
    if not row:
        return 0
    try:
        return int(row[0] or 0)
    except (TypeError, ValueError):
        return 0


def query_rows(query: str, api_key: str, project_id: str, errors: List[str]) -> List[List[Any]]:
    result = posthog_query(query, api_key, project_id, errors)
    if not result:
        return []
    rows = result.get("results")
    if not isinstance(rows, list):
        return []
    return rows


def _empty_snapshot(window_days: int, reason: str = "") -> Dict[str, Any]:
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "window_days": window_days,
        "source": "posthog",
        "status": "skipped" if reason else "ok",
        "status_reason": reason,
        "ios": {"downloads_30d": 0},
        "android": {"downloads_30d": 0, "active_installs": 0},
        "combined": {"downloads_30d": 0},
        "active_users": {"dau": 0, "wau": 0, "mau": 0},
        "query_diagnostics": {"errors": []},
        "snapshots": [],
    }


def run(repo_root: Path, days: int = 30) -> Dict[str, Any]:
    output_path = repo_root / "marketing" / "data" / "store_downloads.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()

    errors: List[str] = []
    payload = _empty_snapshot(days)

    if not key or not project_id:
        payload["status"] = "skipped"
        payload["status_reason"] = "missing POSTHOG_PERSONAL_API_KEY/POSTHOG_API_KEY or POSTHOG_PROJECT_ID"
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {"status": "skipped", "output": str(output_path), "reason": payload["status_reason"]}

    installs_by_os = query_rows(
        f"""
        SELECT coalesce(properties.$os, properties.$os_name, 'Unknown') AS os, count(DISTINCT person_id) AS users
        FROM events
        WHERE event = 'Application Installed'
          AND timestamp > now() - interval {days} day
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY os
        ORDER BY users DESC
        """,
        key,
        project_id,
        errors,
    )

    ios_downloads = 0
    android_downloads = 0
    for row in installs_by_os:
        os_name = str(row[0] or "").lower()
        users = int(row[1] or 0)
        if "ios" in os_name:
            ios_downloads += users
        elif "android" in os_name:
            android_downloads += users

    android_active_installs = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'Application Opened'
          AND (properties.$os = 'Android' OR properties.$os_name = 'Android')
          AND timestamp > now() - interval {days} day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )

    dau = query_scalar(
        """
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'Application Opened'
          AND timestamp > now() - interval 1 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    wau = query_scalar(
        """
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'Application Opened'
          AND timestamp > now() - interval 7 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    mau = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'Application Opened'
          AND timestamp > now() - interval {days} day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "window_days": days,
        "source": "posthog",
        "status": "ok" if not errors else "degraded",
        "status_reason": "",
        "ios": {"downloads_30d": ios_downloads},
        "android": {
            "downloads_30d": android_downloads,
            "active_installs": android_active_installs,
        },
        "combined": {"downloads_30d": ios_downloads + android_downloads},
        "active_users": {"dau": dau, "wau": wau, "mau": mau},
        "query_diagnostics": {"errors": errors},
        "snapshots": [],
    }

    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            snapshots = existing.get("snapshots", [])
            if isinstance(snapshots, list):
                payload["snapshots"] = snapshots
        except (json.JSONDecodeError, OSError):
            pass

    snapshot = {
        "timestamp": payload["generated_at"],
        "ios_downloads_30d": ios_downloads,
        "android_downloads_30d": android_downloads,
        "combined_downloads_30d": ios_downloads + android_downloads,
        "android_active_installs": android_active_installs,
        "dau": dau,
        "wau": wau,
        "mau": mau,
    }
    payload["snapshots"].append(snapshot)
    payload["snapshots"] = payload["snapshots"][-90:]

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "status": payload["status"],
        "output": str(output_path),
        "ios_downloads_30d": ios_downloads,
        "android_downloads_30d": android_downloads,
        "combined_downloads_30d": ios_downloads + android_downloads,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "query_errors_count": len(errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate store downloads snapshot from PostHog")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--days", type=int, default=30, help="Rolling lookback window")
    args = parser.parse_args()

    result = run(Path(args.repo_root).resolve(), days=args.days)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
