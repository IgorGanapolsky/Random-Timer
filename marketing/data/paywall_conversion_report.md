# Paywall Conversion Report

Generated: 2026-07-02T18:39:02+00:00
Window (days): 30

## Funnel
- Views: **161**
- Offer Selects: **10**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **6.2%**
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
| android | pro_base | 32 | 31 |
| android | elite_tactical_monthly | 31 | 19 |
| android | elite_tactical | 30 | 29 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 66 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 40 | 2 | 1 | 5.0% | 50.0% |
| qualified_training_gate | 19 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **66** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2184 | 124 |
| alarm_duration | 1426 | 111 |
| min_seconds | 1282 | 112 |
| volume | 1210 | 79 |
| sound_type | 966 | 106 |
| repeat_enabled | 373 | 99 |
| voice_callouts_enabled | 342 | 63 |
| repeat_rounds | 173 | 58 |
| use_extended_range | 169 | 63 |
| voice_gender | 168 | 91 |
| vibration_enabled | 118 | 78 |
| unknown | 38 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
