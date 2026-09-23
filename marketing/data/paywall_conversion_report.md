# Paywall Conversion Report

Generated: 2026-09-23T00:52:32+00:00
Window (days): 30

## Funnel
- Views: **52**
- Offer Selects: **4**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **7.7%**
- Select -> Purchase Attempt: **25.0%**
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
| android | elite_tactical | 4 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 57 | 55 |
| android | elite_tactical | 52 | 52 |
| android | elite_tactical_monthly | 52 | 52 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| unknown | 14 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- None

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2742 | 88 |
| max_seconds | 2461 | 117 |
| alarm_duration | 1911 | 116 |
| min_seconds | 1476 | 118 |
| sound_type | 1221 | 116 |
| voice_callouts_enabled | 781 | 71 |
| repeat_enabled | 678 | 111 |
| repeat_rounds | 314 | 67 |
| voice_gender | 279 | 99 |
| vibration_enabled | 221 | 83 |
| use_extended_range | 211 | 70 |
| unknown | 7 | 1 |

## Data Quality Warnings
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
