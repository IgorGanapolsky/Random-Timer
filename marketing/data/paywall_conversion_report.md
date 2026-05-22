# Paywall Conversion Report

Generated: 2026-05-22T03:45:25+00:00
Window (days): 30

## Funnel
- Views: **332**
- Offer Selects: **81**
- Purchase Attempts: **6**
- Purchase Successes: **0**
- View -> Offer Select: **24.4%**
- Select -> Purchase Attempt: **7.4%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 6 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 2 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.pro | 0 | 2 | 0 | 0.0% | 0.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| android | elite_tactical_monthly | 66 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 519 | 135 |
| android | elite_tactical | 361 | 116 |
| android | pro_base | 169 | 82 |
| android | unknown | 103 | 66 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 107 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 52 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 7 | 4 | 0 | 57.1% | 0.0% |

## Leaky Entry Points
- `range_gate` had **107** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `setup_upgrade_cta` had **52** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 7183 | 86 |
| max_seconds | 2318 | 232 |
| min_seconds | 1839 | 218 |
| alarm_duration | 1762 | 213 |
| sound_type | 1559 | 193 |
| volume | 1343 | 145 |
| repeat_enabled | 872 | 206 |
| voice_callouts_enabled | 603 | 129 |
| vibration_enabled | 425 | 151 |
| repeat_rounds | 327 | 97 |
| voice_gender | 277 | 165 |
| use_extended_range | 196 | 118 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
