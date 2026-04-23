# Paywall Conversion Report

Generated: 2026-04-23T15:20:19+00:00
Window (days): 30

## Funnel
- Views: **783**
- Offer Selects: **63**
- Purchase Attempts: **84**
- Purchase Successes: **1**
- View -> Offer Select: **8.1%**
- Select -> Purchase Attempt: **133.3%**
- Attempt -> Purchase Success: **1.2%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 39 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| setup_upgrade_cta | 527 | 0 | 0 | 0.0% | 0.0% |
| unknown | 159 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 66 | 43 | 1 | 65.1% | 2.3% |
| range_gate | 31 | 41 | 0 | 132.3% | 0.0% |

## Leaky Entry Points
- `setup_upgrade_cta` had **527** views and **0** purchase attempts.
- `unknown` had **159** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 35320 | 605 |

## Data Quality Warnings
- purchase_attempts exceed offer_selects; paywall funnel events are inconsistent and need instrumentation review
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
