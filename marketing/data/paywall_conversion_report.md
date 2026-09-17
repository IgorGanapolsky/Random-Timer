# Paywall Conversion Report

Generated: 2026-09-17T18:25:42+00:00
Window (days): 30

## Funnel
- Views: **54**
- Offer Selects: **5**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **9.3%**
- Select -> Purchase Attempt: **20.0%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 1 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 5 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 55 | 53 |
| android | elite_tactical | 50 | 50 |
| android | elite_tactical_monthly | 49 | 49 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| unknown | 15 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 13 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- None

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2566 | 110 |
| volume | 1925 | 78 |
| alarm_duration | 1803 | 106 |
| min_seconds | 1511 | 108 |
| sound_type | 1141 | 104 |
| voice_callouts_enabled | 751 | 65 |
| repeat_enabled | 655 | 107 |
| repeat_rounds | 299 | 62 |
| voice_gender | 263 | 90 |
| vibration_enabled | 214 | 77 |
| use_extended_range | 199 | 65 |
| unknown | 7 | 1 |

## Data Quality Warnings
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
