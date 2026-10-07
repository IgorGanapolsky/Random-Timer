# Paywall Conversion Report

Generated: 2026-10-07T18:28:26+00:00
Window (days): 30

## Funnel
- Views: **41**
- Offer Selects: **1**
- Purchase Attempts: **2**
- Purchase Successes: **0**
- View -> Offer Select: **2.4%**
- Select -> Purchase Attempt: **200.0%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 3 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 3 | 2 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 38 | 36 |
| android | elite_tactical | 35 | 35 |
| android | elite_tactical_monthly | 35 | 35 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 20 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 9 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 2 | 2 | 0 | 100.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2188 | 68 |
| max_seconds | 1742 | 86 |
| alarm_duration | 1307 | 79 |
| sound_type | 860 | 89 |
| min_seconds | 843 | 84 |
| voice_callouts_enabled | 530 | 51 |
| repeat_enabled | 458 | 78 |
| repeat_rounds | 210 | 47 |
| voice_gender | 207 | 76 |
| vibration_enabled | 148 | 57 |
| use_extended_range | 144 | 49 |
| unknown | 36 | 4 |

## Data Quality Warnings
- purchase_attempts exceed offer_selects; paywall funnel events are inconsistent and need instrumentation review
- unknown paywall entry_point is still receiving meaningful traffic
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
