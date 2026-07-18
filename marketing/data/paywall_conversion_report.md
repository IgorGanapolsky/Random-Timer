# Paywall Conversion Report

Generated: 2026-07-18T06:49:43+00:00
Window (days): 30

## Funnel
- Views: **65**
- Offer Selects: **6**
- Purchase Attempts: **1**
- Purchase Successes: **1**
- View -> Offer Select: **9.2%**
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
| android | pro_base | 3 | 2 |
| android | elite_tactical | 1 | 1 |
| android | elite_tactical_monthly | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 47 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 1 | 1 | 50.0% | 100.0% |

## Leaky Entry Points
- `unknown` had **47** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2033 | 34 |
| volume | 1398 | 14 |
| min_seconds | 994 | 24 |
| repeat_rounds | 108 | 1 |
| sound_type | 80 | 22 |
| alarm_duration | 68 | 27 |
| repeat_enabled | 46 | 20 |
| unknown | 43 | 2 |
| voice_gender | 38 | 17 |
| vibration_enabled | 20 | 15 |
| use_extended_range | 9 | 2 |
| voice_callouts_enabled | 8 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
