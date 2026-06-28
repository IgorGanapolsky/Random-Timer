# Paywall Conversion Report

Generated: 2026-06-28T01:19:18+00:00
Window (days): 30

## Funnel
- Views: **303**
- Offer Selects: **9**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **3.0%**
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
| android | pro_base | 46 | 45 |
| android | elite_tactical | 44 | 43 |
| android | elite_tactical_monthly | 42 | 28 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 118 | 2 | 1 | 1.7% | 50.0% |
| voice_gate | 82 | 0 | 0 | 0.0% | 0.0% |
| unknown | 64 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 17 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **82** views and **0** purchase attempts.
- `unknown` had **64** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2210 | 156 |
| alarm_duration | 1860 | 146 |
| volume | 1507 | 100 |
| min_seconds | 1266 | 145 |
| sound_type | 1028 | 125 |
| repeat_enabled | 494 | 131 |
| voice_callouts_enabled | 397 | 83 |
| voice_gender | 199 | 109 |
| use_extended_range | 196 | 76 |
| repeat_rounds | 173 | 58 |
| vibration_enabled | 156 | 100 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
