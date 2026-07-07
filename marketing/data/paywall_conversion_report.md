# Paywall Conversion Report

Generated: 2026-07-07T13:00:51+00:00
Window (days): 30

## Funnel
- Views: **123**
- Offer Selects: **10**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **8.1%**
- Select -> Purchase Attempt: **20.0%**
- Attempt -> Purchase Success: **50.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 3 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 3 | 3 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 10 | 2 | 1 | 20.0% | 50.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 24 | 18 |
| android | pro_base | 21 | 20 |
| android | elite_tactical | 19 | 18 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 68 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 21 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 18 | 2 | 1 | 11.1% | 50.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **68** views and **0** purchase attempts.
- `qualified_training_gate` had **21** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2059 | 93 |
| volume | 1382 | 57 |
| min_seconds | 1163 | 80 |
| alarm_duration | 930 | 82 |
| sound_type | 665 | 78 |
| repeat_enabled | 260 | 71 |
| voice_callouts_enabled | 224 | 40 |
| voice_gender | 122 | 64 |
| use_extended_range | 115 | 40 |
| repeat_rounds | 111 | 37 |
| vibration_enabled | 79 | 55 |
| unknown | 43 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
