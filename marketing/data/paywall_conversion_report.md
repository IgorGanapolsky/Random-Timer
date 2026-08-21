# Paywall Conversion Report

Generated: 2026-08-21T00:24:02+00:00
Window (days): 30

## Funnel
- Views: **80**
- Offer Selects: **14**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **17.5%**
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
| unknown | 43 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 26 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 2 | 0 | 200.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **43** views and **0** purchase attempts.
- `qualified_training_gate` had **26** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2679 | 60 |
| volume | 1738 | 24 |
| min_seconds | 1113 | 48 |
| sound_type | 130 | 37 |
| repeat_enabled | 109 | 46 |
| alarm_duration | 93 | 46 |
| voice_gender | 62 | 25 |
| unknown | 59 | 3 |
| vibration_enabled | 32 | 26 |
| use_extended_range | 2 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
