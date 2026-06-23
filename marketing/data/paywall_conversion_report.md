# Paywall Conversion Report

Generated: 2026-06-23T13:15:07+00:00
Window (days): 30

## Funnel
- Views: **525**
- Offer Selects: **10**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **1.9%**
- Select -> Purchase Attempt: **30.0%**
- Attempt -> Purchase Success: **33.3%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 57 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 57 | 37 |
| android | unknown | item_unavailable | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 9 | 2 | 1 | 22.2% | 50.0% |
| android | elite_tactical_monthly | 1 | 1 | 0 | 100.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 91 | 88 |
| android | elite_tactical | 89 | 86 |
| android | elite_tactical_monthly | 82 | 66 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 234 | 3 | 1 | 1.3% | 33.3% |
| voice_gate | 174 | 0 | 0 | 0.0% | 0.0% |
| unknown | 75 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 18 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **174** views and **0** purchase attempts.
- `unknown` had **75** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 2643 | 219 |
| alarm_duration | 2599 | 205 |
| volume | 1655 | 143 |
| min_seconds | 1539 | 204 |
| sound_type | 1196 | 169 |
| repeat_enabled | 745 | 195 |
| voice_callouts_enabled | 520 | 123 |
| vibration_enabled | 242 | 140 |
| voice_gender | 236 | 136 |
| use_extended_range | 236 | 100 |
| repeat_rounds | 199 | 68 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
