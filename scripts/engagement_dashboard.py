#!/usr/bin/env python3
"""Full Engagement Dashboard — queries ALL PostHog events for complete user behavior picture.

Usage:
  python scripts/engagement_dashboard.py [--repo-root .] [--days 30]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Reuse PostHog query helpers from existing infra
sys.path.append(str(Path(__file__).parent.resolve()))
from store_downloads_snapshot import LIVE_EVENTS_PREDICATE, query_rows, query_scalar


LIVE = LIVE_EVENTS_PREDICATE


def _get_credentials():
    key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()
    return key, project_id


# ── Section 1: Onboarding Funnel ──────────────────────────────────────────


def compute_onboarding_funnel(key: str, project_id: str, days: int, errors: List[str]) -> Dict[str, int]:
    first_open = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'first_open'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    first_configured = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'first_timer_configured'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    first_completed = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'first_timer_completed'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    return {
        "first_open_users": first_open,
        "first_timer_configured_users": first_configured,
        "first_timer_completed_users": first_completed,
        "open_to_configured_pct": round(first_configured / first_open * 100, 1) if first_open > 0 else 0.0,
        "configured_to_completed_pct": round(first_completed / first_configured * 100, 1) if first_configured > 0 else 0.0,
    }


# ── Section 2: Timer Interaction Depth ─────────────────────────────────────


def compute_timer_interactions(key: str, project_id: str, days: int, errors: List[str]) -> List[Dict[str, Any]]:
    rows = query_rows(
        f"""
        SELECT event, count() as events, count(DISTINCT person_id) as users
        FROM events
        WHERE event IN (
            'timer_started','timer_paused','timer_resumed','timer_reset',
            'timer_stopped','timer_completed','timer_abandoned'
        )
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        GROUP BY event ORDER BY events DESC
        """,
        key, project_id, errors,
    )
    return [{"event": str(r[0]), "events": int(r[1] or 0), "users": int(r[2] or 0)} for r in rows]


# ── Section 3: Abandon Reasons ─────────────────────────────────────────────


def compute_abandon_reasons(key: str, project_id: str, days: int, errors: List[str]) -> List[Dict[str, Any]]:
    rows = query_rows(
        f"""
        SELECT
          coalesce(properties.abandon_reason, 'unknown') as reason,
          coalesce(properties.abandon_source, 'unknown') as source,
          count() as events,
          count(DISTINCT person_id) as users
        FROM events
        WHERE event = 'timer_abandoned'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        GROUP BY reason, source ORDER BY events DESC
        """,
        key, project_id, errors,
    )
    return [
        {"reason": str(r[0]), "source": str(r[1]), "events": int(r[2] or 0), "users": int(r[3] or 0)}
        for r in rows
    ]


# ── Section 4: Alarm Engagement ────────────────────────────────────────────


def compute_alarm_engagement(key: str, project_id: str, days: int, errors: List[str]) -> List[Dict[str, Any]]:
    rows = query_rows(
        f"""
        SELECT event, count() as events, count(DISTINCT person_id) as users
        FROM events
        WHERE event IN ('alarm_triggered', 'alarm_dismissed')
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        GROUP BY event
        """,
        key, project_id, errors,
    )
    return [{"event": str(r[0]), "events": int(r[1] or 0), "users": int(r[2] or 0)} for r in rows]


# ── Section 5: Paywall Funnel ──────────────────────────────────────────────


def compute_paywall_funnel(key: str, project_id: str, days: int, errors: List[str]) -> Dict[str, Any]:
    """Funnel uses paywall_viewed vs paywall_purchase_attempt vs success/dismiss.

    ``paywall_purchase_attempt`` = native purchase flow start (see
    ``docs/POSTHOG_ANALYTICS.md`` § Paywall funnel semantics), not generic CTA taps.
    """
    viewed = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'paywall_viewed'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    attempted = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'paywall_purchase_attempt'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    succeeded = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE (event = 'paywall_purchase_success'
          OR (event = 'paywall_purchase_result'
              AND lower(coalesce(toString(properties.success), '')) = 'true'))
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    dismissed = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'paywall_dismissed'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        """,
        key, project_id, errors,
    )
    return {
        "paywall_viewed_users": viewed,
        "purchase_attempted_users": attempted,
        "purchase_succeeded_users": succeeded,
        "paywall_dismissed_users": dismissed,
        "view_to_attempt_pct": round(attempted / viewed * 100, 1) if viewed > 0 else 0.0,
        "attempt_to_success_pct": round(succeeded / attempted * 100, 1) if attempted > 0 else 0.0,
    }


# ── Section 6: Review Prompt Funnel ────────────────────────────────────────


def compute_review_funnel(key: str, project_id: str, days: int, errors: List[str]) -> List[Dict[str, Any]]:
    rows = query_rows(
        f"""
        SELECT event, count() as events, count(DISTINCT person_id) as users
        FROM events
        WHERE event IN ('review_prompt_requested', 'write_review_tapped')
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        GROUP BY event
        """,
        key, project_id, errors,
    )
    return [{"event": str(r[0]), "events": int(r[1] or 0), "users": int(r[2] or 0)} for r in rows]


# ── Section 7: Settings Preferences ───────────────────────────────────────


def compute_settings_preferences(key: str, project_id: str, days: int, errors: List[str]) -> List[Dict[str, Any]]:
    rows = query_rows(
        f"""
        SELECT
          coalesce(properties.setting_name, properties.key, 'unknown') as setting,
          count() as changes,
          count(DISTINCT person_id) as users
        FROM events
        WHERE event = 'settings_changed'
          AND timestamp > now() - interval {days} day
          AND {LIVE}
        GROUP BY setting ORDER BY changes DESC
        LIMIT 20
        """,
        key, project_id, errors,
    )
    return [{"setting": str(r[0]), "changes": int(r[1] or 0), "users": int(r[2] or 0)} for r in rows]


