# Paywall Conversion Report

Generated: 2026-08-22T06:13:40+00:00
Window (days): 30

## Funnel
- Views: **76**
- Offer Selects: **14**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **18.4%**
- Select -> Purchase Attempt: **14.3%**
- Attempt -> Purchase Success: **50.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 26 |
| user_cancelled | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 26 | 5 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | pro_base | 5 | 1 | 1 | 20.0% | 100.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
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
| qualified_training_gate | 24 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **42** views and **0** purchase attempts.
- `qualified_training_gate` had **24** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2716 | 60 |
| volume | 1728 | 23 |
| min_seconds | 1144 | 48 |
| sound_type | 135 | 38 |
| repeat_enabled | 110 | 47 |
| alarm_duration | 93 | 46 |
| voice_gender | 61 | 25 |
| unknown | 36 | 2 |
| vibration_enabled | 34 | 28 |
| use_extended_range | 2 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
