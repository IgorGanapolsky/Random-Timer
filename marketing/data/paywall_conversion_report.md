# Paywall Conversion Report

Generated: 2026-06-09T19:58:03+00:00
Window (days): 30

## Funnel
- Views: **658**
- Offer Selects: **51**
- Purchase Attempts: **4**
- Purchase Successes: **0**
- View -> Offer Select: **7.8%**
- Select -> Purchase Attempt: **7.8%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 257 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 257 | 113 |
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
| android | elite_tactical_monthly | 435 | 167 |
| android | elite_tactical | 375 | 180 |
| android | pro_base | 264 | 173 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 303 | 1 | 0 | 0.3% | 0.0% |
| voice_gate | 226 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 35 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| qualified_training_gate | 10 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |
| setup_upgrade_cta | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **226** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **35** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3311 | 344 |
| alarm_duration | 3089 | 321 |
| volume | 2207 | 223 |
| min_seconds | 2109 | 322 |
| sound_type | 1513 | 263 |
| repeat_enabled | 1366 | 315 |
| voice_callouts_enabled | 831 | 197 |
| vibration_enabled | 638 | 237 |
| repeat_rounds | 432 | 127 |
| voice_gender | 378 | 231 |
| use_extended_range | 307 | 171 |
| unknown | 115 | 6 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
