# Paywall Conversion Report

Generated: 2026-05-29T13:10:23+00:00
Window (days): 30

## Funnel
- Views: **509**
- Offer Selects: **60**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **11.8%**
- Select -> Purchase Attempt: **8.3%**
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
| android | elite_tactical_monthly | 45 | 1 | 0 | 2.2% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 511 | 172 |
| android | elite_tactical | 389 | 162 |
| android | pro_base | 231 | 138 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 231 | 1 | 0 | 0.4% | 0.0% |
| voice_gate | 154 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 38 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| setup_upgrade_cta | 10 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 5 | 2 | 0 | 40.0% | 0.0% |
| qualified_training_gate | 3 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **154** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **38** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 3318 | 27 |
| max_seconds | 3007 | 320 |
| alarm_duration | 2526 | 293 |
| min_seconds | 2246 | 297 |
| volume | 2102 | 201 |
| sound_type | 1766 | 253 |
| repeat_enabled | 1241 | 289 |
| voice_callouts_enabled | 769 | 179 |
| vibration_enabled | 576 | 204 |
| repeat_rounds | 396 | 116 |
| voice_gender | 338 | 210 |
| use_extended_range | 241 | 151 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
