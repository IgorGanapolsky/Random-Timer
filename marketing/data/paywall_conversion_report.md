# Paywall Conversion Report

Generated: 2026-06-06T01:13:41+00:00
Window (days): 30

## Funnel
- Views: **653**
- Offer Selects: **49**
- Purchase Attempts: **4**
- Purchase Successes: **0**
- View -> Offer Select: **7.5%**
- Select -> Purchase Attempt: **8.2%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 298 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 298 | 131 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical_monthly | 33 | 1 | 0 | 3.0% | 0.0% |
| android | elite_tactical | 9 | 1 | 0 | 11.1% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 434 | 162 |
| android | elite_tactical | 370 | 169 |
| android | pro_base | 250 | 157 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 299 | 1 | 0 | 0.3% | 0.0% |
| voice_gate | 230 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 54 | 0 | 0 | 0.0% | 0.0% |
| unknown | 36 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 24 | 2 | 0 | 8.3% | 0.0% |
| sound_gate | 5 | 1 | 0 | 20.0% | 0.0% |
| qualified_training_gate | 5 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **230** views and **0** purchase attempts.
- `repeat_gate` had **54** views and **0** purchase attempts.
- `unknown` had **36** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3543 | 328 |
| alarm_duration | 2796 | 307 |
| min_seconds | 2349 | 311 |
| volume | 2167 | 211 |
| repeat_enabled | 1304 | 301 |
| sound_type | 1298 | 249 |
| voice_callouts_enabled | 755 | 184 |
| vibration_enabled | 612 | 220 |
| unknown | 597 | 10 |
| repeat_rounds | 394 | 115 |
| voice_gender | 356 | 217 |
| use_extended_range | 265 | 159 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
