# Paywall Conversion Report

Generated: 2026-10-07T12:34:53+00:00
Window (days): 30

## Funnel
- Views: **47**
- Offer Selects: **1**
- Purchase Attempts: **2**
- Purchase Successes: **0**
- View -> Offer Select: **2.1%**
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
| android | pro_base | 51 | 49 |
| android | elite_tactical | 47 | 47 |
| android | elite_tactical_monthly | 47 | 47 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 20 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 10 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 9 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 2 | 2 | 0 | 100.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2302 | 81 |
| max_seconds | 1802 | 99 |
| alarm_duration | 1703 | 95 |
| sound_type | 1105 | 106 |
| min_seconds | 926 | 99 |
| voice_callouts_enabled | 698 | 64 |
| repeat_enabled | 598 | 95 |
| repeat_rounds | 279 | 60 |
| voice_gender | 261 | 93 |
| vibration_enabled | 192 | 71 |
| use_extended_range | 191 | 63 |
| unknown | 36 | 4 |

## Data Quality Warnings
- purchase_attempts exceed offer_selects; paywall funnel events are inconsistent and need instrumentation review
- unknown paywall entry_point is still receiving meaningful traffic
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
