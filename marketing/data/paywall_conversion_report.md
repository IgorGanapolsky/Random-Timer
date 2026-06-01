# Paywall Conversion Report

Generated: 2026-06-01T08:10:35+00:00
Window (days): 30

## Funnel
- Views: **531**
- Offer Selects: **56**
- Purchase Attempts: **4**
- Purchase Successes: **0**
- View -> Offer Select: **10.5%**
- Select -> Purchase Attempt: **7.1%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 405 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 405 | 176 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical_monthly | 41 | 1 | 0 | 2.4% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 491 | 176 |
| android | elite_tactical | 394 | 167 |
| android | pro_base | 236 | 143 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 247 | 1 | 0 | 0.4% | 0.0% |
| voice_gate | 166 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 38 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| sound_gate | 5 | 1 | 0 | 20.0% | 0.0% |
| qualified_training_gate | 5 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **166** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **38** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3290 | 331 |
| alarm_duration | 2641 | 304 |
| min_seconds | 2346 | 309 |
| volume | 2312 | 208 |
| unknown | 2013 | 22 |
| sound_type | 1781 | 259 |
| repeat_enabled | 1291 | 301 |
| voice_callouts_enabled | 783 | 184 |
| vibration_enabled | 588 | 210 |
| repeat_rounds | 396 | 116 |
| voice_gender | 347 | 215 |
| use_extended_range | 251 | 156 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
