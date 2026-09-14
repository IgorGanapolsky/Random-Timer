# Paywall Conversion Report

Generated: 2026-09-14T00:59:41+00:00
Window (days): 30

## Funnel
- Views: **70**
- Offer Selects: **6**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **8.6%**
- Select -> Purchase Attempt: **16.7%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 26 |
| user_cancelled | 1 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 26 | 5 |
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 6 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 39 | 39 |
| android | elite_tactical | 35 | 35 |
| android | elite_tactical_monthly | 35 | 35 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 28 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **28** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3143 | 102 |
| volume | 2104 | 67 |
| min_seconds | 1628 | 101 |
| alarm_duration | 1421 | 98 |
| sound_type | 928 | 92 |
| voice_callouts_enabled | 606 | 49 |
| repeat_enabled | 545 | 94 |
| repeat_rounds | 232 | 47 |
| voice_gender | 220 | 78 |
| vibration_enabled | 184 | 69 |
| use_extended_range | 155 | 50 |
| unknown | 7 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
