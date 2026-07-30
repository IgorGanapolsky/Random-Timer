# Paywall Conversion Report

Generated: 2026-07-30T00:46:55+00:00
Window (days): 30

## Funnel
- Views: **45**
- Offer Selects: **6**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **13.3%**
- Select -> Purchase Attempt: **33.3%**
- Attempt -> Purchase Success: **50.0%**

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
| android | pro_base | 2 | 1 | 1 | 50.0% | 100.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 4 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 2 | 2 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| qualified_training_gate | 22 | 0 | 0 | 0.0% | 0.0% |
| unknown | 20 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 1 | 0 | 100.0% | 0.0% |

## Leaky Entry Points
- `qualified_training_gate` had **22** views and **0** purchase attempts.
- `unknown` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2806 | 43 |
| volume | 1349 | 21 |
| min_seconds | 1280 | 34 |
| repeat_rounds | 108 | 1 |
| sound_type | 106 | 30 |
| unknown | 84 | 4 |
| alarm_duration | 75 | 38 |
| repeat_enabled | 71 | 30 |
| voice_gender | 65 | 22 |
| vibration_enabled | 23 | 18 |
| use_extended_range | 10 | 2 |
| voice_callouts_enabled | 8 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
