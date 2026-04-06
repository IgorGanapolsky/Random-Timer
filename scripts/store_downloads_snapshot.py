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
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_POSTHOG_RETRYABLE_STATUS = frozenset({429, 502, 503, 504})

LIVE_EVENTS_PREDICATE = """
(
  (
    lower(coalesce(properties.environment, '')) IN ('production', 'live')
    OR lower(coalesce(properties.build_audience, '')) = 'live'
  )
  AND lower(coalesce(properties.build_type, 'release')) != 'debug'
  AND lower(coalesce(properties.runtime_target, 'device')) NOT IN ('simulator', 'emulator')
  AND coalesce(toString(properties.is_internal), 'false') != 'true'
)
"""


def _requests_module():
    try:
        import requests

        return requests
    except ImportError:
        return None


def _posthog_backoff(attempt: int) -> None:
    time.sleep(min(8.0, 2.0**attempt))


def _posthog_execute_once(
    requests: Any,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], bool]:
    """POST once; returns (json_body, error_message, should_retry)."""
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        return None, f"request_error: {exc}", True

    if response.status_code >= 300:
        code = response.status_code
        return None, f"http_{code}", code in _POSTHOG_RETRYABLE_STATUS

    try:
        return response.json(), None, False
    except Exception as exc:
        return None, f"invalid_json: {exc}", True


def posthog_query(
    query: str,
    api_key: str,
    project_id: str,
    errors: List[str],
    *,
    timeout: float = 90.0,
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Execute a HogQL query and return JSON payload.

    Retries on transient PostHog/network failures (504s, timeouts) with backoff.
    """
    requests = _requests_module()
    if requests is None:
        errors.append("missing_dependency: requests")
        return None

    url = f"https://us.posthog.com/api/projects/{project_id}/query/"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"query": {"kind": "HogQLQuery", "query": query}}

    for attempt in range(max_retries):
        data, err, should_retry = _posthog_execute_once(requests, url, headers, payload, timeout)
        if data is not None:
            return data

        final_attempt = attempt >= max_retries - 1
        if final_attempt or not should_retry:
            if err:
                errors.append(err)
            return None

        _posthog_backoff(attempt)

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


def _load_existing_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _metric_definitions() -> Dict[str, Any]:
    return {
        "downloads_30d": {
            "display_name": "Distinct install users (30d)",
            "source": "posthog",
            "semantic_type": "proxy",
            "description": (
                "Distinct live-device users with an 'Application Installed' event over the trailing window. "
                "This is a PostHog proxy metric, not store download truth."
            ),
        }
    }


def _data_quality(
    *,
    generated_at: str,
    status: str,
    errors: List[str],
    preserved_previous_metrics: bool,
    last_good_generated_at: str = "",
) -> Dict[str, Any]:
    is_stale = status in {"degraded", "skipped"} and preserved_previous_metrics
    return {
        "is_stale": is_stale,
        "preserved_previous_metrics": preserved_previous_metrics,
        "last_attempt_generated_at": generated_at,
        "last_good_generated_at": last_good_generated_at,
        "reason": errors[-1] if errors else "",
    }


def _preserve_previous_metrics(
    existing: Dict[str, Any],
    *,
    generated_at: str,
    status: str,
    reason: str,
    errors: List[str],
) -> Optional[Dict[str, Any]]:
    if not existing:
        return None
    payload = dict(existing)
    payload["generated_at"] = generated_at
    payload["status"] = status
    payload["status_reason"] = reason
    payload["metric_definitions"] = _metric_definitions()
    payload["query_diagnostics"] = {"errors": errors}
    payload["data_quality"] = _data_quality(
        generated_at=generated_at,
        status=status,
        errors=errors,
        preserved_previous_metrics=True,
        last_good_generated_at=str(existing.get("generated_at", "")),
    )
    return payload


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
        "metric_definitions": _metric_definitions(),
        "data_quality": {
            "is_stale": False,
            "preserved_previous_metrics": False,
            "last_attempt_generated_at": "",
            "last_good_generated_at": "",
            "reason": "",
        },
        "query_diagnostics": {"errors": []},
        "snapshots": [],
    }


def run(repo_root: Path, days: int = 30) -> Dict[str, Any]:
    output_path = repo_root / "marketing" / "data" / "store_downloads.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_existing_payload(output_path)
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()

    errors: List[str] = []
    payload = _empty_snapshot(days)

    if not key or not project_id:
        payload["generated_at"] = generated_at
        payload["status"] = "skipped"
        payload["status_reason"] = "missing POSTHOG_PERSONAL_API_KEY/POSTHOG_API_KEY or POSTHOG_PROJECT_ID"
        preserved = _preserve_previous_metrics(
            existing,
            generated_at=generated_at,
            status="skipped",
            reason=payload["status_reason"],
            errors=[],
        )
        if preserved is not None:
            output_path.write_text(json.dumps(preserved, indent=2) + "\n", encoding="utf-8")
            return {
                "status": "skipped",
                "output": str(output_path),
                "reason": payload["status_reason"],
                "preserved_previous_metrics": True,
            }
        payload["data_quality"] = _data_quality(
            generated_at=generated_at,
            status="skipped",
            errors=[],
            preserved_previous_metrics=False,
        )
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
        f"""
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
        f"""
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

    if errors:
        preserved = _preserve_previous_metrics(
            existing,
            generated_at=generated_at,
            status="degraded",
            reason="preserved last good metrics after degraded PostHog query",
            errors=errors,
        )
        if preserved is not None:
            output_path.write_text(json.dumps(preserved, indent=2) + "\n", encoding="utf-8")
            return {
                "status": "degraded",
                "output": str(output_path),
                "ios_downloads_30d": int(preserved.get("ios", {}).get("downloads_30d", 0) or 0),
                "android_downloads_30d": int(preserved.get("android", {}).get("downloads_30d", 0) or 0),
                "combined_downloads_30d": int(preserved.get("combined", {}).get("downloads_30d", 0) or 0),
                "dau": int(preserved.get("active_users", {}).get("dau", 0) or 0),
                "wau": int(preserved.get("active_users", {}).get("wau", 0) or 0),
                "mau": int(preserved.get("active_users", {}).get("mau", 0) or 0),
                "query_errors_count": len(errors),
                "preserved_previous_metrics": True,
            }

    payload = {
        "generated_at": generated_at,
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
        "metric_definitions": _metric_definitions(),
        "data_quality": _data_quality(
            generated_at=generated_at,
            status="ok" if not errors else "degraded",
            errors=errors,
            preserved_previous_metrics=False,
        ),
        "query_diagnostics": {"errors": errors},
        "snapshots": [],
    }

    snapshots = existing.get("snapshots", [])
    if isinstance(snapshots, list):
        payload["snapshots"] = snapshots

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
    if not errors:
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
