# Paywall Conversion Report

Generated: 2026-06-10T13:29:02+00:00
Window (days): 30

## Funnel
- Views: **664**
- Offer Selects: **51**
- Purchase Attempts: **4**
- Purchase Successes: **0**
- View -> Offer Select: **7.7%**
- Select -> Purchase Attempt: **7.8%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 255 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 255 | 112 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical_monthly | 33 | 1 | 0 | 3.0% | 0.0% |
| android | elite_tactical | 11 | 1 | 0 | 9.1% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 428 | 166 |
| android | elite_tactical | 375 | 180 |
| android | pro_base | 263 | 172 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 305 | 1 | 0 | 0.3% | 0.0% |
| voice_gate | 230 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 35 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| qualified_training_gate | 10 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |
| setup_upgrade_cta | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **230** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **35** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3284 | 344 |
| alarm_duration | 3090 | 322 |
| volume | 2207 | 223 |
| min_seconds | 2118 | 323 |
| sound_type | 1513 | 263 |
| repeat_enabled | 1364 | 313 |
| voice_callouts_enabled | 829 | 196 |
| vibration_enabled | 638 | 237 |
| repeat_rounds | 432 | 127 |
| voice_gender | 376 | 230 |
| use_extended_range | 307 | 171 |
| unknown | 115 | 6 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
