# Paywall Conversion Report

Generated: 2026-06-11T18:49:19+00:00
Window (days): 30

## Funnel
- Views: **681**
- Offer Selects: **56**
- Purchase Attempts: **6**
- Purchase Successes: **1**
- View -> Offer Select: **8.2%**
- Select -> Purchase Attempt: **10.7%**
- Attempt -> Purchase Success: **16.7%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 234 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 234 | 101 |
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
| android | elite_tactical_monthly | 424 | 166 |
| android | elite_tactical | 374 | 181 |
| android | pro_base | 266 | 175 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 305 | 3 | 1 | 1.0% | 33.3% |
| voice_gate | 230 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| qualified_training_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **230** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 3185 | 329 |
| max_seconds | 3138 | 348 |
| volume | 2335 | 230 |
| min_seconds | 2155 | 328 |
| sound_type | 1580 | 269 |
| repeat_enabled | 1385 | 319 |
| voice_callouts_enabled | 852 | 200 |
| vibration_enabled | 645 | 242 |
| repeat_rounds | 442 | 131 |
| voice_gender | 388 | 236 |
| use_extended_range | 321 | 176 |
| unknown | 88 | 5 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
