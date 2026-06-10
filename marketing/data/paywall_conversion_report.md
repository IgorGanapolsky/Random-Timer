# Paywall Conversion Report

Generated: 2026-06-10T17:11:33+00:00
Window (days): 30

## Funnel
- Views: **679**
- Offer Selects: **55**
- Purchase Attempts: **5**
- Purchase Successes: **0**
- View -> Offer Select: **8.1%**
- Select -> Purchase Attempt: **9.1%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| (none) | 0 |

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
| android | elite_tactical | 15 | 2 | 0 | 13.3% | 0.0% |
| android | elite_tactical_monthly | 33 | 1 | 0 | 3.0% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 431 | 166 |
| android | elite_tactical | 375 | 180 |
| android | pro_base | 263 | 172 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 310 | 2 | 0 | 0.7% | 0.0% |
| voice_gate | 230 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 35 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 10 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **230** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **35** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3289 | 345 |
| alarm_duration | 3091 | 323 |
| volume | 2207 | 223 |
| min_seconds | 2135 | 325 |
| sound_type | 1513 | 263 |
| repeat_enabled | 1364 | 313 |
| voice_callouts_enabled | 829 | 196 |
| vibration_enabled | 638 | 237 |
| repeat_rounds | 432 | 127 |
| voice_gender | 378 | 231 |
| use_extended_range | 307 | 171 |
| unknown | 115 | 6 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status

## Query Diagnostics
- Query errors: **1**
- Last error: `request_error: HTTPSConnectionPool(host='us.posthog.com', port=443): Read timed out. (read timeout=90.0)`
