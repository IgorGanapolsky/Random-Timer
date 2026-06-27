# Paywall Conversion Report

Generated: 2026-06-27T02:18:21+00:00
Window (days): 30

## Funnel
- Views: **305**
- Offer Selects: **9**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **2.9%**
- Select -> Purchase Attempt: **22.2%**
- Attempt -> Purchase Success: **50.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 15 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 15 | 10 |

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
| voice_gate | 84 | 0 | 0 | 0.0% | 0.0% |
| unknown | 64 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 17 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **84** views and **0** purchase attempts.
- `unknown` had **64** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2256 | 157 |
| alarm_duration | 1861 | 147 |
| volume | 1543 | 101 |
| min_seconds | 1278 | 146 |
| sound_type | 1026 | 124 |
| repeat_enabled | 498 | 132 |
| voice_callouts_enabled | 396 | 82 |
| voice_gender | 197 | 108 |
| use_extended_range | 194 | 75 |
| repeat_rounds | 173 | 58 |
| vibration_enabled | 157 | 101 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
