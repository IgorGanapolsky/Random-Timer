# Paywall Conversion Report

Generated: 2026-05-30T12:29:09+00:00
Window (days): 30

## Funnel
- Views: **514**
- Offer Selects: **57**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **11.1%**
- Select -> Purchase Attempt: **8.8%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 5 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | user_cancelled | 4 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical_monthly | 42 | 1 | 0 | 2.4% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 496 | 173 |
| android | elite_tactical | 391 | 164 |
| android | pro_base | 233 | 140 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 237 | 1 | 0 | 0.4% | 0.0% |
| voice_gate | 158 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 39 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| sound_gate | 5 | 2 | 0 | 40.0% | 0.0% |
| setup_upgrade_cta | 4 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 3 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **158** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **39** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3090 | 324 |
| unknown | 2615 | 24 |
| alarm_duration | 2555 | 297 |
| min_seconds | 2307 | 301 |
| volume | 2121 | 204 |
| sound_type | 1770 | 255 |
| repeat_enabled | 1253 | 293 |
| voice_callouts_enabled | 773 | 181 |
| vibration_enabled | 581 | 207 |
| repeat_rounds | 396 | 116 |
| voice_gender | 340 | 211 |
| use_extended_range | 245 | 153 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
