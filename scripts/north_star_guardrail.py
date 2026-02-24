#!/usr/bin/env python3
"""Compute the North Star metric and enforce paid attribution guardrails.

North Star Metric (NSM):
  Weekly Qualified Training Users (WQTU) =
  distinct users with >= 3 timer_completed events in trailing 7 days.

Guardrail:
  If any paid campaign is marked active, paid-attributed users over trailing
  lookback must be > 0. This script can be run in enforce mode to fail CI.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

try:
    from scripts.store_downloads_snapshot import query_rows, query_scalar
except ModuleNotFoundError:
    from store_downloads_snapshot import query_rows, query_scalar


def _load_paid_campaigns(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"campaigns": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"campaigns": []}
    if not isinstance(payload, dict):
        return {"campaigns": []}
    return payload


def _active_campaigns(campaigns: Sequence[Dict[str, Any]], active_statuses: Set[str]) -> List[Dict[str, Any]]:
    active: List[Dict[str, Any]] = []
    for campaign in campaigns:
        status = str(campaign.get("status", "")).strip().lower()
        if status not in active_statuses:
            continue
        active.append(
            {
                "platform": campaign.get("platform", "unknown"),
                "status": campaign.get("status", ""),
                "daily_budget_usd": campaign.get("daily_budget_usd"),
                "launched_at": campaign.get("launched_at"),
            }
        )
    return active


def _parse_iso_utc(value: Any) -> Optional[dt.datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _campaign_outside_grace(campaign: Dict[str, Any], now: dt.datetime, grace_days: int) -> bool:
    launched = _parse_iso_utc(campaign.get("launched_at"))
    if launched is None:
        # Without launch timestamp, treat as mature campaign and enforce attribution hygiene.
        return True
    return launched <= now - dt.timedelta(days=max(0, grace_days))


def _load_apple_ads_live_metrics(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _apple_paid_traffic_signal(snapshot: Dict[str, Any]) -> Tuple[bool, str]:
    if not snapshot:
        return False, "apple snapshot missing"
    if str(snapshot.get("status", "")).strip().lower() != "ok":
        return False, f"apple snapshot status={snapshot.get('status') or 'unknown'}"
    metrics = snapshot.get("metrics_30d", {}) if isinstance(snapshot.get("metrics_30d"), dict) else {}
    taps = int(metrics.get("taps", 0) or 0)
    spend = float(metrics.get("spend_usd", 0.0) or 0.0)
    installs = int(metrics.get("installs", 0) or 0)
    has_signal = taps > 0 or spend > 0 or installs > 0
    detail = f"apple_30d taps={taps}, spend_usd={spend:.2f}, installs={installs}"
    return has_signal, detail


def _empty_payload(lookback_days: int, wqtu_window_days: int, reason: str = "") -> Dict[str, Any]:
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": "posthog",
        "status": "skipped" if reason else "ok",
        "status_reason": reason,
        "lookback_days": lookback_days,
        "wqtu_window_days": wqtu_window_days,
        "north_star": {
            "name": "Weekly Qualified Training Users",
            "key": "WQTU",
            "definition": "distinct users with >=3 timer_completed events in trailing 7 days",
            "wqtu_7d": 0,
            "timer_completed_7d": 0,
            "completed_users_7d": 0,
            "sessions_per_completed_user_7d": 0.0,
            "targets": {"checkpoint_2026_03_31": 8, "quarter_2026_06_30": 25},
            "on_track_checkpoint": False,
            "on_track_quarter": False,
        },
        "paid": {
            "paid_distinct_users_30d": 0,
            "paid_events_by_source_30d": [],
            "active_campaigns": [],
            "active_campaign_count": 0,
            "active_statuses": [],
            "campaign_grace_days": 7,
            "active_campaigns_outside_grace_count": 0,
            "paid_traffic_signal": False,
            "paid_traffic_signal_detail": "",
            "guardrail_violated": False,
            "guardrail_reason": "",
        },
        "query_diagnostics": {"errors": []},
        "snapshots": [],
    }


def run(
    repo_root: Path,
    lookback_days: int = 30,
    wqtu_window_days: int = 7,
    checkpoint_target: int = 8,
    quarter_target: int = 25,
    campaign_grace_days: int = 7,
    active_statuses: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    output_path = repo_root / "marketing" / "data" / "north_star.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()

    statuses = active_statuses or {"active", "running", "enabled", "live", "serving", "on"}
    errors: List[str] = []
    payload = _empty_payload(lookback_days, wqtu_window_days)
    payload["north_star"]["targets"] = {
        "checkpoint_2026_03_31": checkpoint_target,
        "quarter_2026_06_30": quarter_target,
    }
    payload["paid"]["active_statuses"] = sorted(statuses)

    paid_path = repo_root / "marketing" / "data" / "paid_campaigns.json"
    campaigns = _load_paid_campaigns(paid_path).get("campaigns", [])
    if not isinstance(campaigns, list):
        campaigns = []
    active = _active_campaigns(campaigns, statuses)
    payload["paid"]["active_campaigns"] = active
    payload["paid"]["active_campaign_count"] = len(active)
    payload["paid"]["campaign_grace_days"] = campaign_grace_days

    if not key or not project_id:
        payload["status"] = "skipped"
        payload["status_reason"] = "missing POSTHOG_PERSONAL_API_KEY/POSTHOG_API_KEY or POSTHOG_PROJECT_ID"
        payload["paid"]["guardrail_violated"] = len(active) > 0
        if len(active) > 0:
            payload["paid"]["guardrail_reason"] = "active campaigns exist but PostHog credentials are missing"
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {
            "status": payload["status"],
            "output": str(output_path),
            "reason": payload["status_reason"],
            "guardrail_violated": payload["paid"]["guardrail_violated"],
            "active_campaign_count": len(active),
        }

    wqtu = query_scalar(
        f"""
        SELECT count(*)
        FROM (
          SELECT person_id
          FROM events
          WHERE event = 'timer_completed'
            AND timestamp > now() - interval {wqtu_window_days} day
          GROUP BY person_id
          HAVING count() >= 3
        )
        """,
        key,
        project_id,
        errors,
    )
    completions_7d = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'timer_completed'
          AND timestamp > now() - interval {wqtu_window_days} day
        """,
        key,
        project_id,
        errors,
    )
    completed_users_7d = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'timer_completed'
          AND timestamp > now() - interval {wqtu_window_days} day
        """,
        key,
        project_id,
        errors,
    )
    paid_distinct_users_30d = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE timestamp > now() - interval {lookback_days} day
          AND (
            lower(coalesce(properties.utm_source,'')) IN ('apple_ads','google_ads','reddit','meta','tiktok')
            OR properties.utm_campaign IS NOT NULL
          )
        """,
        key,
        project_id,
        errors,
    )
    paid_events_rows = query_rows(
        f"""
        SELECT lower(coalesce(properties.utm_source,'(none)')) AS source,
               count() AS events,
               count(DISTINCT person_id) AS users
        FROM events
        WHERE timestamp > now() - interval {lookback_days} day
          AND (
            lower(coalesce(properties.utm_source,'')) IN ('apple_ads','google_ads','reddit','meta','tiktok')
            OR properties.utm_campaign IS NOT NULL
          )
        GROUP BY source
        ORDER BY events DESC
        """,
        key,
        project_id,
        errors,
    )

    sessions_per_user = 0.0
    if completed_users_7d > 0:
        sessions_per_user = round(completions_7d / completed_users_7d, 2)

    payload["status"] = "ok" if not errors else "degraded"
    payload["north_star"]["wqtu_7d"] = wqtu
    payload["north_star"]["timer_completed_7d"] = completions_7d
    payload["north_star"]["completed_users_7d"] = completed_users_7d
    payload["north_star"]["sessions_per_completed_user_7d"] = sessions_per_user
    payload["north_star"]["on_track_checkpoint"] = wqtu >= checkpoint_target
    payload["north_star"]["on_track_quarter"] = wqtu >= quarter_target

    payload["paid"]["paid_distinct_users_30d"] = paid_distinct_users_30d
    payload["paid"]["paid_events_by_source_30d"] = [
        {"source": str(row[0]), "events": int(row[1] or 0), "users": int(row[2] or 0)} for row in paid_events_rows
    ]
    now = dt.datetime.now(dt.timezone.utc)
    outside_grace = [c for c in active if _campaign_outside_grace(c, now, campaign_grace_days)]
    payload["paid"]["active_campaigns_outside_grace_count"] = len(outside_grace)

    has_apple_active = any(str(c.get("platform", "")).lower() == "apple_search_ads" for c in active)
    signal = False
    signal_detail = "no active paid campaigns"
    if has_apple_active:
        signal, signal_detail = _apple_paid_traffic_signal(
            _load_apple_ads_live_metrics(repo_root / "marketing" / "data" / "apple_ads_live_metrics.json")
        )
    payload["paid"]["paid_traffic_signal"] = signal
    payload["paid"]["paid_traffic_signal_detail"] = signal_detail

    should_enforce = (
        len(active) > 0
        and paid_distinct_users_30d == 0
        and (len(outside_grace) > 0 or signal)
    )
    payload["paid"]["guardrail_violated"] = should_enforce
    if should_enforce:
        payload["paid"]["guardrail_reason"] = (
            "active campaigns exist, paid-attributed users over lookback window is zero, "
            f"outside_grace={len(outside_grace)}, signal={signal} ({signal_detail})"
        )
    elif len(active) > 0 and paid_distinct_users_30d == 0:
        payload["paid"]["guardrail_reason"] = (
            "guardrail not enforced: campaigns are within grace window and no paid traffic signal detected"
        )

    payload["query_diagnostics"]["errors"] = errors

    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            snapshots = existing.get("snapshots", [])
            if isinstance(snapshots, list):
                payload["snapshots"] = snapshots
        except (json.JSONDecodeError, OSError):
            payload["snapshots"] = []

    payload["snapshots"].append(
        {
            "timestamp": payload["generated_at"],
            "wqtu_7d": wqtu,
            "timer_completed_7d": completions_7d,
            "completed_users_7d": completed_users_7d,
            "paid_distinct_users_30d": paid_distinct_users_30d,
            "active_campaign_count": len(active),
            "guardrail_violated": payload["paid"]["guardrail_violated"],
        }
    )
    payload["snapshots"] = payload["snapshots"][-120:]

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "status": payload["status"],
        "output": str(output_path),
        "wqtu_7d": wqtu,
        "timer_completed_7d": completions_7d,
        "completed_users_7d": completed_users_7d,
        "paid_distinct_users_30d": paid_distinct_users_30d,
        "active_campaign_count": len(active),
        "guardrail_violated": payload["paid"]["guardrail_violated"],
        "query_errors_count": len(errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute North Star metric and enforce paid attribution guardrail")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--lookback-days", type=int, default=30, help="Lookback window for paid attribution")
    parser.add_argument("--wqtu-window-days", type=int, default=7, help="Window for WQTU computation")
    parser.add_argument("--checkpoint-target", type=int, default=8, help="Checkpoint target for WQTU")
    parser.add_argument("--quarter-target", type=int, default=25, help="Quarter target for WQTU")
    parser.add_argument(
        "--campaign-grace-days",
        type=int,
        default=7,
        help="Days after campaign launch before zero paid attribution can fail guardrail",
    )
    parser.add_argument(
        "--active-statuses",
        default="active,running,enabled,live,serving,on",
        help="Comma-separated statuses treated as active campaigns",
    )
    parser.add_argument("--enforce-guardrail", action="store_true", help="Exit non-zero on guardrail violation")
    parser.add_argument(
        "--require-posthog",
        action="store_true",
        help="Exit non-zero if PostHog credentials are missing or queries degrade",
    )
    args = parser.parse_args()

    statuses = {s.strip().lower() for s in args.active_statuses.split(",") if s.strip()}
    result = run(
        Path(args.repo_root).resolve(),
        lookback_days=args.lookback_days,
        wqtu_window_days=args.wqtu_window_days,
        checkpoint_target=args.checkpoint_target,
        quarter_target=args.quarter_target,
        campaign_grace_days=args.campaign_grace_days,
        active_statuses=statuses,
    )
    print(json.dumps(result, indent=2))

    if args.require_posthog and result.get("status") != "ok":
        return 2
    if args.enforce_guardrail and result.get("guardrail_violated"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
