# Play compliance artifacts (optional)

## `play_data_safety.csv`

Export your **Data Safety** answers from Play Console as CSV (see [Google Help](https://support.google.com/googleplay/android-developer/answer/10787469)), or maintain a CSV that matches Google’s current template.

- **Commit this file here** if you want the **Play Data Safety upload** workflow to use the repo copy.
- **Or** omit the file and store the entire CSV body in the GitHub Actions secret **`PLAY_DATA_SAFETY_CSV`** instead (mind secret size limits).

Upload is performed by `scripts/play_data_safety_upload.py` (Tier A — no browser).

**Do not** commit service account JSON; use `GOOGLE_PLAY_JSON_KEY` in CI secrets only.
