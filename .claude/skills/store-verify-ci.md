# Store Verify CI Skill

**Trigger:** `/store-verify`, session start before any release claim, whenever a public storefront read-back fails or times out.

## The Core Rule (read this first every session)

**"Shipped" = API verify + GitHub tag.  
"Publicly visible" = iTunes / Play HTML PASS — a lagging proxy, NOT a release gate.**

These are two different things. The native-release pipeline can succeed and produce a GitHub release tag even when `verify_public_store_versions.py` reports `VERSION_MISMATCH`. That is expected and correct.

---

## Truth Tiers (never conflate)

| Tier | Endpoint | Lag | Block release? |
|------|----------|-----|----------------|
| 0 — Uploaded | Android Publisher API tracks; ASC TestFlight builds | Minutes | ✅ Yes (via `verify_release.py`) |
| 1 — Submitted for review | ASC `appStoreState` (`WAITING_FOR_REVIEW`, `IN_REVIEW`) | Minutes | ✅ Yes (via `asc_poll_version_state.py`) |
| 2 — Public storefront | iTunes lookup; Play HTML `141` regex | **Hours to 24h+** | ❌ Never block release |

---

## Scripts

| Script | Purpose | Timeout |
|--------|---------|---------|
| `scripts/verify_release.py --wait` | Tier 0: API confirm build on track (Play) / TestFlight (ASC) | 600s (10 min) — OK to block |
| `scripts/asc/asc_poll_version_state.py --version X.Y.Z` | Tier 1: ASC review state | 60s poll, non-blocking read |
| `scripts/verify_public_store_versions.py` | Tier 2: public listing proxy | **≤120s** — never block native-release |
| `scripts/verify_play_public_listing.py` | Tier 2: Play HTML only | **≤60s** — watcher only |

---

## Workflows

| Workflow | Purpose | Should block? |
|----------|---------|---------------|
| `native-release.yml` / `verify-releases` job | Tier 0 + tag + submit | ✅ Blocks on Tier 0 |
| `native-release.yml` / Play public listing step | Tier 2 soft check | `continue-on-error: true` always |
| `public-store-version-readback.yml` | Tier 2 audit | `continue-on-error: true` on `workflow_run`; may fail on `workflow_dispatch` for manual audit |
| `store-release-watcher.yml` (cron `*/30 * * * *`) | Tier 2 propagation tracker | ❌ Never blocks; posts to GitHub Issue |

---

## Key Times (May 2026, from research)

- **Play public HTML** after production API: typically **hours**; can be same-day if Managed Publishing is off.
- **Managed Publishing**: approved changes sit until Console → **Publish changes**; after click, listing usually propagates within minutes.
- **iTunes lookup vs live App Store**: Apple has documented a **~24h delay** for the iTunes lookup endpoint to reflect the live storefront version.
- **ASC API**: authoritative within minutes of upload; use `appStoreState` not iTunes for CI decisions.

---

## Debug runbook (when store verify fails in CI)

```bash
# 1. Confirm what APIs say (authoritative)
python scripts/verify_release.py --platform both --version 1.X.Y --version-code NNNN --wait --timeout 60

# 2. Check ASC review state (iOS)
python scripts/asc/asc_poll_version_state.py --version 1.X.Y --json

# 3. Quick public sniff (1 poll, no wait — advisory only)
python scripts/verify_public_store_versions.py --expected-version 1.X.Y --timeout 10 --poll-interval 10

# 4. If Managed Publishing may be holding Play:
#    Console → Publishing overview → look for staged/pending changes → Publish changes

# 5. If Play listing still lagging after API shows completed:
#    Wait; re-run store-release-watcher via workflow_dispatch; do NOT re-run native-release
```

---

## Play Managed Publishing check

```bash
# Via Android Publisher API — check if there are unpublished edits
python - <<'EOF'
import json, os, sys
sys.path.insert(0, '.')
from scripts.verify_release import GooglePlayVerifier
v = GooglePlayVerifier()
v.authenticate()
# If edits().get() returns an open edit, Managed Publishing may be holding listing updates
EOF
```

---

## Do NOT do these

- ❌ Do not run `verify_public_store_versions.py` with `--timeout 900` or `1800` in a blocking pipeline step.
- ❌ Do not say "release failed" because iTunes lookup or Play HTML still shows the old version.
- ❌ Do not re-trigger `native-release.yml` because `public-store-version-readback.yml` failed.
- ❌ Do not claim "publicly visible" using only the API result.

---

## iOS App IDs

- App Store numeric ID: `6758355312`
- Bundle ID: `com.igorganapolsky.randomtimer`
- ASC App ID (internal): read from `scripts/asc/asc_client.py` or `asc_resolve_version.py` output

## Android

- Package: `com.iganapolsky.randomtimer`
- Service account: `GOOGLE_PLAY_JSON_KEY` (GitHub secret) → `/tmp/play-service-account.json` in CI

---

## Session start checklist

Before any release claim, run these in order:

```bash
# Step 1 — API truth (fast, authoritative)
gh release list -L 1
python scripts/verify_release.py --platform both --version $(gh release view --json tagName -q '.tagName[1:]') --wait --timeout 60 2>&1 | tail -10

# Step 2 — ASC state (iOS review queue)
python scripts/asc/asc_poll_version_state.py --version 1.X.Y --json 2>&1

# Step 3 — Public sniff (advisory only, short)
python scripts/verify_public_store_versions.py --expected-version 1.X.Y --timeout 30 --poll-interval 10 2>&1

# Step 4 — Revenue (always check before claiming $)
# Run PostHog HogQL via MCP: SELECT count() FROM events WHERE event='paywall_purchase_success' AND timestamp > now() - interval 7 day
```
