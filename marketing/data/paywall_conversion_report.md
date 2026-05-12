# Paywall Conversion Report

Generated: 2026-05-11T14:18:45+00:00
Window (days): 30

## Funnel
- Views: **333**
- Offer Selects: **82**
- Purchase Attempts: **12**
- Purchase Successes: **0**
- View -> Offer Select: **24.6%**
- Select -> Purchase Attempt: **14.6%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| user_cancelled | 10 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| setup_upgrade_cta | 232 | 0 | 0 | 0.0% | 0.0% |
| unknown | 49 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 41 | 3 | 0 | 7.3% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 5 | 9 | 0 | 180.0% | 0.0% |

## Leaky Entry Points
- `setup_upgrade_cta` had **232** views and **0** purchase attempts.
- `unknown` had **49** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| unknown | 22802 | 356 |
| sound_type | 1030 | 83 |
| alarm_duration | 932 | 80 |
| max_seconds | 778 | 90 |
| min_seconds | 753 | 82 |
| volume | 520 | 56 |
| repeat_enabled | 261 | 77 |
| voice_callouts_enabled | 257 | 52 |
| voice_gender | 107 | 61 |
| repeat_rounds | 100 | 35 |
| use_extended_range | 87 | 42 |
| vibration_enabled | 60 | 45 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- settings_changed is still dominated by unknown setting_name rows in live data
