# Paywall Conversion Report

Generated: 2026-07-13T07:22:37+00:00
Window (days): 30

## Funnel
- Views: **76**
- Offer Selects: **7**
- Purchase Attempts: **1**
- Purchase Successes: **1**
- View -> Offer Select: **9.2%**
- Select -> Purchase Attempt: **14.3%**
- Attempt -> Purchase Success: **100.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 1 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | pro_base | 2 | 1 | 1 | 50.0% | 100.0% |
| android | elite_tactical | 5 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 2 | 2 |
| android | elite_tactical | 1 | 1 |
| android | elite_tactical_monthly | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 55 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 17 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 1 | 1 | 50.0% | 100.0% |

## Leaky Entry Points
- `unknown` had **55** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2147 | 40 |
| volume | 1058 | 12 |
| min_seconds | 1007 | 28 |
| repeat_rounds | 108 | 1 |
| sound_type | 77 | 22 |
| alarm_duration | 60 | 27 |
| unknown | 43 | 2 |
| repeat_enabled | 40 | 19 |
| voice_gender | 30 | 14 |
| vibration_enabled | 18 | 13 |
| use_extended_range | 9 | 3 |
| voice_callouts_enabled | 7 | 3 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
