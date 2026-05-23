# Paywall Conversion Report

Generated: 2026-05-23T18:19:35+00:00
Window (days): 30

## Funnel
- Views: **307**
- Offer Selects: **66**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **21.5%**
- Select -> Purchase Attempt: **7.6%**
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
| android | elite_tactical_monthly | 51 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 499 | 138 |
| android | elite_tactical | 353 | 121 |
| android | pro_base | 187 | 95 |
| android | unknown | 120 | 81 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 115 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 62 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 37 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 22 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |

## Leaky Entry Points
- `range_gate` had **115** views and **0** purchase attempts.
- `voice_gate` had **62** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **37** views and **0** purchase attempts.
- `setup_upgrade_cta` had **22** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 4616 | 44 |
| max_seconds | 2446 | 254 |
| min_seconds | 1919 | 238 |
| alarm_duration | 1840 | 234 |
| sound_type | 1639 | 209 |
| volume | 1448 | 158 |
| repeat_enabled | 998 | 224 |
| voice_callouts_enabled | 661 | 141 |
| vibration_enabled | 491 | 165 |
| repeat_rounds | 380 | 109 |
| voice_gender | 302 | 183 |
| use_extended_range | 207 | 129 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
