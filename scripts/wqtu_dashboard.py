#!/usr/bin/env python3
"""WQTU Dashboard — Weekly Qualified Training Users metric from PostHog.

WQTU is the product-value North Star Metric:
  Users with >= 3 `timer_completed` events in the trailing 7 days.

This script:
  1. Queries PostHog for WQTU (live-device users only)
  2. Queries supplementary health metrics (DAU, abandon rate, funnel)
  3. Writes marketing/data/wqtu_health.json
  4. Prints a human-readable summary
  5. Exits non-zero if WQTU drops below alert threshold

Usage:
  python scripts/wqtu_dashboard.py [--repo-root .] [--alert-threshold 0]
  # Requires: POSTHOG_PERSONAL_API_KEY (or POSTHOG_API_KEY) + POSTHOG_PROJECT_ID
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

# Reuse PostHog query helpers from existing infra
sys.path.append(str(Path(__file__).parent.resolve()))
from store_downloads_snapshot import LIVE_EVENTS_PREDICATE, posthog_query, query_rows, query_scalar


def _get_credentials():
    key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()
    return key, project_id


def compute_wqtu(key: str, project_id: str, errors: list) -> int:
    """WQTU = distinct users with >= 3 timer_completed in trailing 7 days (live only)."""
    result = posthog_query(
        f"""
        SELECT count() AS wqtu
        FROM (
            SELECT person_id, count() AS completions
            FROM events
            WHERE event = 'timer_completed'
              AND timestamp > now() - interval 7 day
              AND {LIVE_EVENTS_PREDICATE}
            GROUP BY person_id
            HAVING completions >= 3
        )
        """,
        key,
        project_id,
        errors,
    )
    if not result or not result.get("results"):
        return 0
    try:
        return int(result["results"][0][0] or 0)
    except (TypeError, ValueError, IndexError):
        return 0


def compute_abandon_rate(key: str, project_id: str, errors: list) -> dict:
    """30-day abandon rate: started vs completed."""
    started = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'timer_started'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    completed = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'timer_completed'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    rate = round((1 - completed / started) * 100, 1) if started > 0 else 0.0
    return {"started_30d": started, "completed_30d": completed, "abandon_rate_pct": rate}


def compute_monetization_funnel(key: str, project_id: str, errors: list) -> dict:
    """Paywall funnel: viewed -> attempted -> succeeded."""
    viewed = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'paywall_viewed'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    attempted = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'paywall_purchase_attempt'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    succeeded = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE (
            event = 'paywall_purchase_success'
            OR (event = 'paywall_purchase_result' AND lower(coalesce(toString(properties.success), '')) = 'true')
        )
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    conversion = round(succeeded / viewed * 100, 1) if viewed > 0 else 0.0
    return {
        "paywall_viewed_users": viewed,
        "purchase_attempted_users": attempted,
        "purchase_succeeded_users": succeeded,
        "conversion_pct": conversion,
    }


def compute_dau_wau(key: str, project_id: str, errors: list) -> dict:
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
    return {"dau": dau, "wau": wau}


def compute_wqtu_trend(key: str, project_id: str, errors: list) -> list:
    """WQTU per week for the last 4 weeks."""
    rows = query_rows(
        f"""
        SELECT week, count() AS wqtu
        FROM (
            SELECT
                toStartOfWeek(timestamp) AS week,
                person_id,
                count() AS completions
            FROM events
            WHERE event = 'timer_completed'
              AND timestamp > now() - interval 28 day
              AND {LIVE_EVENTS_PREDICATE}
            GROUP BY week, person_id
            HAVING completions >= 3
        )
        GROUP BY week
        ORDER BY week
        """,
        key,
        project_id,
        errors,
    )
    return [{"week_start": str(r[0]), "wqtu": int(r[1] or 0)} for r in rows]


def run(repo_root: Path, alert_threshold: int = 0) -> dict:
    output_path = repo_root / "marketing" / "data" / "wqtu_health.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    key, project_id = _get_credentials()

    if not key or not project_id:
        payload = {
            "generated_at": generated_at,
            "status": "skipped",
            "reason": "missing POSTHOG credentials",
            "wqtu": 0,
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    errors: list = []

    wqtu = compute_wqtu(key, project_id, errors)
    abandon = compute_abandon_rate(key, project_id, errors)
    funnel = compute_monetization_funnel(key, project_id, errors)
    engagement = compute_dau_wau(key, project_id, errors)
    trend = compute_wqtu_trend(key, project_id, errors)

    alert_fired = wqtu < alert_threshold
    status = "alert" if alert_fired else ("degraded" if errors else "ok")

    payload = {
        "generated_at": generated_at,
        "status": status,
        "nsm": {
            "wqtu": wqtu,
            "definition": "Users with >= 3 timer_completed in trailing 7 days",
            "alert_threshold": alert_threshold,
            "alert_fired": alert_fired,
        },
        "engagement": engagement,
        "abandon_rate": abandon,
        "monetization_funnel": funnel,
        "wqtu_trend": trend,
        "query_errors": errors,
    }

    # Load existing and append to history
    existing = {}
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    history = existing.get("history", []) if isinstance(existing, dict) else []
    history.append({"timestamp": generated_at, "wqtu": wqtu, "dau": engagement["dau"]})
    history = history[-90:]  # keep 90 data points
    payload["history"] = history

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Human-readable summary
    print("=" * 60)
    print("  WQTU HEALTH DASHBOARD")
    print("=" * 60)
    print(f"  WQTU (North Star):  {wqtu}")
    print(f"  DAU:                {engagement['dau']}")
    print(f"  WAU:                {engagement['wau']}")
    print(f"  Abandon Rate (30d): {abandon['abandon_rate_pct']}%")
    print(f"  Paywall Conversion: {funnel['conversion_pct']}%")
    if alert_fired:
        print(f"  ⚠️  ALERT: WQTU ({wqtu}) below threshold ({alert_threshold})")
    if errors:
        print(f"  ⚠️  Query errors: {len(errors)}")
    print(f"  Output: {output_path}")
    print("=" * 60)

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="WQTU Health Dashboard")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument(
        "--alert-threshold",
        type=int,
        default=0,
        help="WQTU threshold below which to fire alert (exit 1)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    result = run(Path(args.repo_root).resolve(), alert_threshold=args.alert_threshold)

    if args.json:
        print(json.dumps(result, indent=2))

    if result.get("status") == "alert":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
