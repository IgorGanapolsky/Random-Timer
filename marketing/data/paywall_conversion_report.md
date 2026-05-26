# Paywall Conversion Report

Generated: 2026-05-26T19:04:22+00:00
Window (days): 30

## Funnel
- Views: **404**
- Offer Selects: **62**
- Purchase Attempts: **6**
- Purchase Successes: **0**
- View -> Offer Select: **15.3%**
- Select -> Purchase Attempt: **9.7%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 5 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | user_cancelled | 4 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 47 | 1 | 0 | 2.1% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 512 | 162 |
| android | elite_tactical | 373 | 146 |
| android | pro_base | 215 | 122 |
| android | unknown | 198 | 112 |
| ios | unknown | 15 | 5 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 175 | 1 | 0 | 0.6% | 0.0% |
| voice_gate | 100 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| setup_upgrade_cta | 14 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |
| qualified_training_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **100** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 3972 | 33 |
| max_seconds | 2677 | 287 |
| alarm_duration | 2185 | 265 |
| min_seconds | 2036 | 269 |
| sound_type | 1708 | 236 |
| volume | 1637 | 179 |
| repeat_enabled | 1117 | 259 |
| voice_callouts_enabled | 722 | 162 |
| vibration_enabled | 535 | 183 |
| repeat_rounds | 393 | 116 |
| voice_gender | 327 | 202 |
| use_extended_range | 220 | 140 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
