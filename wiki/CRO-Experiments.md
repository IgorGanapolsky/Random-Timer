# CRO Experiments

Conversion Rate Optimization through A/B testing of store listing elements.

## Active Experiments

_Auto-updated from `marketing/data/cro_experiments.json`._

### 1. Title A/B Test (Play Store)

**Status:** Proposed | **Duration:** 14 days | **Metric:** conversion_rate

| Variant | Title |
|---------|-------|
| A (control) | Random Tactical Timer |
| B | Reaction Timer — Random HIIT Drill |
| C | Random Timer for Boxing & HIIT |
| D | Tactical Drill Timer — Unpredictable |

### 2. Short Description A/B Test

**Status:** Proposed | **Duration:** 14 days | **Metric:** conversion_rate

| Variant | Description |
|---------|------------|
| A (control) | Random timer for HIIT, drills & party games. Set a range — boom. |
| B | Unpredictable interval timer for reaction training and tactical drills. |
| C | Set a random countdown — perfect for boxing rounds, HIIT, and focus drills. |

### 3. Screenshot Order A/B Test

**Status:** Proposed | **Duration:** 21 days | **Metric:** conversion_rate

| Variant | First 3 Screenshots |
|---------|-------------------|
| A (control) | Setup → Active → Settings |
| B | Active → Setup → Loop |
| C | Setup (HIIT use case) → Active → Settings |

## Localization Status

| Locale | Language | Android | iOS |
|--------|----------|:---:|:---:|
| en-US | English | ✅ | ✅ |
| ja | Japanese | ✅ | ✅ |
| de-DE | German | ✅ | ✅ |
| ko | Korean | ✅ | ✅ |
| pt-BR | Portuguese | ✅ | ✅ |

## Source Files

- `scripts/cro_optimization.py` — Experiment generation + localization
- `marketing/data/cro_experiments.json` — Experiment data
- `marketing/data/localization_status.json` — Locale completion
- `.github/workflows/weekly-cro-optimization.yml` — Tuesday 11:00 UTC
