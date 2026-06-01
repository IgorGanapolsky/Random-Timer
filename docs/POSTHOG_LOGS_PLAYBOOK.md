# PostHog Logs & billing observability playbook

Last updated: 2026-06-01.

This doc maps PostHog’s **Logs** product updates (alerts, saved views, easier ingestion) to **Random Tactical Timer** — a **native iOS/Android** app, not a PostHog JS site.

## How this helps us

| PostHog capability | Our use | ROI |
|--------------------|---------|-----|
| **Saved views / HogQL** | Recurring incidents: empty Play catalog, `FEATURE_NOT_SUPPORTED (-2)`, paywall leak | Faster MTTR on **$0 paywall conversion** |
| **Alerts (logs)** | CI/automation OTLP (`random-timer-automation`) | Catch billing regressions in scripts without reading Actions logs |
| **Alerts (events)** | `billing_product_not_found`, `billing_product_catalog_status` | Same checks via HogQL today — no JS “zero setup” on mobile |
| **Easier ingestion** | JS zero-setup **does not apply** to Kotlin/Swift | We use **structured `billing_*` events** now; OTLP later |
| **Traces (alpha)** | Future: link paywall → StoreKit/Play Billing spans | Planned; not wired in this repo yet |

**North star link:** paywall failures block **WQTU** and revenue. These queries surface **Play Billing -2** and empty catalogs before store version lag hides the issue.

## What we implemented in the repo

### Native Android (PostHog events)

- `billing_client_setup` — every Play Billing connection result (`billing_response_label`).
- `billing_product_query_retry` — transient SKU query retries before `billing_product_not_found`.
- `billing_diagnostic` — structured error companion on catalog failures.
- `billing_response_label` on `billing_product_not_found` (human-readable, not only `-2`).
- Product query **retry** (up to 3) for `SERVICE_DISCONNECTED`, `NETWORK_ERROR`, `SERVICE_UNAVAILABLE`, `FEATURE_NOT_SUPPORTED`.

### Repo automation

- **`marketing/data/posthog_observability.json`** — canonical HogQL saved queries + log-alert templates.
- **`scripts/posthog_observability_bootstrap.py`** — verifies queries live; optional `--apply-log-alerts`.
- **`marketing/data/posthog_observability_status.json`** — generated evidence (gitignored if sensitive; committed when only counts).

### Manual PostHog UI (5 minutes, one-time)

1. Open **Logs** → run HogQL from `posthog_observability.json` → **bookmark** each query (saved view).
2. **Activity / Trends** → alert on `billing_product_not_found` count **> 0** in 5 minutes, filter `distribution_channel = play_store`.
3. When enabling CI OTLP, set template `ci_billing_error_logs` to `enabled: true` and run bootstrap with `--apply-log-alerts`.

## Commands (evidence)

```bash
# Verify HogQL (requires POSTHOG_API_KEY + POSTHOG_PROJECT_ID in .env)
python3 scripts/posthog_observability_bootstrap.py

# Optional log alerts (POSTHOG_PERSONAL_API_KEY with logs scope)
python3 scripts/posthog_observability_bootstrap.py --apply-log-alerts
```

## Related docs

- `docs/POSTHOG_ANALYTICS.md` — event contract
- `docs/OBSERVABILITY.md` — stack status
- `scripts/paywall_conversion_report.py` — weekly funnel + billing breakdown
