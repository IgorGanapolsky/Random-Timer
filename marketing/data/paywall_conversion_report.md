# Paywall Conversion Report

Generated: 2026-08-07T06:33:05+00:00
Window (days): 30

## Funnel
- Views: **52**
- Offer Selects: **7**
- Purchase Attempts: **3**
- Purchase Successes: **2**
- View -> Offer Select: **13.5%**
- Select -> Purchase Attempt: **42.9%**
- Attempt -> Purchase Success: **66.7%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 1 |
| user_cancelled | 1 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 1 | 1 |
| android | unknown | failed | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | pro_base | 4 | 2 | 2 | 50.0% | 100.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 3 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| qualified_training_gate | 26 | 0 | 0 | 0.0% | 0.0% |
| unknown | 21 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 1 | 0 | 100.0% | 0.0% |

## Leaky Entry Points
- `qualified_training_gate` had **26** views and **0** purchase attempts.
- `unknown` had **21** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2863 | 47 |
| volume | 1706 | 22 |
| min_seconds | 1231 | 39 |
| sound_type | 126 | 34 |
| repeat_rounds | 108 | 1 |
| repeat_enabled | 98 | 37 |
| alarm_duration | 90 | 43 |
| voice_gender | 66 | 23 |
| unknown | 41 | 2 |
| vibration_enabled | 25 | 21 |
| use_extended_range | 12 | 3 |
| voice_callouts_enabled | 8 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
