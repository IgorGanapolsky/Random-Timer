# Paywall Conversion Report

Generated: 2026-05-19T17:44:25+00:00
Window (days): 30

## Funnel
- Views: **361**
- Offer Selects: **112**
- Purchase Attempts: **7**
- Purchase Successes: **0**
- View -> Offer Select: **31.0%**
- Select -> Purchase Attempt: **6.2%**
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
| android | elite_tactical | 9 | 1 | 0 | 11.1% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| android | elite_tactical_monthly | 96 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 503 | 120 |
| android | elite_tactical | 340 | 98 |
| android | pro_base | 106 | 50 |
| android | unknown | 60 | 35 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| setup_upgrade_cta | 110 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 79 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 39 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 7 | 5 | 0 | 71.4% | 0.0% |

## Leaky Entry Points
- `setup_upgrade_cta` had **110** views and **0** purchase attempts.
- `range_gate` had **79** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **39** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 10085 | 151 |
| max_seconds | 1914 | 184 |
| alarm_duration | 1592 | 168 |
| min_seconds | 1490 | 171 |
| sound_type | 1388 | 152 |
| volume | 1027 | 113 |
| repeat_enabled | 663 | 162 |
| voice_callouts_enabled | 482 | 102 |
| vibration_enabled | 297 | 117 |
| repeat_rounds | 233 | 71 |
| voice_gender | 224 | 127 |
| use_extended_range | 169 | 93 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
