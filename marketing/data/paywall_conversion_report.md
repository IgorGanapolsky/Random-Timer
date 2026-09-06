# Paywall Conversion Report

Generated: 2026-09-06T22:29:23+00:00
Window (days): 30

## Funnel
- Views: **62**
- Offer Selects: **15**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **24.2%**
- Select -> Purchase Attempt: **6.7%**
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
| android | elite_tactical | 11 | 0 | 0 | 0.0% | 0.0% |
| android | pro_base | 3 | 0 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 2 | 2 |
| android | elite_tactical | 1 | 1 |
| android | elite_tactical_monthly | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 30 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 20 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **30** views and **0** purchase attempts.
- `qualified_training_gate` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3111 | 60 |
| volume | 1445 | 23 |
| min_seconds | 1404 | 49 |
| alarm_duration | 126 | 46 |
| sound_type | 120 | 31 |
| repeat_enabled | 99 | 41 |
| voice_gender | 44 | 19 |
| unknown | 36 | 2 |
| vibration_enabled | 36 | 26 |
| voice_callouts_enabled | 14 | 2 |
| repeat_rounds | 9 | 2 |
| use_extended_range | 6 | 3 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
