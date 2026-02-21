# ASO Keyword Rotation

Weekly automated keyword optimization for iOS App Store and Google Play Store.

## Current iOS Keywords

From `native-ios/fastlane/metadata/en-US/keywords.txt` (100-char limit):

```
reaction,interval,hiit,tabata,boxing,martial arts,drills,focus,sparring,workout,coach,random,timer
```

## How Rotation Works

1. **Sunday**: `attribution_feedback.py` writes real install data to `marketing/keywords/posthog_feedback.json`
2. **Monday**: `aso_keyword_rotation.py` runs:
   - Loads current keywords + BID-score backlog from `growth_keyword_engine.py`
   - Evaluates each keyword: keeps **performing** (rank < target), flags **underperforming**
   - Selects top BID-score replacements not in current set
   - Writes new `keywords.txt` (respects 100-char iOS limit)
   - Generates Play Store title A/B variants (50-char limit)
   - Logs rotation to `marketing/keywords/rotation_history.json`

## BID Score Formula

```python
bid_score = (intent_weight * 30) + (business_relevance * 25)
            + ((100 - keyword_difficulty) * 0.2) - (ai_trap_penalty * 15)
            + (tool_intent_bonus * 10)
```

| Intent Type | Weight | Example |
|-------------|--------|---------|
| `tool` | 1.0 | "reaction timer app" |
| `commercial` | 0.8 | "best hiit timer" |
| `mixed` | 0.5 | "boxing drill timer" |
| `informational` | 0.2 | "what is tabata" |

## Seed Keywords (10) × Modifiers (10)

**Seeds:** reaction training, interval timer, tactical timer, random timer, focus drills, combat conditioning, boxing drills, home workout timer, sparring prep, mental readiness

**Modifiers:** best, vs, under 20, review, calculator, checker, generator, template, app, for beginners

→ 110 keyword combinations scored and ranked.

## Source Files

- `scripts/aso_keyword_rotation.py` — Rotation logic
- `scripts/growth_keyword_engine.py` — BID scoring engine
- `marketing/keywords/strategy.json` — Seed config
- `marketing/keywords/rotation_history.json` — Rotation log
- `.github/workflows/weekly-aso-rotation.yml` — Monday 10:00 UTC
