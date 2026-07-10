# Paywall Conversion Report

Generated: 2026-07-10T07:23:12+00:00
Window (days): 30

## Funnel
- Views: **101**
- Offer Selects: **8**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **7.9%**
- Select -> Purchase Attempt: **25.0%**
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
| android | elite_tactical | 8 | 2 | 1 | 25.0% | 50.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 11 | 9 |
| android | pro_base | 9 | 9 |
| android | elite_tactical | 7 | 7 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 67 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 10 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 8 | 2 | 1 | 25.0% | 50.0% |

## Leaky Entry Points
- `unknown` had **67** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 1840 | 60 |
| volume | 1181 | 32 |
| min_seconds | 1025 | 49 |
| alarm_duration | 449 | 51 |
| sound_type | 325 | 46 |
| repeat_enabled | 138 | 40 |
| voice_callouts_enabled | 98 | 18 |
| voice_gender | 70 | 36 |
| use_extended_range | 52 | 18 |
| repeat_rounds | 48 | 16 |
| unknown | 43 | 2 |
| vibration_enabled | 43 | 29 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
