# Paywall Conversion Report

Generated: 2026-07-04T18:29:20+00:00
Window (days): 30

## Funnel
- Views: **126**
- Offer Selects: **10**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **7.9%**
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
| android | elite_tactical_monthly | 30 | 19 |
| android | pro_base | 25 | 24 |
| android | elite_tactical | 24 | 23 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 68 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 22 | 2 | 1 | 9.1% | 50.0% |
| qualified_training_gate | 20 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **68** views and **0** purchase attempts.
- `qualified_training_gate` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2039 | 105 |
| volume | 1285 | 66 |
| min_seconds | 1191 | 92 |
| alarm_duration | 1123 | 93 |
| sound_type | 798 | 90 |
| repeat_enabled | 303 | 82 |
| voice_callouts_enabled | 276 | 49 |
| voice_gender | 141 | 75 |
| repeat_rounds | 138 | 46 |
| use_extended_range | 138 | 49 |
| vibration_enabled | 95 | 64 |
| unknown | 61 | 3 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
