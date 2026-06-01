# Paywall Conversion Report

Generated: 2026-06-01T17:40:24+00:00
Window (days): 30

## Funnel
- Views: **548**
- Offer Selects: **55**
- Purchase Attempts: **4**
- Purchase Successes: **0**
- View -> Offer Select: **10.0%**
- Select -> Purchase Attempt: **7.3%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 405 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 405 | 176 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical_monthly | 40 | 1 | 0 | 2.5% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 489 | 177 |
| android | elite_tactical | 397 | 170 |
| android | pro_base | 239 | 146 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 259 | 1 | 0 | 0.4% | 0.0% |
| voice_gate | 172 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 39 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| sound_gate | 5 | 1 | 0 | 20.0% | 0.0% |
| qualified_training_gate | 5 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **172** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **39** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3350 | 337 |
| alarm_duration | 2705 | 309 |
| min_seconds | 2384 | 313 |
| volume | 2325 | 211 |
| sound_type | 1796 | 263 |
| unknown | 1589 | 22 |
| repeat_enabled | 1307 | 307 |
| voice_callouts_enabled | 791 | 187 |
| vibration_enabled | 593 | 214 |
| repeat_rounds | 396 | 116 |
| voice_gender | 352 | 218 |
| use_extended_range | 253 | 157 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
