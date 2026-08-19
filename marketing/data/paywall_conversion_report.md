# Paywall Conversion Report

Generated: 2026-08-19T06:16:35+00:00
Window (days): 30

## Funnel
- Views: **82**
- Offer Selects: **14**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **17.1%**
- Select -> Purchase Attempt: **21.4%**
- Attempt -> Purchase Success: **33.3%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 26 |
| user_cancelled | 3 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 26 | 5 |
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
| unknown | 44 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 27 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 2 | 0 | 200.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **44** views and **0** purchase attempts.
- `qualified_training_gate` had **27** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3320 | 63 |
| volume | 1922 | 27 |
| min_seconds | 1321 | 51 |
| sound_type | 150 | 42 |
| repeat_enabled | 130 | 50 |
| alarm_duration | 104 | 51 |
| voice_gender | 78 | 29 |
| unknown | 77 | 4 |
| vibration_enabled | 34 | 28 |
| use_extended_range | 5 | 2 |
| voice_callouts_enabled | 1 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
