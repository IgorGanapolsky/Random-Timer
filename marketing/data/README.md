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

See also `docs/OPERATIONAL_RELIABILITY.md` and `docs/OBSERVABILITY.md`.
