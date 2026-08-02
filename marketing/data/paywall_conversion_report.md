# Paywall Conversion Report

Generated: 2026-08-02T12:31:53+00:00
Window (days): 30

## Funnel
- Views: **42**
- Offer Selects: **4**
- Purchase Attempts: **2**
- Purchase Successes: **1**
- View -> Offer Select: **9.5%**
- Select -> Purchase Attempt: **50.0%**
- Attempt -> Purchase Success: **50.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 1 |
| user_cancelled | 1 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 1 | 1 |
| android | unknown | failed | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | pro_base | 2 | 1 | 1 | 50.0% | 100.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 2 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 2 | 2 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| qualified_training_gate | 22 | 0 | 0 | 0.0% | 0.0% |
| unknown | 17 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 1 | 1 | 50.0% | 100.0% |
| sound_gate | 1 | 1 | 0 | 100.0% | 0.0% |

## Leaky Entry Points
- `qualified_training_gate` had **22** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2617 | 44 |
| volume | 1230 | 18 |
| min_seconds | 1063 | 36 |
| repeat_rounds | 108 | 1 |
| sound_type | 103 | 30 |
| repeat_enabled | 78 | 31 |
| alarm_duration | 74 | 41 |
| unknown | 64 | 3 |
| voice_gender | 63 | 21 |
| vibration_enabled | 22 | 17 |
| use_extended_range | 10 | 2 |
| voice_callouts_enabled | 8 | 2 |

## Data Quality Warnings
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
