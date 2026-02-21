# Review Velocity

Tracks app store review submission rates and dynamically tunes in-app review prompt timing.

## How It Works

1. **Wednesday 09:00 UTC**: `review_velocity_tracker.py` runs
2. Reads `marketing/data/asc_reviews_cache.json` for iOS review counts
3. Computes rolling 7-day velocity (reviews/day)
4. Detects velocity drops (threshold: -20%)
5. Adjusts review prompt config based on velocity trend
6. Saves snapshot to `marketing/data/review_velocity.json` (90-snapshot rolling window)

## Prompt Tuning Logic

| Velocity Trend | `completions_before_prompt` | `min_days_between_prompts` |
|---------------|:---:|:---:|
| Rising / stable | 3 | 30 |
| Slight drop | 2 | 21 |
| Significant drop | 2 | 21 |
| Very low | 5 | 45 |

Additional flags:
- `prompt_after_positive_experience`: `true` — Only prompt after successful timer completion
- `suppress_during_low_rating_period`: `true` — Pause prompts if rating drops

## In-App Integration

Both platforms use `StoreReviewManager` with the same gate logic:
- Minimum **3 timer completions** before first prompt
- Minimum **30 days** between prompts (tunable)
- **Version-aware**: resets per app version
- Fires `review_prompt_requested` and `write_review_tapped` PostHog events

## Data Format

```json
{
  "snapshots": [
    {
      "timestamp": "2026-02-20T...",
      "ios_total": 0, "ios_rating": 0,
      "ios_recent_7d": 0,
      "android_total": 0, "android_rating": 0,
      "android_recent_7d": 0
    }
  ],
  "alerts": [],
  "latest_velocity": {
    "ios_velocity": 0.0,
    "android_velocity": 0.0
  },
  "review_prompt_config": {
    "completions_before_prompt": 3,
    "min_days_between_prompts": 30,
    "prompt_after_positive_experience": true,
    "suppress_during_low_rating_period": true
  }
}
```

## Source Files

- `scripts/review_velocity_tracker.py` — Velocity computation + prompt tuning
- `native-android/.../review/StoreReviewManager.kt` — Android prompt gate
- `native-ios/.../Services/StoreReviewManager.swift` — iOS prompt gate
- `.github/workflows/weekly-review-velocity.yml` — Wednesday 09:00 UTC
