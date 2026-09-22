# Paywall Conversion Report

Generated: 2026-09-22T00:54:16+00:00
Window (days): 30

## Funnel
- Views: **56**
- Offer Selects: **5**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **8.9%**
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
| android | pro_base | 57 | 55 |
| android | elite_tactical | 52 | 52 |
| android | elite_tactical_monthly | 52 | 52 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 15 | 0 | 0 | 0.0% | 0.0% |
| unknown | 15 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- None

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2796 | 90 |
| max_seconds | 2639 | 120 |
| alarm_duration | 1914 | 117 |
| min_seconds | 1587 | 120 |
| sound_type | 1231 | 117 |
| voice_callouts_enabled | 781 | 71 |
| repeat_enabled | 681 | 114 |
| repeat_rounds | 314 | 67 |
| voice_gender | 281 | 100 |
| vibration_enabled | 224 | 84 |
| use_extended_range | 211 | 70 |
| unknown | 7 | 1 |

## Data Quality Warnings
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