# ── Section 8: DAU Trend ──────────────────────────────────────────────────


def compute_dau_trend(key: str, project_id: str, errors: List[str]) -> List[Dict[str, Any]]:
    rows = query_rows(
        f"""
        SELECT toDate(timestamp) as day, count(DISTINCT person_id) as dau
        FROM events
        WHERE event = 'Application Opened'
          AND timestamp > now() - interval 14 day
          AND {LIVE}
        GROUP BY day ORDER BY day
        """,
        key, project_id, errors,
    )
    return [{"day": str(r[0]), "dau": int(r[1] or 0)} for r in rows]


# ── Main run() ─────────────────────────────────────────────────────────────


def run(repo_root: Path, days: int = 30) -> Dict[str, Any]:
    output_path = repo_root / "marketing" / "data" / "engagement_dashboard.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    key, project_id = _get_credentials()

    if not key or not project_id:
        payload = {
            "generated_at": generated_at,
            "status": "skipped",
            "reason": "missing POSTHOG credentials",
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("Engagement Dashboard: SKIPPED (missing POSTHOG credentials)")
        return payload

    errors: List[str] = []

    onboarding = compute_onboarding_funnel(key, project_id, days, errors)
    timer_interactions = compute_timer_interactions(key, project_id, days, errors)
    abandon_reasons = compute_abandon_reasons(key, project_id, days, errors)
    alarm_engagement = compute_alarm_engagement(key, project_id, days, errors)
    paywall_funnel = compute_paywall_funnel(key, project_id, days, errors)
    review_funnel = compute_review_funnel(key, project_id, days, errors)
    settings_prefs = compute_settings_preferences(key, project_id, days, errors)
    dau_trend = compute_dau_trend(key, project_id, errors)

    status = "degraded" if errors else "ok"

    payload: Dict[str, Any] = {
        "generated_at": generated_at,
        "window_days": days,
        "status": status,
        "onboarding_funnel": onboarding,
        "timer_interactions": timer_interactions,
        "abandon_reasons": abandon_reasons,
        "alarm_engagement": alarm_engagement,
        "paywall_funnel": paywall_funnel,
        "review_funnel": review_funnel,
        "settings_preferences": settings_prefs,
        "dau_trend_14d": dau_trend,
        "query_errors": errors,
    }

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Human-readable summary
    print("=" * 64)
    print("  FULL ENGAGEMENT DASHBOARD")
    print("=" * 64)

    print("\n  -- Onboarding Funnel ({days}d) --".format(days=days))
    print(f"  first_open:             {onboarding['first_open_users']} users")
    print(f"  first_timer_configured: {onboarding['first_timer_configured_users']} users  ({onboarding['open_to_configured_pct']}%)")
    print(f"  first_timer_completed:  {onboarding['first_timer_completed_users']} users  ({onboarding['configured_to_completed_pct']}%)")

    print(f"\n  -- Timer Interactions ({days}d) --")
    for row in timer_interactions:
        print(f"  {row['event']:25s}  {row['events']:>6} events  {row['users']:>5} users")

    print(f"\n  -- Abandon Reasons ({days}d) --")
    if abandon_reasons:
        for row in abandon_reasons:
            print(f"  {row['reason']:20s} / {row['source']:15s}  {row['events']:>5} events  {row['users']:>4} users")
    else:
        print("  (none recorded)")

    print(f"\n  -- Alarm Engagement ({days}d) --")
    for row in alarm_engagement:
        print(f"  {row['event']:25s}  {row['events']:>6} events  {row['users']:>5} users")

    print(f"\n  -- Paywall Funnel ({days}d) --")
    pf = paywall_funnel
    print(f"  viewed:    {pf['paywall_viewed_users']} users")
    print(f"  attempted: {pf['purchase_attempted_users']} users  ({pf['view_to_attempt_pct']}% of viewed)")
    print(f"  succeeded: {pf['purchase_succeeded_users']} users  ({pf['attempt_to_success_pct']}% of attempted)")
    print(f"  dismissed: {pf['paywall_dismissed_users']} users")

    print(f"\n  -- Review Prompt Funnel ({days}d) --")
    for row in review_funnel:
        print(f"  {row['event']:30s}  {row['events']:>5} events  {row['users']:>4} users")
    if not review_funnel:
        print("  (none recorded)")

    print(f"\n  -- Settings Preferences ({days}d, top 20) --")
    for row in settings_prefs:
        print(f"  {row['setting']:30s}  {row['changes']:>5} changes  {row['users']:>4} users")
    if not settings_prefs:
        print("  (none recorded)")

    print("\n  -- DAU Trend (14d) --")
    for row in dau_trend:
        bar = "#" * min(row["dau"], 50)
        print(f"  {row['day']}  {row['dau']:>4}  {bar}")
    if not dau_trend:
        print("  (no data)")

    if errors:
        print(f"\n  Query errors: {len(errors)}")
        for e in errors:
            print(f"    - {e}")

    print(f"\n  Output: {output_path}")
    print("=" * 64)

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Full Engagement Dashboard from PostHog")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--days", type=int, default=30, help="Rolling lookback window (default 30)")
    args = parser.parse_args()

    run(Path(args.repo_root).resolve(), days=args.days)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
