# Paywall Conversion Report

Generated: 2026-06-21T18:43:53+00:00
Window (days): 30

## Funnel
- Views: **517**
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
| android | elite_tactical | 107 | 95 |
| android | pro_base | 105 | 97 |
| android | elite_tactical_monthly | 100 | 75 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 244 | 3 | 1 | 1.2% | 33.3% |
| voice_gate | 176 | 0 | 0 | 0.0% | 0.0% |
| unknown | 55 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 18 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **176** views and **0** purchase attempts.
- `unknown` had **55** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 2642 | 216 |
| max_seconds | 2514 | 232 |
| volume | 1711 | 151 |
| min_seconds | 1538 | 216 |
| sound_type | 1236 | 179 |
| repeat_enabled | 811 | 205 |
| voice_callouts_enabled | 551 | 130 |
| vibration_enabled | 275 | 146 |
| voice_gender | 247 | 146 |
| use_extended_range | 242 | 106 |
| repeat_rounds | 227 | 75 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
