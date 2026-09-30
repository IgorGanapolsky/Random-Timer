# Paywall Conversion Report

Generated: 2026-09-30T12:37:09+00:00
Window (days): 30

## Funnel
- Views: **52**
- Offer Selects: **1**
- Purchase Attempts: **2**
- Purchase Successes: **0**
- View -> Offer Select: **1.9%**
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
| android | pro_base | 56 | 54 |
| android | elite_tactical | 52 | 52 |
| android | elite_tactical_monthly | 52 | 52 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 19 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 14 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 9 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 2 | 2 | 0 | 100.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- None

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2685 | 88 |
| max_seconds | 2135 | 109 |
| alarm_duration | 1865 | 105 |
| sound_type | 1204 | 112 |
| min_seconds | 1057 | 109 |
| voice_callouts_enabled | 773 | 70 |
| repeat_enabled | 660 | 104 |
| repeat_rounds | 308 | 66 |
| voice_gender | 274 | 97 |
| vibration_enabled | 214 | 79 |
| use_extended_range | 210 | 69 |
| unknown | 36 | 4 |

## Data Quality Warnings
- purchase_attempts exceed offer_selects; paywall funnel events are inconsistent and need instrumentation review
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
