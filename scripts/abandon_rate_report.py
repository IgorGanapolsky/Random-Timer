#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

# Add scripts directory to path to import store_downloads_snapshot
sys.path.append(str(Path(__file__).parent.resolve()))

try:
    from store_downloads_snapshot import posthog_query, query_scalar, query_rows
except ImportError:
    print("Error: Could not import posthog_query from store_downloads_snapshot.py")
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
    
    # 1. Abandon Rate (timer_started vs timer_completed) - Production Only
    started = query_scalar("SELECT count() FROM events WHERE event = 'timer_started' AND properties.environment = 'production' AND timestamp > now() - interval 30 day", key, project_id, errors)
    completed = query_scalar("SELECT count() FROM events WHERE event = 'timer_completed' AND properties.environment = 'production' AND timestamp > now() - interval 30 day", key, project_id, errors)
    unique_users = query_scalar("SELECT count(DISTINCT person_id) FROM events WHERE event = 'timer_started' AND properties.environment = 'production' AND timestamp > now() - interval 30 day", key, project_id, errors)
    
    abandon_rate = 0.0
    if started > 0:
        abandon_rate = ((started - completed) / started) * 100

    # 2. Most Used Parts (Screen Views) - Production Only
    screens = query_rows("""
        SELECT properties.$screen_name as screen, count() as count
        FROM events
        WHERE event = '$screenview' AND properties.environment = 'production' AND timestamp > now() - interval 30 day
        GROUP BY screen
        ORDER BY count DESC
    """, key, project_id, errors)

    # 3. Top Events - Production Only
    top_events = query_rows("""
        SELECT event, count() as count
        FROM events
        WHERE properties.environment = 'production' AND timestamp > now() - interval 30 day
          AND event NOT IN ('$feature_flag_called', '$groupidentify', '$identify', '$screenview', '$pageview')
        GROUP BY event
        ORDER BY count DESC
        LIMIT 10
    """, key, project_id, errors)

    report = {
        "abandon_metrics": {
            "timer_started_30d": started,
            "timer_completed_30d": completed,
            "unique_started_users_30d": unique_users,
            "abandon_rate_percent": round(abandon_rate, 2)
        },
        "most_used_screens": [{"name": row[0], "count": row[1]} for row in screens if row[0]],
        "top_feature_events": [{"event": row[0], "count": row[1]} for row in top_events],
        "errors": errors
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run()
