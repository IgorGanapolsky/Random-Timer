# Paywall Conversion Report

Generated: 2026-06-12T18:45:42+00:00
Window (days): 30

## Funnel
- Views: **551**
- Offer Selects: **20**
- Purchase Attempts: **6**
- Purchase Successes: **1**
- View -> Offer Select: **3.6%**
- Select -> Purchase Attempt: **30.0%**
- Attempt -> Purchase Success: **16.7%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 156 |
| user_cancelled | 6 |
| cancelled | 2 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 156 | 69 |
| android | unknown | user_cancelled | 4 | 1 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |
| android | unknown | item_unavailable | 2 | 1 |
| android | unknown | cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 12 | 3 | 1 | 25.0% | 33.3% |
| android | elite_tactical_monthly | 5 | 1 | 0 | 20.0% | 0.0% |
| android | pro_base | 3 | 1 | 0 | 33.3% | 0.0% |
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical_monthly | 274 | 140 |
| android | elite_tactical | 228 | 156 |
| android | pro_base | 202 | 157 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 277 | 3 | 1 | 1.1% | 33.3% |
| voice_gate | 182 | 0 | 0 | 0.0% | 0.0% |
| unknown | 40 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 16 | 2 | 0 | 12.5% | 0.0% |
| qualified_training_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 4 | 1 | 0 | 25.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **182** views and **0** purchase attempts.
- `unknown` had **40** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 2994 | 303 |
| max_seconds | 2989 | 321 |
| volume | 2292 | 215 |
| min_seconds | 1999 | 303 |
| sound_type | 1588 | 255 |
| repeat_enabled | 1243 | 293 |
| voice_callouts_enabled | 829 | 189 |
| vibration_enabled | 577 | 217 |
| repeat_rounds | 452 | 132 |
| voice_gender | 359 | 222 |
| use_extended_range | 304 | 164 |
| unknown | 88 | 5 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
