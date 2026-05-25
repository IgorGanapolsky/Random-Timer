# Paywall Conversion Report

Generated: 2026-05-25T14:01:46+00:00
Window (days): 30

## Funnel
- Views: **304**
- Offer Selects: **63**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **20.7%**
- Select -> Purchase Attempt: **7.9%**
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
| android | elite_tactical_monthly | 48 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 492 | 137 |
| android | elite_tactical | 350 | 121 |
| android | pro_base | 188 | 96 |
| android | unknown | 122 | 83 |
| ios | unknown | 9 | 4 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 117 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 62 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 36 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 16 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |
| qualified_training_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `range_gate` had **117** views and **0** purchase attempts.
- `voice_gate` had **62** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **36** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 4194 | 36 |
| max_seconds | 2527 | 260 |
| min_seconds | 1951 | 243 |
| alarm_duration | 1792 | 236 |
| sound_type | 1600 | 210 |
| volume | 1536 | 158 |
| repeat_enabled | 994 | 225 |
| voice_callouts_enabled | 647 | 140 |
| vibration_enabled | 489 | 164 |
| repeat_rounds | 373 | 108 |
| voice_gender | 302 | 184 |
| use_extended_range | 201 | 128 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
