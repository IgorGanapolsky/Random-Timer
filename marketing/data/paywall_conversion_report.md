# Paywall Conversion Report

Generated: 2026-06-14T07:51:25+00:00
Window (days): 30

## Funnel
- Views: **573**
- Offer Selects: **21**
- Purchase Attempts: **6**
- Purchase Successes: **1**
- View -> Offer Select: **3.7%**
- Select -> Purchase Attempt: **28.6%**
- Attempt -> Purchase Success: **16.7%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 68 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 68 | 45 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 13 | 3 | 1 | 23.1% | 33.3% |
| android | elite_tactical_monthly | 5 | 1 | 0 | 20.0% | 0.0% |
| android | pro_base | 3 | 1 | 0 | 33.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 264 | 140 |
| android | elite_tactical | 228 | 156 |
| android | pro_base | 203 | 158 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 279 | 3 | 1 | 1.1% | 33.3% |
| voice_gate | 182 | 0 | 0 | 0.0% | 0.0% |
| unknown | 58 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| qualified_training_gate | 14 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **182** views and **0** purchase attempts.
- `unknown` had **58** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3239 | 319 |
| alarm_duration | 2991 | 301 |
| volume | 2364 | 216 |
| min_seconds | 2239 | 302 |
| sound_type | 1600 | 258 |
| repeat_enabled | 1246 | 289 |
| voice_callouts_enabled | 830 | 190 |
| vibration_enabled | 571 | 215 |
| repeat_rounds | 452 | 132 |
| voice_gender | 361 | 222 |
| use_extended_range | 306 | 164 |
| unknown | 70 | 4 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
