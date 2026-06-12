# Paywall Conversion Report

Generated: 2026-06-12T13:27:00+00:00
Window (days): 30

## Funnel
- Views: **619**
- Offer Selects: **42**
- Purchase Attempts: **6**
- Purchase Successes: **1**
- View -> Offer Select: **6.8%**
- Select -> Purchase Attempt: **14.3%**
- Attempt -> Purchase Success: **16.7%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 216 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 216 | 92 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 14 | 3 | 1 | 21.4% | 33.3% |
| android | elite_tactical_monthly | 22 | 1 | 0 | 4.5% | 0.0% |
| android | pro_base | 6 | 1 | 0 | 16.7% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 363 | 153 |
| android | elite_tactical | 314 | 169 |
| android | pro_base | 255 | 170 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 293 | 3 | 1 | 1.0% | 33.3% |
| voice_gate | 210 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 30 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| qualified_training_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **210** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.
- `repeat_gate` had **30** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 3196 | 321 |
| max_seconds | 3118 | 339 |
| volume | 2336 | 228 |
| min_seconds | 2145 | 321 |
| sound_type | 1641 | 268 |
| repeat_enabled | 1331 | 310 |
| voice_callouts_enabled | 866 | 201 |
| vibration_enabled | 621 | 234 |
| repeat_rounds | 457 | 135 |
| voice_gender | 384 | 234 |
| use_extended_range | 325 | 175 |
| unknown | 88 | 5 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
