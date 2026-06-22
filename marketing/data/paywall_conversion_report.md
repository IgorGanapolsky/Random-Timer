# Paywall Conversion Report

Generated: 2026-06-22T01:27:09+00:00
Window (days): 30

## Funnel
- Views: **511**
- Offer Selects: **10**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **2.0%**
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
| android | pro_base | 97 | 94 |
| android | elite_tactical | 95 | 92 |
| android | elite_tactical_monthly | 88 | 72 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 240 | 3 | 1 | 1.2% | 33.3% |
| voice_gate | 174 | 0 | 0 | 0.0% | 0.0% |
| unknown | 55 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 18 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **174** views and **0** purchase attempts.
- `unknown` had **55** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 2642 | 213 |
| max_seconds | 2479 | 228 |
| volume | 1710 | 150 |
| min_seconds | 1517 | 213 |
| sound_type | 1234 | 178 |
| repeat_enabled | 807 | 204 |
| voice_callouts_enabled | 551 | 130 |
| vibration_enabled | 275 | 146 |
| voice_gender | 245 | 144 |
| use_extended_range | 242 | 106 |
| repeat_rounds | 227 | 75 |
| unknown | 18 | 1 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
