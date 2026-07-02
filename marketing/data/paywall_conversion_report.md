# Paywall Conversion Report

Generated: 2026-07-02T07:21:43+00:00
Window (days): 30

## Funnel
- Views: **229**
- Offer Selects: **10**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **4.4%**
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
| android | pro_base | 34 | 33 |
| android | elite_tactical | 32 | 31 |
| android | elite_tactical_monthly | 31 | 19 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 72 | 2 | 1 | 2.8% | 50.0% |
| unknown | 66 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 19 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **66** views and **0** purchase attempts.
- `voice_gate` had **50** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2276 | 139 |
| alarm_duration | 1578 | 125 |
| min_seconds | 1334 | 126 |
| volume | 1247 | 88 |
| sound_type | 988 | 114 |
| repeat_enabled | 410 | 111 |
| voice_callouts_enabled | 359 | 69 |
| voice_gender | 179 | 98 |
| use_extended_range | 176 | 66 |
| repeat_rounds | 173 | 58 |
| vibration_enabled | 131 | 86 |
| unknown | 38 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
