# Paywall Conversion Report

Generated: 2026-07-21T00:51:06+00:00
Window (days): 30

## Funnel
- Views: **53**
- Offer Selects: **6**
- Purchase Attempts: **1**
- Purchase Successes: **1**
- View -> Offer Select: **11.3%**
- Select -> Purchase Attempt: **16.7%**
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
| android | elite_tactical | 4 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 2 | 2 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 33 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 18 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 1 | 1 | 50.0% | 100.0% |

## Leaky Entry Points
- `unknown` had **33** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2409 | 39 |
| volume | 1504 | 17 |
| min_seconds | 1007 | 25 |
| repeat_rounds | 108 | 1 |
| sound_type | 85 | 24 |
| alarm_duration | 74 | 32 |
| repeat_enabled | 50 | 21 |
| unknown | 43 | 2 |
| voice_gender | 42 | 18 |
| vibration_enabled | 21 | 16 |
| use_extended_range | 12 | 2 |
| voice_callouts_enabled | 9 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
