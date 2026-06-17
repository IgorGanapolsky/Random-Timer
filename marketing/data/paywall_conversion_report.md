# Paywall Conversion Report

Generated: 2026-06-17T19:04:07+00:00
Window (days): 30

## Funnel
- Views: **544**
- Offer Selects: **10**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **1.8%**
- Select -> Purchase Attempt: **30.0%**
- Attempt -> Purchase Success: **33.3%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 64 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 64 | 43 |
| android | unknown | item_unavailable | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 9 | 2 | 1 | 22.2% | 50.0% |
| android | elite_tactical_monthly | 1 | 1 | 0 | 100.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical | 216 | 155 |
| android | elite_tactical_monthly | 211 | 135 |
| android | pro_base | 195 | 157 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 276 | 3 | 1 | 1.1% | 33.3% |
| voice_gate | 176 | 0 | 0 | 0.0% | 0.0% |
| unknown | 50 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 15 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 3 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **176** views and **0** purchase attempts.
- `unknown` had **50** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 2954 | 297 |
| max_seconds | 2824 | 313 |
| volume | 2172 | 212 |
| min_seconds | 1834 | 295 |
| sound_type | 1592 | 254 |
| repeat_enabled | 1231 | 283 |
| voice_callouts_enabled | 822 | 187 |
| vibration_enabled | 558 | 209 |
| repeat_rounds | 451 | 131 |
| voice_gender | 355 | 219 |
| use_extended_range | 301 | 161 |
| unknown | 55 | 3 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
