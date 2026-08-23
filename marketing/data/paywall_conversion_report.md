# Paywall Conversion Report

Generated: 2026-08-23T18:11:29+00:00
Window (days): 30

## Funnel
- Views: **77**
- Offer Selects: **15**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **19.5%**
- Select -> Purchase Attempt: **13.3%**
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
| android | elite_tactical | 9 | 0 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 1 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| (none) | (none) | 0 | 0 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 41 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 26 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **41** views and **0** purchase attempts.
- `qualified_training_gate` had **26** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2858 | 63 |
| volume | 1708 | 23 |
| min_seconds | 1124 | 47 |
| sound_type | 136 | 38 |
| repeat_enabled | 109 | 46 |
| alarm_duration | 88 | 45 |
| voice_gender | 51 | 23 |
| unknown | 36 | 2 |
| vibration_enabled | 32 | 25 |
| use_extended_range | 4 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
