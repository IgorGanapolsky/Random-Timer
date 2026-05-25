# Paywall Conversion Report

Generated: 2026-05-25T22:22:09+00:00
Window (days): 30

## Funnel
- Views: **336**
- Offer Selects: **63**
- Purchase Attempts: **6**
- Purchase Successes: **0**
- View -> Offer Select: **18.8%**
- Select -> Purchase Attempt: **9.5%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 5 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | user_cancelled | 4 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 48 | 1 | 0 | 2.1% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 503 | 151 |
| android | elite_tactical | 361 | 135 |
| android | pro_base | 203 | 111 |
| android | unknown | 153 | 98 |
| ios | unknown | 9 | 4 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 135 | 1 | 0 | 0.7% | 0.0% |
| voice_gate | 78 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 34 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| setup_upgrade_cta | 16 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |
| qualified_training_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **78** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **34** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 4022 | 33 |
| max_seconds | 2604 | 274 |
| min_seconds | 1990 | 256 |
| alarm_duration | 1938 | 251 |
| sound_type | 1663 | 225 |
| volume | 1594 | 169 |
| repeat_enabled | 1056 | 243 |
| voice_callouts_enabled | 694 | 151 |
| vibration_enabled | 523 | 174 |
| repeat_rounds | 392 | 115 |
| voice_gender | 319 | 195 |
| use_extended_range | 215 | 137 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
