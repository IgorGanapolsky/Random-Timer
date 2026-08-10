# Paywall Conversion Report

Generated: 2026-08-10T06:40:29+00:00
Window (days): 30

## Funnel
- Views: **66**
- Offer Selects: **16**
- Purchase Attempts: **3**
- Purchase Successes: **2**
- View -> Offer Select: **24.2%**
- Select -> Purchase Attempt: **18.8%**
- Attempt -> Purchase Success: **66.7%**

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
| android | pro_base | 7 | 2 | 2 | 28.6% | 100.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 8 | 0 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 1 | 1 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| qualified_training_gate | 27 | 0 | 0 | 0.0% | 0.0% |
| unknown | 26 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 1 | 1 | 25.0% | 100.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 1 | 0 | 100.0% | 0.0% |

## Leaky Entry Points
- `qualified_training_gate` had **27** views and **0** purchase attempts.
- `unknown` had **26** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2978 | 55 |
| volume | 1825 | 27 |
| min_seconds | 1331 | 42 |
| sound_type | 159 | 42 |
| repeat_enabled | 122 | 45 |
| repeat_rounds | 108 | 1 |
| alarm_duration | 97 | 48 |
| voice_gender | 77 | 28 |
| unknown | 41 | 2 |
| vibration_enabled | 30 | 25 |
| use_extended_range | 12 | 3 |
| voice_callouts_enabled | 8 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- purchase failures are dominated by user_cancelled; prioritize pricing, plan default, and purchase-sheet value proof before assuming a store outage
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
