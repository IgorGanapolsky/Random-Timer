# Paywall Conversion Report

Generated: 2026-06-19T01:29:20+00:00
Window (days): 30

## Funnel
- Views: **518**
- Offer Selects: **10**
- Purchase Attempts: **3**
- Purchase Successes: **1**
- View -> Offer Select: **1.9%**
- Select -> Purchase Attempt: **30.0%**
- Attempt -> Purchase Success: **33.3%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 63 |
| item_unavailable | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 63 | 42 |
| android | unknown | item_unavailable | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| android | elite_tactical | 9 | 2 | 1 | 22.2% | 50.0% |
| android | elite_tactical_monthly | 1 | 1 | 0 | 100.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | elite_tactical | 146 | 112 |
| android | elite_tactical_monthly | 138 | 91 |
| android | pro_base | 135 | 114 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| range_gate | 258 | 3 | 1 | 1.2% | 33.3% |
| voice_gate | 176 | 0 | 0 | 0.0% | 0.0% |
| unknown | 43 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| setup_upgrade_cta | 12 | 0 | 0 | 0.0% | 0.0% |
| sound_arsenal_gate | 8 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 1 | 0 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `voice_gate` had **176** views and **0** purchase attempts.
- `unknown` had **43** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| alarm_duration | 2717 | 237 |
| max_seconds | 2432 | 256 |
| volume | 1741 | 168 |
| min_seconds | 1566 | 239 |
| sound_type | 1325 | 197 |
| repeat_enabled | 933 | 225 |
| voice_callouts_enabled | 622 | 145 |
| vibration_enabled | 353 | 163 |
| repeat_rounds | 288 | 90 |
| voice_gender | 275 | 165 |
| use_extended_range | 257 | 121 |
| unknown | 34 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
