# Paywall Conversion Report

Generated: 2026-07-01T07:47:24+00:00
Window (days): 30

## Funnel
- Views: **278**
- Offer Selects: **11**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **4.0%**
- Select -> Purchase Attempt: **18.2%**
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
| android | elite_tactical | 11 | 2 | 1 | 18.2% | 50.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 40 | 39 |
| android | elite_tactical | 38 | 37 |
| android | elite_tactical_monthly | 34 | 21 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 102 | 2 | 1 | 2.0% | 50.0% |
| voice_gate | 70 | 0 | 0 | 0.0% | 0.0% |
| unknown | 65 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 19 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **70** views and **0** purchase attempts.
- `unknown` had **65** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2392 | 151 |
| alarm_duration | 1754 | 138 |
| min_seconds | 1478 | 137 |
| volume | 1295 | 97 |
| sound_type | 1028 | 125 |
| repeat_enabled | 449 | 123 |
| voice_callouts_enabled | 383 | 78 |
| voice_gender | 193 | 106 |
| use_extended_range | 186 | 71 |
| repeat_rounds | 173 | 58 |
| vibration_enabled | 146 | 96 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
