# Paywall Conversion Report

Generated: 2026-06-04T13:26:06+00:00
Window (days): 30

## Funnel
- Views: **677**
- Offer Selects: **54**
- Purchase Attempts: **4**
- Purchase Successes: **0**
- View -> Offer Select: **8.0%**
- Select -> Purchase Attempt: **7.4%**
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
| android | unknown | item_unavailable | 2 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical_monthly | 38 | 1 | 0 | 2.6% | 0.0% |
| android | elite_tactical | 9 | 1 | 0 | 11.1% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 468 | 172 |
| android | elite_tactical | 403 | 178 |
| android | pro_base | 249 | 156 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 321 | 1 | 0 | 0.3% | 0.0% |
| voice_gate | 232 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 36 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| sound_gate | 5 | 1 | 0 | 20.0% | 0.0% |
| qualified_training_gate | 5 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **232** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **36** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3631 | 364 |
| alarm_duration | 3143 | 337 |
| min_seconds | 2465 | 340 |
| volume | 2257 | 232 |
| sound_type | 1838 | 280 |
| repeat_enabled | 1395 | 330 |
| voice_callouts_enabled | 852 | 205 |
| unknown | 818 | 13 |
| vibration_enabled | 631 | 237 |
| repeat_rounds | 422 | 125 |
| voice_gender | 387 | 238 |
| use_extended_range | 288 | 173 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
