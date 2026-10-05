# Paywall Conversion Report

Generated: 2026-10-05T18:29:05+00:00
Window (days): 30

## Funnel
- Views: **49**
- Offer Selects: **0**
- Purchase Attempts: **2**
- Purchase Successes: **0**
- View -> Offer Select: **0.0%**
- Select -> Purchase Attempt: **0.0%**
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

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 55 | 53 |
| android | elite_tactical | 51 | 51 |
| android | elite_tactical_monthly | 51 | 51 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 20 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 7 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 2 | 2 | 0 | 100.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2344 | 86 |
| alarm_duration | 1841 | 101 |
| max_seconds | 1824 | 103 |
| sound_type | 1192 | 112 |
| min_seconds | 953 | 105 |
| voice_callouts_enabled | 767 | 69 |
| repeat_enabled | 642 | 99 |
| repeat_rounds | 305 | 65 |
| voice_gender | 277 | 98 |
| vibration_enabled | 209 | 76 |
| use_extended_range | 207 | 68 |
| unknown | 36 | 4 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
