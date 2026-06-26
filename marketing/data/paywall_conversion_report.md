# Paywall Conversion Report

Generated: 2026-06-26T12:58:01+00:00
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
| android | pro_base | 61 | 60 |
| android | elite_tactical | 59 | 58 |
| android | elite_tactical_monthly | 52 | 38 |

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
| max_seconds | 2427 | 179 |
| alarm_duration | 2185 | 169 |
| volume | 1542 | 118 |
| min_seconds | 1391 | 168 |
| sound_type | 1077 | 139 |
| repeat_enabled | 604 | 155 |
| voice_callouts_enabled | 439 | 99 |
| use_extended_range | 215 | 86 |
| voice_gender | 205 | 114 |
| vibration_enabled | 183 | 117 |
| repeat_rounds | 173 | 58 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
