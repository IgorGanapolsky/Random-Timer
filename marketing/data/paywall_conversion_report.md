# Paywall Conversion Report

Generated: 2026-09-03T06:35:47+00:00
Window (days): 30

## Funnel
- Views: **71**
- Offer Selects: **16**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **22.5%**
- Select -> Purchase Attempt: **6.2%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 26 |
| user_cancelled | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 26 | 5 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 12 | 0 | 0 | 0.0% | 0.0% |
| android | pro_base | 3 | 0 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 36 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 21 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **36** views and **0** purchase attempts.
- `qualified_training_gate` had **21** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3039 | 60 |
| volume | 1596 | 23 |
| min_seconds | 1383 | 51 |
| sound_type | 126 | 34 |
| alarm_duration | 120 | 48 |
| repeat_enabled | 111 | 45 |
| voice_gender | 50 | 22 |
| vibration_enabled | 38 | 28 |
| unknown | 36 | 2 |
| voice_callouts_enabled | 8 | 1 |
| repeat_rounds | 6 | 1 |
| use_extended_range | 3 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
