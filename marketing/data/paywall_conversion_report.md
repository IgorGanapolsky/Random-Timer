# Paywall Conversion Report

Generated: 2026-05-21T16:43:19+00:00
Window (days): 30

## Funnel
- Views: **342**
- Offer Selects: **87**
- Purchase Attempts: **6**
- Purchase Successes: **0**
- View -> Offer Select: **25.4%**
- Select -> Purchase Attempt: **6.9%**
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
| android | elite_tactical_monthly | 72 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 521 | 130 |
| android | elite_tactical | 364 | 110 |
| android | pro_base | 156 | 73 |
| android | unknown | 94 | 58 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 105 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 64 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 7 | 4 | 0 | 57.1% | 0.0% |

## Leaky Entry Points
- `range_gate` had **105** views and **0** purchase attempts.
- `setup_upgrade_cta` had **64** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 7443 | 95 |
| max_seconds | 2264 | 220 |
| min_seconds | 1815 | 206 |
| alarm_duration | 1711 | 201 |
| sound_type | 1502 | 181 |
| volume | 1265 | 136 |
| repeat_enabled | 811 | 195 |
| voice_callouts_enabled | 561 | 120 |
| vibration_enabled | 379 | 141 |
| repeat_rounds | 292 | 88 |
| voice_gender | 259 | 153 |
| use_extended_range | 187 | 109 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
