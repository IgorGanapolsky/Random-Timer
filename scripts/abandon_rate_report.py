#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

# Add scripts directory to path to import store_downloads_snapshot
sys.path.append(str(Path(__file__).parent.resolve()))

try:
    from store_downloads_snapshot import LIVE_EVENTS_PREDICATE, query_rows, query_scalar
except ImportError:
    print("Error: Could not import PostHog query helpers from store_downloads_snapshot.py")
    sys.exit(1)

def run():
    key = (
        os.getenv("POSTHOG_PERSONAL_API_KEY", "").strip()
        or os.getenv("POSTHOG_API_KEY", "").strip()
        or os.getenv("posthog_api_key", "").strip()
    )
    project_id = os.getenv("POSTHOG_PROJECT_ID", "").strip()

    if not key or not project_id:
        print("Error: Missing PostHog credentials.")
        return

    errors = []
    
    # 1. Abandon Rate (timer_started vs timer_completed) - Live audience only
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
    unique_users = query_scalar(
        f"""
        SELECT count(DISTINCT person_id)
        FROM events
        WHERE event = 'timer_started'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    
    abandon_rate = 0.0
    if started > 0:
        abandon_rate = ((started - completed) / started) * 100

    # 1b. Real abandon reasons from the timer_abandoned event
    abandon_reasons = query_rows(
        f"""
        SELECT
            coalesce(properties.abandon_reason, 'unknown') as reason,
            coalesce(properties.abandon_source, 'unknown') as source,
            count() as events,
            count(DISTINCT person_id) as users
        FROM events
        WHERE event = 'timer_abandoned'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY reason, source
        ORDER BY events DESC
        LIMIT 20
        """,
        key,
        project_id,
        errors,
    )
    total_abandoned_events = sum(row[2] for row in abandon_reasons) if abandon_reasons else 0

    # 1c. Onboarding funnel (first_open -> first_timer_configured -> first_timer_completed)
    first_open = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'first_open'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    first_configured = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'first_timer_configured'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    first_completed = query_scalar(
        f"""
        SELECT count(DISTINCT person_id) FROM events
        WHERE event = 'first_timer_completed'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )

    # 2. Most Used Parts (Screen Views) - Live audience only
    screens = query_rows(f"""
        SELECT properties.$screen_name as screen, count() as count
        FROM events
        WHERE event = '$screenview'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        GROUP BY screen
        ORDER BY count DESC
    """, key, project_id, errors)

    # 3. Top Events - Live audience only
    top_events = query_rows(f"""
        SELECT event, count() as count
        FROM events
        WHERE timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
          AND event NOT IN ('$feature_flag_called', '$groupidentify', '$identify', '$screenview', '$pageview')
        GROUP BY event
        ORDER BY count DESC
        LIMIT 10
    """, key, project_id, errors)

    # 4. Monetization funnel (live audience only)
    paywall_viewed = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_viewed'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    canonical_purchase_attempts = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_purchase_attempt'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    canonical_purchase_success = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_purchase_success'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )
    purchase_metrics_source = "canonical_events"
    paywall_purchase_attempts = canonical_purchase_attempts
    paywall_purchase_success = canonical_purchase_success
    if canonical_purchase_attempts == 0 and canonical_purchase_success == 0:
        purchase_metrics_source = "paywall_purchase_result_fallback"
        paywall_purchase_attempts = query_scalar(
            f"""
            SELECT count()
            FROM events
            WHERE event = 'paywall_purchase_result'
              AND timestamp > now() - interval 30 day
              AND {LIVE_EVENTS_PREDICATE}
            """,
            key,
            project_id,
            errors,
        )
        paywall_purchase_success = query_scalar(
            f"""
            SELECT count()
            FROM events
            WHERE event = 'paywall_purchase_result'
              AND (
                lower(coalesce(properties.result, '')) IN ('success', 'restored', 'already_unlocked')
                OR lower(toString(properties.success)) = 'true'
              )
              AND timestamp > now() - interval 30 day
              AND {LIVE_EVENTS_PREDICATE}
            """,
            key,
            project_id,
            errors,
        )
    paywall_restore_events = query_scalar(
        f"""
        SELECT count()
        FROM events
        WHERE event = 'paywall_restore_result'
          AND timestamp > now() - interval 30 day
          AND {LIVE_EVENTS_PREDICATE}
        """,
        key,
        project_id,
        errors,
    )

    # 5. Build segmentation sanity check (all events, last 30d)
    build_audience_breakdown = query_rows(
        """
        SELECT lower(coalesce(properties.build_audience, '(missing)')) AS build_audience, count() AS events
        FROM events
        WHERE timestamp > now() - interval 30 day
        GROUP BY build_audience
        ORDER BY events DESC
        """,
        key,
        project_id,
        errors,
    )

    report = {
        "abandon_metrics": {
            "timer_started_30d": started,
            "timer_completed_30d": completed,
            "unique_started_users_30d": unique_users,
            "inferred_abandon_rate_percent": round(abandon_rate, 2),
            "timer_abandoned_events_30d": total_abandoned_events,
            "abandon_reasons": [
                {"reason": row[0], "source": row[1], "events": row[2], "users": row[3]}
                for row in abandon_reasons
            ],
        },
        "onboarding_funnel_30d": {
            "first_open_users": first_open,
            "first_timer_configured_users": first_configured,
            "first_timer_completed_users": first_completed,
            "open_to_configured_pct": round((first_configured / first_open) * 100, 2) if first_open > 0 else 0.0,
            "configured_to_completed_pct": round((first_completed / first_configured) * 100, 2) if first_configured > 0 else 0.0,
            "open_to_completed_pct": round((first_completed / first_open) * 100, 2) if first_open > 0 else 0.0,
        },
        "monetization_metrics": {
            "paywall_viewed_30d": paywall_viewed,
            "paywall_purchase_attempts_30d": paywall_purchase_attempts,
            "paywall_purchase_success_30d": paywall_purchase_success,
            "paywall_restore_events_30d": paywall_restore_events,
            "paywall_purchase_metrics_source": purchase_metrics_source,
            "paywall_view_to_purchase_rate_percent": round((paywall_purchase_success / paywall_viewed) * 100, 2) if paywall_viewed > 0 else 0.0,
        },
        "build_audience_breakdown_30d": [{"build_audience": row[0], "events": row[1]} for row in build_audience_breakdown],
        "most_used_screens": [{"name": row[0], "count": row[1]} for row in screens if row[0]],
        "top_feature_events": [{"event": row[0], "count": row[1]} for row in top_events],
        "errors": errors
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run()
