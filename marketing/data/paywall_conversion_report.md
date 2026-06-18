# Paywall Conversion Report

Generated: 2026-06-18T13:27:08+00:00
Window (days): 30

## Funnel
- Views: **538**
- Offer Selects: **10**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **1.9%**
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
| android | elite_tactical | 191 | 134 |
| android | elite_tactical_monthly | 183 | 113 |
| android | pro_base | 172 | 136 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 272 | 3 | 1 | 1.1% | 33.3% |
| voice_gate | 176 | 0 | 0 | 0.0% | 0.0% |
| unknown | 49 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 1 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **176** views and **0** purchase attempts.
- `unknown` had **49** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 2840 | 270 |
| max_seconds | 2711 | 288 |
| volume | 1991 | 191 |
| min_seconds | 1780 | 270 |
| sound_type | 1448 | 227 |
| repeat_enabled | 1086 | 257 |
| voice_callouts_enabled | 713 | 166 |
| vibration_enabled | 443 | 188 |
| repeat_rounds | 355 | 110 |
| voice_gender | 311 | 193 |
| use_extended_range | 278 | 140 |
| unknown | 34 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
