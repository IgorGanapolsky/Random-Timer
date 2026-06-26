# Paywall Conversion Report

Generated: 2026-06-26T07:34:13+00:00
Window (days): 30

## Funnel
- Views: **408**
- Offer Selects: **9**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **2.2%**
- Select -> Purchase Attempt: **22.2%**
- Attempt -> Purchase Success: **50.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 29 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 29 | 20 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 9 | 2 | 1 | 22.2% | 50.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 62 | 61 |
| android | elite_tactical | 60 | 59 |
| android | elite_tactical_monthly | 53 | 39 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 174 | 2 | 1 | 1.1% | 50.0% |
| voice_gate | 132 | 0 | 0 | 0.0% | 0.0% |
| unknown | 64 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **132** views and **0** purchase attempts.
- `unknown` had **64** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2432 | 180 |
| alarm_duration | 2189 | 170 |
| volume | 1551 | 119 |
| min_seconds | 1393 | 169 |
| sound_type | 1083 | 140 |
| repeat_enabled | 611 | 156 |
| voice_callouts_enabled | 444 | 100 |
| use_extended_range | 216 | 87 |
| voice_gender | 207 | 115 |
| vibration_enabled | 189 | 118 |
| repeat_rounds | 178 | 59 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
