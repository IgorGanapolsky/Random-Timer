# Operational reliability contract

**Audience:** CEO, agents, CI, anyone interpreting automation output.

This document defines **how** we stay trustworthy in operations. It does **not** claim infallibility; it claims **disciplined process** so errors are visible, scoped, and fixable.

## 1. Ground truth vs proxy

Every quantitative claim MUST identify:

| Field | Meaning |
| --- | --- |
| **Source** | API name, SQL, file path, or UI surface |
| **Time window** | e.g. trailing 7d, snapshot `generated_at` |
| **Semantics** | What is included and excluded per vendor docs |

**Rule:** Never present a **proxy** (API subset, sampled page, PostHog distinct persons) as **store or ledger ground truth** without saying so.

**Examples:**

- Play `reviews.list` counts are **not** “public Play review totals.” Use `review_count_metric_id` in `executive_metrics.json` / `real_store_downloads` output.
- PostHog “installs” from `Application Installed` are **not** Play Console download units. Executive PostHog scalars map to `posthog.metric_field_ids` under `metric_bundle_id` `posthog_executive_pragmatic_live_hogql_v1`.
- Crashlytics **`fatal_events_in_window`** is **COUNT(\*)** of fatal rows in the BQ lookback window (canonical crash volume). **`fatal_events`** is the sum of crash counts in the **parsed top-issue sample** (see `metric_field_ids` — not a full-window total if many issue groups exist).
- **Public storefront version read-back** (`scripts/verify_public_store_versions.py`): iOS uses the **iTunes public lookup** `version` field (US storefront JSON — a public proxy, not a substitute for App Store Connect internal state). Android uses a **regex on the public Play HTML** (embedded `141` payload string — a fragile listing proxy, not Play Console track truth). Default expected version for automation is the **latest GitHub release tag** so integration-branch repo versions are not mistaken for “what must be live” in the US storefront.
- **Store ratings snapshot** (`scripts/store_ratings_snapshot.py`, workflow `store-ratings-snapshot.yml`): iOS **`average_rating_sample_mean`** is computed over the **App Store Connect `customerReviews` paginated sample** (`review_count_metric_id` = `asc_customer_reviews_api_paginated_sample_mean_v1`). Android uses **`androidpublisher.reviews.list`** (`google_play_androidpublisher_reviews_list_paginated_sample_mean_v1`), which is **not** the same as public Play lifetime totals. Treat JSON `semantics` fields as binding; a **zero-size sample** is valid output when the API returns no rows.

### Release verification tiers (binding)

"Shipped" and "publicly visible" are **distinct** states. Never conflate.

| Tier | Source | Lag after upload | Blocks `native-release`? |
|------|--------|-----------------|--------------------------|
| 0 — Uploaded / on track | Android Publisher API; ASC TestFlight builds API | Minutes | ✅ Yes — via `verify_release.py` |
| 1 — In review / approved | ASC `appStoreVersions.appStoreState` | Minutes | ✅ Yes — via `asc_poll_version_state.py` |
| 2 — Public storefront | iTunes lookup (US JSON); Play HTML `141` regex | **Hours to 24h+** | ❌ Never — `continue-on-error: true` |

- **Tier 0 + GitHub tag = shipped.** The release is correct and complete when `native-release.yml` exits green and the tag exists.
- **Tier 2 failures are propagation lag, not release failures.** Do not re-trigger the release pipeline because `public-store-version-readback.yml` fails or `verify_public_store_versions.py` times out.
- Use `store-release-watcher.yml` (cron every 30 min) for asynchronous Tier 2 monitoring.
- Full debug runbook: `.claude/skills/store-verify-ci.md`.

## 2. Evidence, not assertions

For repo state, CI, releases, and metrics:

- Prefer **reproducible proof**: command run, path, exit code, and **sanitized** excerpt of output or response body.
- Do **not** rely on unstated memory of prior sessions for “current” status.

## 3. Contradiction protocol

If human-observed reality **conflicts** with automation:

1. **Stop** treating the automation number as authoritative until reconciled.
2. **Re-read** vendor documentation for that endpoint.
3. **Re-run** the pipeline with the same inputs, or capture raw API response (redacted).
4. If still unclear, label the metric **unverified** and file a bug on semantics or labeling.

## 4. Explicit uncertainty

- Use **“not verified in this session”** or **“unknown”** when proof is missing.
- Do **not** fill gaps with plausible numbers or assumed API behavior.

## 5. Metric definitions and schema drift

When the meaning of a field changes:

- Add or update **`review_count_metric_id`** (or equivalent) and human **`note`** text.
- Update **`definitions`** in `executive_metrics_snapshot.py` so JSON is self-describing.
- Avoid silently reusing a field name for a different meaning.

## 6. Irreversible and spend actions

- **Git:** No force-push to shared branches unless the CEO explicitly requests it. Merge only with green required checks per `CLAUDE.md`.
- **Spend:** Respect the monthly cap in `AGENTS.md` / `CLAUDE.md`; document MTD estimate when reporting costs.
- **Releases / store:** Follow verification checklists in `AGENTS.md` (screenshots, build state, metadata).

## 7. Secrets

- Never commit tokens, PATs, or private keys. Rotate anything exposed in logs or chat.
- Verify `.env` key **names** and CI secret **names** exist before claiming “no access.”

## 8. CEO veto

The CEO may require explicit approval for any irreversible or high-blast-radius action. Agents must honor that when stated for a task.

---

**Canonical path:** `docs/OPERATIONAL_RELIABILITY.md`  
**Cursor rule:** `.cursor/rules/operational-reliability.mdc`  
**Cross-references:** `AGENTS.md`, `CLAUDE.md`
