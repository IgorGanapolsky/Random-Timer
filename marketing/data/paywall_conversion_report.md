# Paywall Conversion Report

Generated: 2026-09-24T06:35:50+00:00
Window (days): 30

## Funnel
- Views: **55**
- Offer Selects: **4**
- Purchase Attempts: **2**
- Purchase Successes: **0**
- View -> Offer Select: **7.3%**
- Select -> Purchase Attempt: **50.0%**
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
| android | elite_tactical | 4 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 56 | 54 |
| android | elite_tactical | 52 | 52 |
| android | elite_tactical_monthly | 52 | 52 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 18 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 10 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 1 | 2 | 0 | 200.0% | 0.0% |

## Leaky Entry Points
- None

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| volume | 2636 | 87 |
| max_seconds | 2348 | 111 |
| alarm_duration | 1875 | 110 |
| min_seconds | 1437 | 113 |
| sound_type | 1208 | 115 |
| voice_callouts_enabled | 773 | 70 |
| repeat_enabled | 664 | 106 |
| repeat_rounds | 308 | 66 |
| voice_gender | 275 | 97 |
| vibration_enabled | 215 | 80 |
| use_extended_range | 210 | 69 |
| unknown | 30 | 3 |

## Data Quality Warnings
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
