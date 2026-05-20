# Paywall Conversion Report

Generated: 2026-05-20T13:38:34+00:00
Window (days): 30

## Funnel
- Views: **377**
- Offer Selects: **105**
- Purchase Attempts: **7**
- Purchase Successes: **0**
- View -> Offer Select: **27.9%**
- Select -> Purchase Attempt: **6.7%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 7 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 3 | 3 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.pro | 0 | 3 | 0 | 0.0% | 0.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| android | elite_tactical_monthly | 90 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 547 | 140 |
| android | elite_tactical | 384 | 118 |
| android | pro_base | 148 | 71 |
| android | unknown | 90 | 56 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| setup_upgrade_cta | 100 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 97 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 46 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 8 | 5 | 0 | 62.5% | 0.0% |

## Leaky Entry Points
- `setup_upgrade_cta` had **100** views and **0** purchase attempts.
- `range_gate` had **97** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **46** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 9489 | 142 |
| max_seconds | 2183 | 215 |
| alarm_duration | 1705 | 198 |
| min_seconds | 1701 | 201 |
| sound_type | 1497 | 180 |
| volume | 1259 | 134 |
| repeat_enabled | 804 | 192 |
| voice_callouts_enabled | 561 | 120 |
| vibration_enabled | 377 | 139 |
| repeat_rounds | 292 | 88 |
| voice_gender | 257 | 152 |
| use_extended_range | 187 | 109 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
