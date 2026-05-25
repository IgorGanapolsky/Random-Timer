# Paywall Conversion Report

Generated: 2026-05-25T22:47:44+00:00
Window (days): 30

## Funnel
- Views: **372**
- Offer Selects: **63**
- Purchase Attempts: **6**
- Purchase Successes: **0**
- View -> Offer Select: **16.9%**
- Select -> Purchase Attempt: **9.5%**
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
| ios | com.iganapolsky.randomtimer.elite | 0 | 2 | 0 | 0.0% | 0.0% |
| android | elite_tactical_monthly | 48 | 1 | 0 | 2.1% | 0.0% |
| android | elite_tactical | 8 | 1 | 0 | 12.5% | 0.0% |
| android | pro_base | 7 | 1 | 0 | 14.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 509 | 157 |
| android | elite_tactical | 367 | 141 |
| android | pro_base | 209 | 117 |
| android | unknown | 177 | 105 |
| ios | unknown | 9 | 4 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 159 | 1 | 0 | 0.6% | 0.0% |
| voice_gate | 89 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 50 | 0 | 0 | 0.0% | 0.0% |
| unknown | 34 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 18 | 2 | 0 | 11.1% | 0.0% |
| setup_upgrade_cta | 16 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 5 | 3 | 0 | 60.0% | 0.0% |
| qualified_training_gate | 2 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **89** views and **0** purchase attempts.
- `repeat_gate` had **50** views and **0** purchase attempts.
- `unknown` had **34** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 4022 | 33 |
| max_seconds | 2638 | 281 |
| alarm_duration | 2053 | 258 |
| min_seconds | 2010 | 262 |
| sound_type | 1684 | 230 |
| volume | 1611 | 175 |
| repeat_enabled | 1079 | 250 |
| voice_callouts_enabled | 707 | 155 |
| vibration_enabled | 529 | 179 |
| repeat_rounds | 393 | 116 |
| voice_gender | 322 | 198 |
| use_extended_range | 217 | 139 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
