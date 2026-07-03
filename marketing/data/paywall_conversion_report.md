# Paywall Conversion Report

Generated: 2026-07-03T12:49:15+00:00
Window (days): 30

## Funnel
- Views: **128**
- Offer Selects: **10**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **7.8%**
- Select -> Purchase Attempt: **20.0%**
- Attempt -> Purchase Success: **50.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 4 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 4 | 4 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 10 | 2 | 1 | 20.0% | 50.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 31 | 19 |
| android | pro_base | 26 | 25 |
| android | elite_tactical | 25 | 24 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 66 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 26 | 2 | 1 | 7.7% | 50.0% |
| qualified_training_gate | 20 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **66** views and **0** purchase attempts.
- `qualified_training_gate` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2115 | 118 |
| volume | 1336 | 75 |
| alarm_duration | 1325 | 104 |
| min_seconds | 1243 | 105 |
| sound_type | 929 | 101 |
| repeat_enabled | 349 | 92 |
| voice_callouts_enabled | 329 | 58 |
| repeat_rounds | 168 | 55 |
| voice_gender | 162 | 87 |
| use_extended_range | 159 | 58 |
| vibration_enabled | 109 | 73 |
| unknown | 38 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
