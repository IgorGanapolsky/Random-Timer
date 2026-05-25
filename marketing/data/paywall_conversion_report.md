# Paywall Conversion Report

Generated: 2026-05-25T20:54:43+00:00
Window (days): 30

## Funnel
- Views: **300**
- Offer Selects: **62**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **20.7%**
- Select -> Purchase Attempt: **8.1%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 5 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 47 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 494 | 142 |
| android | elite_tactical | 352 | 126 |
| android | pro_base | 194 | 102 |
| android | unknown | 128 | 89 |
| ios | unknown | 9 | 4 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 115 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 62 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 34 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 16 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |
| qualified_training_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `range_gate` had **115** views and **0** purchase attempts.
- `voice_gate` had **62** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **34** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 4159 | 34 |
| max_seconds | 2560 | 266 |
| min_seconds | 1964 | 250 |
| alarm_duration | 1829 | 243 |
| sound_type | 1636 | 218 |
| volume | 1578 | 163 |
| repeat_enabled | 1028 | 233 |
| voice_callouts_enabled | 676 | 146 |
| vibration_enabled | 517 | 170 |
| repeat_rounds | 391 | 114 |
| voice_gender | 314 | 191 |
| use_extended_range | 207 | 134 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
