# Paywall Conversion Report

Generated: 2026-08-16T00:24:01+00:00
Window (days): 30

## Funnel
- Views: **81**
- Offer Selects: **14**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **17.3%**
- Select -> Purchase Attempt: **21.4%**
- Attempt -> Purchase Success: **33.3%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 3 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | pro_base | 5 | 1 | 1 | 20.0% | 100.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 8 | 0 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| (none) | (none) | 0 | 0 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 42 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 28 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 2 | 0 | 200.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **42** views and **0** purchase attempts.
- `qualified_training_gate` had **28** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3023 | 56 |
| volume | 1553 | 26 |
| min_seconds | 1189 | 44 |
| sound_type | 132 | 38 |
| repeat_enabled | 124 | 46 |
| alarm_duration | 102 | 48 |
| unknown | 77 | 4 |
| voice_gender | 67 | 24 |
| vibration_enabled | 28 | 24 |
| use_extended_range | 5 | 2 |
| voice_callouts_enabled | 1 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
