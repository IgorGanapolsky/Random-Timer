# Marketing data snapshots

## `executive_metrics.json`

**What it is:** A JSON bundle of PostHog scalars (product), Play / App Store Connect snippets (when APIs succeed), and Crashlytics BigQuery summary (when the export has data).

**Do you need to do anything?**

- **No**, for day-to-day work. The file in git is a **sample** from the last run (local or CI). Read it as a snapshot, not a live dashboard.
- **Optional local refresh** (updates the file on disk): from the repo root, with `.env` / keys available:

  ```bash
  uv run python scripts/executive_metrics_snapshot.py
  ```

- **App Store Connect errors** (timeouts, etc.): the script **retries** a few times with a longer timeout. If ASC is still down or blocked, iOS store fields may be empty in that run—**re-run later**; you do not need to edit the JSON by hand.
- **Crashlytics shows “no tables yet”:** BigQuery tables are created when the Firebase → BigQuery export receives data. Until then, crash counts stay at zero in this file—**not** proof that the app has never crashed.

**Tighter “external user only” PostHog counts**

- New app builds tag `distribution_channel` and mark **TestFlight** and **non–Play-Store** Android installs as **internal** for analytics.
- For known PostHog **person IDs** to exclude (e.g. internal cohort), set:

  `POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS` = comma-separated UUIDs in **`.env`** (local) and as repository secret **`POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS`** for **`Executive metrics snapshot`** (`.github/workflows/executive-metrics.yml` passes it into the script).

**Finding person IDs to exclude (PostHog UI)**

1. PostHog → **Persons** (or open a person from **Activity** / an event stream).
2. Copy the **Person distinct ID** (UUID format) for each device or profile you want out of executive counts.
3. Paste comma-separated into `POSTHOG_EXECUTIVE_EXCLUDE_PERSON_IDS`. This is the only supported way to drop *your* devices from WQTU/install scalars; the script does not auto-detect names or “bot vs human.”

**Local Play / Crashlytics keys**

- **Play:** use `GOOGLE_PLAY_JSON_KEY` (raw JSON from the secret) or `GOOGLE_PLAY_JSON_KEY_PATH` (path to a file). If the path is wrong, the snapshot now fails with a clear “not a file” error instead of a JSON parse error.
- **Crashlytics BigQuery:** prefer `CRASHLYTICS_SERVICE_ACCOUNT_JSON` (same pattern as CI). If you use `GOOGLE_APPLICATION_CREDENTIALS`, the file must exist or the snapshot reports an explicit missing-file error.

See also `docs/OPERATIONAL_RELIABILITY.md` and `docs/OBSERVABILITY.md`.
