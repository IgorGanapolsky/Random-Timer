# Paywall Conversion Report

Generated: 2026-06-30T12:59:22+00:00
Window (days): 30

## Funnel
- Views: **291**
- Offer Selects: **9**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **3.1%**
- Select -> Purchase Attempt: **22.2%**
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
| android | elite_tactical | 9 | 2 | 1 | 22.2% | 50.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 43 | 42 |
| android | elite_tactical | 41 | 40 |
| android | elite_tactical_monthly | 38 | 24 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 112 | 2 | 1 | 1.8% | 50.0% |
| voice_gate | 78 | 0 | 0 | 0.0% | 0.0% |
| unknown | 63 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **78** views and **0** purchase attempts.
- `unknown` had **63** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2113 | 152 |
| alarm_duration | 1826 | 140 |
| min_seconds | 1268 | 139 |
| volume | 1138 | 97 |
| sound_type | 1030 | 125 |
| repeat_enabled | 473 | 124 |
| voice_callouts_enabled | 393 | 81 |
| voice_gender | 196 | 107 |
| use_extended_range | 192 | 74 |
| repeat_rounds | 173 | 58 |
| vibration_enabled | 152 | 98 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
