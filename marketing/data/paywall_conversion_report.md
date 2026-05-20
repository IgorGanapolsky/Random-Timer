# Paywall Conversion Report

Generated: 2026-05-20T00:09:09+00:00
Window (days): 30

## Funnel
- Views: **379**
- Offer Selects: **112**
- Purchase Attempts: **7**
- Purchase Successes: **0**
- View -> Offer Select: **29.5%**
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
| android | elite_tactical_monthly | 535 | 134 |
| android | elite_tactical | 372 | 112 |
| android | pro_base | 132 | 64 |
| android | unknown | 80 | 49 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| setup_upgrade_cta | 110 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 91 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 45 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 7 | 5 | 0 | 71.4% | 0.0% |

## Leaky Entry Points
- `setup_upgrade_cta` had **110** views and **0** purchase attempts.
- `range_gate` had **91** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **45** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 10085 | 151 |
| max_seconds | 2128 | 209 |
| alarm_duration | 1688 | 194 |
| min_seconds | 1657 | 195 |
| sound_type | 1478 | 175 |
| volume | 1230 | 129 |
| repeat_enabled | 785 | 188 |
| voice_callouts_enabled | 548 | 117 |
| vibration_enabled | 364 | 136 |
| repeat_rounds | 283 | 85 |
| voice_gender | 251 | 147 |
| use_extended_range | 184 | 106 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
