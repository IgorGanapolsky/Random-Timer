# Play compliance artifacts

## Data Safety source of truth

`play_data_safety_source.json` is the repo-owned declaration source. It maps app evidence to Google Play Data Safety answers:

- analytics/app interactions
- Crashlytics crash logs
- diagnostics/performance
- Firebase/PostHog device or app-instance identifiers
- purchase history for Pro entitlement state

`scripts/generate_play_data_safety_csv.py` patches Google's official sample/export CSV shape, writes `play_data_safety.csv`, and writes `play_data_safety_evidence.json`.

## Upload order

The **Play Data Safety upload** workflow uses this order:

1. `PLAY_DATA_SAFETY_CSV` secret, if present.
2. committed `marketing/compliance/play_data_safety.csv`, if present.
3. generated CSV from `marketing/compliance/play_data_safety_source.json`.

Upload is performed by `scripts/play_data_safety_upload.py` through the Android Publisher API.

**Do not** commit service account JSON; use `GOOGLE_PLAY_JSON_KEY` in CI secrets only.
