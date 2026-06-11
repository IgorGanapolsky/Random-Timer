# Paywall Conversion Report

Generated: 2026-06-11T13:39:20+00:00
Window (days): 30

## Funnel
- Views: **675**
- Offer Selects: **56**
- Purchase Attempts: **6**
- Purchase Successes: **1**
- View -> Offer Select: **8.3%**
- Select -> Purchase Attempt: **10.7%**
- Attempt -> Purchase Success: **16.7%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 245 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 245 | 107 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 16 | 3 | 1 | 18.8% | 33.3% |
| android | elite_tactical_monthly | 33 | 1 | 0 | 3.0% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 424 | 165 |
| android | elite_tactical | 374 | 180 |
| android | pro_base | 264 | 173 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 307 | 3 | 1 | 1.0% | 33.3% |
| voice_gate | 230 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 33 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 11 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **230** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **33** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3107 | 343 |
| alarm_duration | 3084 | 322 |
| volume | 2286 | 224 |
| min_seconds | 2134 | 323 |
| sound_type | 1514 | 262 |
| repeat_enabled | 1362 | 313 |
| voice_callouts_enabled | 828 | 196 |
| vibration_enabled | 638 | 237 |
| repeat_rounds | 430 | 127 |
| voice_gender | 377 | 230 |
| use_extended_range | 310 | 172 |
| unknown | 88 | 5 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
