# Paywall Conversion Report

Generated: 2026-05-22T16:34:26+00:00
Window (days): 30

## Funnel
- Views: **313**
- Offer Selects: **73**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **23.3%**
- Select -> Purchase Attempt: **6.9%**
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
| android | elite_tactical_monthly | 58 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 501 | 132 |
| android | elite_tactical | 346 | 114 |
| android | pro_base | 172 | 85 |
| android | unknown | 106 | 69 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 107 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 39 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 36 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |

## Leaky Entry Points
- `range_gate` had **107** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **39** views and **0** purchase attempts.
- `setup_upgrade_cta` had **36** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 6506 | 72 |
| max_seconds | 2334 | 236 |
| min_seconds | 1847 | 222 |
| alarm_duration | 1776 | 217 |
| sound_type | 1580 | 197 |
| volume | 1367 | 148 |
| repeat_enabled | 894 | 209 |
| voice_callouts_enabled | 618 | 132 |
| vibration_enabled | 443 | 154 |
| repeat_rounds | 342 | 100 |
| voice_gender | 285 | 169 |
| use_extended_range | 199 | 121 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
