# Paywall Conversion Report

Generated: 2026-07-04T12:35:34+00:00
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
| android | elite_tactical_monthly | 30 | 19 |
| android | pro_base | 25 | 24 |
| android | elite_tactical | 24 | 23 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 68 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 24 | 2 | 1 | 8.3% | 50.0% |
| qualified_training_gate | 20 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **68** views and **0** purchase attempts.
- `qualified_training_gate` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2052 | 110 |
| volume | 1303 | 69 |
| min_seconds | 1208 | 97 |
| alarm_duration | 1195 | 97 |
| sound_type | 847 | 94 |
| repeat_enabled | 318 | 85 |
| voice_callouts_enabled | 293 | 52 |
| voice_gender | 148 | 79 |
| repeat_rounds | 147 | 49 |
| use_extended_range | 146 | 52 |
| vibration_enabled | 101 | 67 |
| unknown | 61 | 3 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
