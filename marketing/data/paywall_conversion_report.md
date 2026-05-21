# Paywall Conversion Report

Generated: 2026-05-21T20:34:33+00:00
Window (days): 30

## Funnel
- Views: **340**
- Offer Selects: **85**
- Purchase Attempts: **6**
- Purchase Successes: **0**
- View -> Offer Select: **25.0%**
- Select -> Purchase Attempt: **7.1%**
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
| android | elite_tactical_monthly | 70 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 525 | 136 |
| android | elite_tactical | 373 | 116 |
| android | pro_base | 164 | 79 |
| android | unknown | 101 | 64 |
| ios | unknown | 4 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 107 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 60 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 60 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| sound_gate | 7 | 4 | 0 | 57.1% | 0.0% |

## Leaky Entry Points
- `range_gate` had **107** views and **0** purchase attempts.
- `voice_gate` had **60** views and **0** purchase attempts.
- `setup_upgrade_cta` had **60** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 7335 | 94 |
| max_seconds | 2299 | 228 |
| min_seconds | 1831 | 214 |
| alarm_duration | 1741 | 209 |
| sound_type | 1541 | 189 |
| volume | 1319 | 142 |
| repeat_enabled | 851 | 202 |
| voice_callouts_enabled | 588 | 126 |
| vibration_enabled | 409 | 148 |
| repeat_rounds | 315 | 94 |
| voice_gender | 270 | 161 |
| use_extended_range | 193 | 115 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
