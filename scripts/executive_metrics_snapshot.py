#!/usr/bin/env python3
"""Single executive snapshot: PostHog (product) + store APIs + Crashlytics (BigQuery).

Outputs marketing/data/executive_metrics.json. Intended to run locally (.env) or in CI
(GitHub Actions secrets). No secrets are printed.

Audience (PostHog): PRAGMATIC_LIVE — non-debug, real device, not is_internal=true.
See docs/OBSERVABILITY.md for strict LIVE_EVENTS_PREDICATE vs legacy events.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from repo_dotenv import load_repo_dotenv

PRAGMATIC_LIVE = """(
  lower(coalesce(properties.build_type, 'release')) != 'debug'
  AND lower(coalesce(properties.runtime_target, 'device')) NOT IN ('simulator', 'emulator')
  AND coalesce(toString(properties.is_internal), 'false') != 'true'
)"""


def _posthog_credentials() -> tuple[str, str]:
    key = (
        os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.environ.get("POSTHOG_API_KEY", "").strip()
        or os.environ.get("posthog_api_key", "").strip()
    )
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "").strip()
    return key, project_id


def _posthog_section(project_id: str, api_key: str, days: int) -> Dict[str, Any]:
    from store_downloads_snapshot import posthog_query

    errors: List[str] = []
    win = f"{days} day"
    f = PRAGMATIC_LIVE
    out: Dict[str, Any] = {
        "status": "ok" if api_key and project_id else "skipped",
        "host": "https://us.posthog.com",
        "project_id": project_id or None,
        "audience": "pragmatic_live",
        "audience_sql": PRAGMATIC_LIVE.strip(),
        "window_days": days,
        "errors": errors,
    }
    if not api_key or not project_id:
        out["reason"] = "missing POSTHOG_PERSONAL_API_KEY or POSTHOG_PROJECT_ID"
        return out

    def scalar(sql: str) -> Optional[int]:
        data = posthog_query(sql, api_key, project_id, errors)
        if not data or not data.get("results"):
            return None
        row = data["results"][0]
        if not row:
            return None
        try:
            return int(row[0] or 0)
        except (TypeError, ValueError):
            return None

    out["distinct_persons_application_installed"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'Application Installed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_first_open"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'first_open' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    started = scalar(
        f"SELECT count() FROM events WHERE event = 'timer_started' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    completed = scalar(
        f"SELECT count() FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["timer_started_events"] = started
    out["timer_completed_events"] = completed
    out["distinct_persons_timer_started"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_started' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_timer_completed"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["distinct_persons_timer_started_and_completed"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"AND person_id IN ("
        f"SELECT person_id FROM events WHERE event = 'timer_started' "
        f"AND timestamp > now() - interval {win} AND {f}"
        f")"
    )
    out["wqtu_distinct_persons"] = scalar(
        f"SELECT count() FROM ("
        f"SELECT person_id FROM events WHERE event = 'timer_completed' "
        f"AND timestamp > now() - interval {win} AND {f} "
        f"GROUP BY person_id HAVING count() >= 3"
        f")"
    )
    if started and started > 0 and completed is not None:
        out["timer_abandon_rate_event_level_pct"] = round(
            (started - completed) / started * 100, 2
        )
    out["distinct_persons_paywall_purchase_success"] = scalar(
        f"SELECT count(DISTINCT person_id) FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["events_paywall_purchase_success"] = scalar(
        f"SELECT count() FROM events WHERE event = 'paywall_purchase_success' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    q_reviews = posthog_query(
        f"SELECT count(), count(DISTINCT person_id) FROM events WHERE event = 'review_prompt_requested' "
        f"AND timestamp > now() - interval {win} AND {f}",
        api_key,
        project_id,
        errors,
    )
    if q_reviews and q_reviews.get("results"):
        r0 = q_reviews["results"][0]
        if r0 and len(r0) >= 2:
            out["in_app_review_prompt_events"] = int(r0[0] or 0)
            out["in_app_review_prompt_distinct_persons"] = int(r0[1] or 0)

    q_screen = posthog_query(
        f"""
        SELECT coalesce(toString(properties.`$screen_name`), toString(properties.screen_name), '(unnamed)'),
               count(DISTINCT person_id), count()
        FROM events WHERE event = '$screen' AND timestamp > now() - interval {win} AND {f}
        GROUP BY 1 ORDER BY 2 DESC LIMIT 12
        """,
        api_key,
        project_id,
        errors,
    )
    out["top_screens_by_distinct_persons"] = (q_screen or {}).get("results") or []

    q_exc = scalar(
        f"SELECT count() FROM events WHERE event = '$exception' "
        f"AND timestamp > now() - interval {win} AND {f}"
    )
    out["posthog_exception_events"] = q_exc
    if errors:
        out["query_errors"] = errors[:20]
    return out


def run(
    repo_root: Path,
    days: int = 30,
    crashlytics_hours: int = 168,
    load_dotenv: bool = True,
) -> Dict[str, Any]:
    if load_dotenv:
        load_repo_dotenv(repo_root)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    ph_key, ph_proj = _posthog_credentials()
    posthog = _posthog_section(ph_proj, ph_key, days)

    try:
        from real_store_downloads import _get_android_data, _get_ios_data
    except Exception as exc:
        android = {"status": "error", "reason": f"import real_store_downloads: {exc}"}
        ios = {"status": "error", "reason": f"import real_store_downloads: {exc}"}
    else:
        try:
            android = _get_android_data(days)
        except Exception as exc:
            android = {"status": "error", "reason": str(exc)}
        try:
            ios = _get_ios_data(days)
        except Exception as exc:
            ios = {"status": "error", "reason": str(exc)}

    try:
        from check_crashlytics import collect_crashlytics_snapshot

        crashlytics = collect_crashlytics_snapshot(hours=crashlytics_hours)
    except Exception as exc:
        crashlytics = {"status": "error", "reason": str(exc), "source": "crashlytics"}

    payload: Dict[str, Any] = {
        "generated_at": generated_at,
        "source": "executive_metrics_snapshot",
        "definitions": {
            "install_proxy_posthog": "Distinct persons with event Application Installed (not store units).",
            "reviews_store": "From Play/App Store APIs in store section (sample/pagination limits apply).",
            "reviews_in_app": "PostHog review_prompt_requested / write_review_tapped (not published star count).",
            "paid_posthog": "paywall_purchase_success and paywall_purchase_result in PostHog; use Store/RevenueCat for ledger truth.",
            "crashes": "Crashlytics via BigQuery export; PostHog $exception also listed if captured.",
            "uninstalls": "Not available on iOS; Android uninstall metrics require Play reporting APIs (not in this script yet).",
            "wqtu": "Distinct persons with >=3 timer_completed events in the same window (North Star proxy for that window).",
            "started_and_completed_persons": "Distinct persons with at least one timer_completed in-window who also have at least one timer_started in-window.",
        },
        "posthog": posthog,
        "store_apis": {"android": android, "ios": ios},
        "crashlytics_bigquery": crashlytics,
    }

    out_path = repo_root / "marketing" / "data" / "executive_metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Executive metrics snapshot (PostHog + stores + Crashlytics)")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--days", type=int, default=30, help="PostHog window days")
    parser.add_argument(
        "--crashlytics-hours",
        type=int,
        default=168,
        help="Crashlytics BigQuery lookback (default 7d)",
    )
    parser.add_argument("--no-dotenv", action="store_true", help="Skip loading .env from repo root")
    parser.add_argument("--json-stdout", action="store_true", help="Print full JSON to stdout")
    args = parser.parse_args()

    payload = run(
        args.repo_root.resolve(),
        days=args.days,
        crashlytics_hours=args.crashlytics_hours,
        load_dotenv=not args.no_dotenv,
    )
    out_path = args.repo_root.resolve() / "marketing" / "data" / "executive_metrics.json"
    print("=" * 60)
    print("  EXECUTIVE METRICS SNAPSHOT")
    print("=" * 60)
    print(f"  Written: {out_path}")
    ph = payload.get("posthog") or {}
    print(f"  PostHog: {ph.get('status')}  installs(persons)={ph.get('distinct_persons_application_installed')}")
    if ph.get("status") == "ok":
        print(
            f"    timer: started(events)={ph.get('timer_started_events')} "
            f"completed(events)={ph.get('timer_completed_events')} "
            f"distinct_started={ph.get('distinct_persons_timer_started')} "
            f"distinct_completed={ph.get('distinct_persons_timer_completed')} "
            f"starters_who_completed={ph.get('distinct_persons_timer_started_and_completed')} "
            f"wqtu_window={ph.get('wqtu_distinct_persons')}"
        )
    st = payload.get("store_apis") or {}
    print(f"  Android API: {(st.get('android') or {}).get('status')}")
    print(f"  iOS API: {(st.get('ios') or {}).get('status')}")
    cr = payload.get("crashlytics_bigquery") or {}
    print(f"  Crashlytics BQ: {cr.get('status')} fatal_events={cr.get('fatal_crash_events')}")
    print("=" * 60)
    if args.json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
