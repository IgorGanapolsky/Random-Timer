# Paywall Conversion Report

Generated: 2026-06-30T18:49:36+00:00
Window (days): 30

## Funnel
- Views: **293**
- Offer Selects: **10**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **3.4%**
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
| android | pro_base | 43 | 42 |
| android | elite_tactical | 41 | 40 |
| android | elite_tactical_monthly | 38 | 24 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 112 | 2 | 1 | 1.8% | 50.0% |
| voice_gate | 78 | 0 | 0 | 0.0% | 0.0% |
| unknown | 63 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 18 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **78** views and **0** purchase attempts.
- `unknown` had **63** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2386 | 153 |
| alarm_duration | 1833 | 141 |
| min_seconds | 1507 | 140 |
| volume | 1170 | 98 |
| sound_type | 1035 | 126 |
| repeat_enabled | 474 | 125 |
| voice_callouts_enabled | 393 | 81 |
| voice_gender | 197 | 108 |
| use_extended_range | 192 | 74 |
| repeat_rounds | 173 | 58 |
| vibration_enabled | 152 | 98 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
