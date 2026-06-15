# Paywall Conversion Report

Generated: 2026-06-15T14:23:56+00:00
Window (days): 30

## Funnel
- Views: **562**
- Offer Selects: **18**
- Purchase Attempts: **6**
- Purchase Successes: **1**
- View -> Offer Select: **3.2%**
- Select -> Purchase Attempt: **33.3%**
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
| android | elite_tactical | 12 | 3 | 1 | 25.0% | 33.3% |
| android | elite_tactical_monthly | 5 | 1 | 0 | 20.0% | 0.0% |
| android | pro_base | 1 | 1 | 0 | 100.0% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 256 | 138 |
| android | elite_tactical | 228 | 156 |
| android | pro_base | 203 | 158 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 277 | 3 | 1 | 1.1% | 33.3% |
| voice_gate | 182 | 0 | 0 | 0.0% | 0.0% |
| unknown | 51 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 14 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 14 | 2 | 0 | 14.3% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **182** views and **0** purchase attempts.
- `unknown` had **51** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3097 | 317 |
| alarm_duration | 2991 | 300 |
| volume | 2228 | 215 |
| min_seconds | 2101 | 300 |
| sound_type | 1597 | 256 |
| repeat_enabled | 1246 | 288 |
| voice_callouts_enabled | 828 | 189 |
| vibration_enabled | 567 | 213 |
| repeat_rounds | 452 | 132 |
| voice_gender | 359 | 221 |
| use_extended_range | 305 | 163 |
| unknown | 70 | 4 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
