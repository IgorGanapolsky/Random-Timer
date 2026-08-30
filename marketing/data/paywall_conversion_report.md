# Paywall Conversion Report

Generated: 2026-08-30T06:32:02+00:00
Window (days): 30

## Funnel
- Views: **77**
- Offer Selects: **17**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **22.1%**
- Select -> Purchase Attempt: **11.8%**
- Attempt -> Purchase Success: **50.0%**

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
| android | pro_base | 5 | 1 | 1 | 20.0% | 100.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 11 | 0 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 39 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 24 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **39** views and **0** purchase attempts.
- `qualified_training_gate` had **24** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2959 | 63 |
| volume | 1905 | 25 |
| min_seconds | 1322 | 52 |
| sound_type | 151 | 39 |
| alarm_duration | 129 | 53 |
| repeat_enabled | 121 | 51 |
| voice_gender | 51 | 23 |
| vibration_enabled | 39 | 29 |
| unknown | 36 | 2 |
| voice_callouts_enabled | 8 | 1 |
| repeat_rounds | 6 | 1 |
| use_extended_range | 5 | 3 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
