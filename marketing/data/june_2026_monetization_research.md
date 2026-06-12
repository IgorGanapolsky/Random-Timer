---
generated_at: 2026-06-03T19:43:56Z
source: posthog_execute_sql + internal_json + web_research_fallback
window_primary: trailing 7d and 30d (UTC, PostHog project timezone)
reliability_contract_doc: docs/OPERATIONAL_RELIABILITY.md
issue_ref: https://github.com/IgorGanapolsky/Random-Timer/issues/1684
external_research: WebSearch fallback (PERPLEXITY_API_KEY not present in .env)
---

# June 2026 Monetization Research — Random Tactical Timer

**App:** Random Tactical Timer (`com.iganapolsky.randomtimer`) — Android + iOS interval timer for tactical / MMA-style training.  
**North Star:** WQTU (≥3 `timer_completed` / person / trailing 7d).  
**Business goal:** $100/day after-tax from app sales (not claimed achievable in 30 days).  
**Budget:** $20 USD/month external spend cap.

---

## Executive summary

- **Revenue is effectively zero today.** PostHog (30d, queried 2026-06-03 UTC): **0** `paywall_purchase_success`, **4** `paywall_purchase_attempt`, **172** distinct paywall viewers, **375** `paywall_viewed` events. Executive proxy revenue is **$0/day** vs **$100/day** target (`marketing/data/executive_metrics.json`).
- **WQTU is far below the June 30 target (25).** Live WQTU = **4** (7d); checkpoint history peaked ~11 in mid-May and is declining. Product value exists (WAU **212**, DAU **48**) but qualified training depth is thin.
- **Android billing is the P0 blocker, not pricing psychology.** Play Console catalog readback is **ok** (`marketing/data/play_iap_catalog.json`), but client telemetry on **1.3.50** shows **0** `billing_product_catalog_status` and **5** `billing_diagnostic` rows with `product_details_supported=false` / response **-2** (`FEATURE_NOT_SUPPORTED`). Catalog status 30d: **20** `ok` vs **299** `empty` vs **36** other — paywall cannot monetize at scale until `ok` dominates on the production cohort.
- **Distribution is split-brain.** Play API reports **1.3.50** (VC `1780500214`); public listing still **1.3.43**. iOS **1.3.51** is in repo but **not shipped** — Android monetization fixes must pair with iOS release to capture iOS training usage (e.g. **1.3.42** iOS had **66** `timer_completed` in 7d vs **1** on latest Android cohort).
- **External benchmarks (2026) say Health & Fitness median D35 download-to-paid ≈ 2.9%** (top quartile >6.2%) — achievable only *after* billing works, listing is current, and paywall sees a loaded catalog. **$100/day is a 12–18+ month outcome** for a solo/indie app at current MAU unless conversion and installs step-change; do not promise otherwise.

---

## What data proves today

| Metric | Window | Value | Source / notes |
|--------|--------|-------|----------------|
| WQTU | 7d | **4** | PostHog HogQL canonical query; target Q2 **25** |
| DAU / WAU | 30d | **48** / **212** | `marketing/data/wqtu_health.json` |
| `timer_completed` abandon rate | 30d | **68.8%** (652/2091 started) | `wqtu_health.json` |
| Paywall views (events / users) | 30d | **375** / **172** | PostHog `execute-sql` |
| Purchase attempts / success | 30d | **4** / **0** | PostHog; **not** store ledger |
| Paywall funnel (views → select → attempt → success) | 30d | **681** → **56** → **4** → **0** | `paywall_conversion_report.json` |
| Catalog `ok` / `empty` / other | 30d | **20** / **299** / **36** | PostHog `billing_product_catalog_status` |
| `billing_diagnostic` FEATURE_NOT_SUPPORTED (-2) | 7d on 1.3.50 | **5** events | `product_details_supported=false` |
| Catalog events on 1.3.50 (7d) | 7d | **0** `billing_product_catalog_status` | Matches `monetization_decision_brief.json` |
| Play API vs public listing version | snapshot | **1.3.50** vs **1.3.43** | `monetization_decision_brief.json` |
| iOS 1.3.50 shipped | snapshot | **false** | brief |
| Play IAP catalog (API readback) | snapshot | **ok**, products active | `play_iap_catalog.json` |
| PostHog paywall revenue proxy | 30d | **$0** | `executive_metrics.json` |
| Top paywall leak | 30d | **voice_gate**: 232 views, **0** attempts | `paywall_conversion_report.json` |
| Top failure reason (purchase result) | 30d | **failed**: 405 (proxy) | Not equivalent to Play ledger |

**Proxy labeling:** `paywall_purchase_success` = telemetry only. `billing_product_catalog_status` = client catalog probe, not Play Console revenue. See `docs/OPERATIONAL_RELIABILITY.md`.

---

## Ranked levers (P0–P3)

Impact = expected lift toward **first paid conversion** and path to $100/day; effort = engineering/ops weeks; cost must fit **≤$20/mo** unless CEO approves overrun.

### P0 — Fix money collection (ship + billing + listing parity)

| Lever | Expected impact | Effort | Cost |
|-------|-----------------|--------|------|
| **Unblock v1.3.51** (androidTest CI) and ship Android with billing probe fixes | Unblocks all downstream monetization; without this, experiments are invalid | High (CI/device tests) | $0 |
| **Resolve FEATURE_NOT_SUPPORTED on 1.3.50+ cohort** — `isFeatureSupported(PRODUCT_DETAILS)` before query; documented fallback `querySkuDetailsAsync` for legacy Play Store; user-facing “update Play Store” path; verify telemetry `catalog ok` on VC `1780500214` | Moves catalog from **empty** → **ok** for majority of paywall sessions; enables non-zero attempt→success | Medium | $0 |
| **Close Play listing lag** (promote 1.3.51+ to production track users actually install) | Aligns installed binary with IAP + metadata; reduces “wrong build” support noise | Low–medium | $0 |
| **Re-verify issue #1684** with 7d PostHog after ship: `billing_product_catalog_status=ok` on 1.3.51, ≥1 `paywall_purchase_success` | Proof gate before any growth spend | Low | $0 |

### P1 — Activate paywall on proven gates + ship iOS

| Lever | Expected impact | Effort | Cost |
|-------|-----------------|--------|------|
| **Ship iOS 1.3.51** (CEO `testflight-signoff` → internal → App Store) | Captures iOS training-heavy users; adds second store for subscriptions | High | $0 (CI/signing only) |
| **Fix voice_gate / repeat_gate** monetization path (232 + 54 paywall views, ~0 attempts) | Largest leaky entry points; even 1% view→attempt adds attempts | Medium | $0 |
| **Annual-first paywall + trial** (category norm: ~60% revenue annual; onboarding paywall + trial ~1.78% install→paid benchmark) | Improves *attempt* quality once catalog works | Medium | $0 |
| **Raise WQTU** (onboarding to 3 completions / 7d) | Correlates with retention and willingness to pay for “serious training” tools | Medium | $0 |

### P2 — Zero-budget growth loops (after P0 proof)

| Lever | Expected impact | Effort | Cost |
|-------|-----------------|--------|------|
| **ASO intent clusters** (MMA, round timer, reaction training, Tabata alternative) + screenshot copy tests | Organic installs without ads; long-tail vs head terms | Medium ongoing | $0 |
| **PostHog paywall experiments** (trial length, annual default, fallback offer on dismiss) — use RPPV not trial-start alone | Top-quartile apps 2–3× median via paywall tests | Medium | $0 (existing PostHog) |
| **Stack Overflow / community answers** (`docs/STACK_OVERFLOW_PLAYBOOK.md`) | Qualified technical audience; compounding backlinks | Low ongoing | $0 |
| **Wire store ledger revenue** into executive snapshot (ASC + Play) | Stops flying blind on real $ vs telemetry | Medium | $0 |

### P3 — Paid scale (only after attempt→success > 0)

| Lever | Expected impact | Effort | Cost |
|-------|-----------------|--------|------|
| **Apple Search Ads** (minimal budget, brand + competitor keywords) | Incremental installs if CPI ≤ $3 guardrail | Low | **≤$20/mo cap** — must not exceed mandate |
| **Reddit / social paid** | Usually negative ROI pre-PMF | Medium | **Defer** |
| **AdMob / display** | Needs scale; distracts from subscription | Medium | **Defer** |

**Reality check on $100/day:** At **~$4–10/mo** effective ARPU (monthly/annual blend), **$100/day after tax** ≈ **~350–900 active paying subscribers** depending on plan mix and store fees — far above **3** users who attempted purchase in 30d. Industry median for Health & Fitness **D35** install→paid **2.9%** implies thousands of *new installs per month* at scale, not ~200 WAU. Path: **first dollar → $400/mo indie proof (12mo case studies) → five-figure MRR** — not a June leap.

---

## 30-day action plan (tied to v1.3.51 + billing + iOS)

| Week | Focus | Exit criteria (evidence) |
|------|--------|-------------------------|
| **1** | Unblock `androidTest`, merge/release **v1.3.51** with billing diagnostics + `PRODUCT_DETAILS` gating/fallback per [Play Billing migration](https://developer.android.com/google/play/billing/migrate-gpblv6) | Green CI; artifact on `develop`; PR merged |
| **2** | Promote Android build to production; monitor PostHog **7d**: `billing_product_catalog_status=ok` on **≥1.3.51**; `billing_diagnostic` FEATURE_NOT_SUPPORTED trending down | Counts in brief JSON; issue #1684 updated |
| **3** | iOS: TestFlight signoff → build **1.3.51** → submit; fix any ASC IAP/metadata gaps | Build `VALID` on ASC; IAP products cleared |
| **4** | Paywall: annual default + trial copy; instrument **voice_gate** CTA; hold **all paid ads** | ≥1 `paywall_purchase_success` (telemetry) **or** store ledger row; attempt→success rate measurable |

**Daily habit (CEO/CTO):** Refresh `monetization_decision_brief.json` from PostHog after each prod rollout — WQTU, catalog ok/empty, purchase_success.

---

## What NOT to do

- **Do not run paid user acquisition** (Apple Ads, Reddit, Meta) until **catalog `ok` on production Android cohort** and **paywall attempt→success > 0** — current data shows money leaks at catalog and gate UX, not top-of-funnel volume.
- **Do not treat** `paywall_purchase_success` **or** catalog events **as revenue** — wire store ledger before ROI claims.
- **Do not optimize paywall colors** before structural tests (trial length, annual vs weekly default, fallback offer) — Adapty/RevenueCat 2026 data: trial/plan tests beat UI tweaks on LTV win rate.
- **Do not ship iOS** without CEO **testflight-signoff** environment approval (repo rule).
- **Do not ignore public listing 1.3.43 lag** — users on stale builds skew billing and support metrics.
- **Do not promise $100/day by June 30** — WQTU **4** vs target **25**; revenue proxy **$0**.
- **Do not add SaaS/tools** that push **>$20/mo** spend without CEO approval.
- **Avoid dark-pattern paywalls** (delayed dismiss, hidden terms) — Apple/Google enforcement increasing in 2026.

---

## External research synthesis (June 2026)

*Method: four focused WebSearch queries (Perplexity unavailable — `PERPLEXITY_API_KEY` not in `.env`). Treat as directional, not primary evidence.*

### 1. Play Billing `PRODUCT_DETAILS` / `FEATURE_NOT_SUPPORTED`

- Google documents **-2 `FEATURE_NOT_SUPPORTED`** when Play Store on device is too old for `ProductDetails` ([Billing errors](https://developer.android.com/google/play/billing/errors), [BillingResponseCode](https://developer.android.com/reference/com/android/billingclient/api/BillingClient.BillingResponseCode)).
- **Mitigation:** call `isFeatureSupported(PRODUCT_DETAILS)` first; if unsupported, **fallback** to `querySkuDetailsAsync` (BL6 migration guide) or block purchase with clear “update Google Play” UX ([migrate GPBLv6](https://developer.android.com/google/play/billing/migrate-gpblv6)).
- Field reports: updating Play Store app often resolves emulator/device false negatives ([Stack Overflow #72317599](https://stackoverflow.com/questions/72317599/android-google-billing-integration-client-does-not-support-productdetails)).
- **Maps to our telemetry:** `billing_response_code=-2`, `product_details_supported=false` on 1.3.45–1.3.50 — aligns with official diagnosis; fix is client capability path + device hygiene, not Console SKU deletion (Console readback already **ok**).

### 2. Fitness / timer subscription benchmarks (2026)

- RevenueCat State of Subscription Apps 2026 — **Health & Fitness median D35 download-to-paid: 2.9%** (top quartile **>6.2%**) ([Health & Fitness report](https://www.revenuecat.com/state-of-subscription-apps-2026-health-and-fitness/)).
- Adapty ($3B processed): **onboarding paywall + trial ~1.78%** install→paid; **install→trial median 11.2%** (NA **14.5%**); annual-heavy revenue mix in Health & Fitness ([benchmarks](https://adapty.io/blog/health-fitness-app-subscription-benchmarks/)).
- Trial length: **7–14 days** often beats ≤3 days for habit apps; **17–32 day** trials ~**46%** trial→paid in cross-category summaries ([Apps Finboard 2026](https://appsfinboard.com/blog/subscription-pricing-paywall-optimization-mobile-apps/)).
- **Implication for RTT:** Interval/tactical training behaves like fitness (habit, annual plans). Prioritize **annual + trial** and **Day 0 + Day 4–7** paywall paths once billing works.

### 3. ASO + paywall (tactical / fitness)

- **89%+ trial starts on Day 0** — paywall after short value onboarding ([GrowthPad 2026](https://growthpad.blog/2026/04/15/whats-actually-working-in-app-distribution-in-2026/)).
- Hard paywall / strong gating can outperform weak freemium on trial→paid (category-dependent; test with RPPV) ([RocketShip HQ](https://www.rocketshiphq.com/paywall-optimization-fitness-apps/)).
- ASO 2026: **intent clusters** and long-tail over head terms; screenshot text and localized listings ([GrowthPad 2026](https://growthpad.blog/2026/04/15/whats-actually-working-in-app-distribution-in-2026/)).
- **Implication:** RTT should own “random interval timer”, “MMA round timer”, “reaction training timer” clusters; show **training outcome** in screenshots, not feature lists.

### 4. Zero-budget indie path toward material revenue

- Realistic solo trajectory: **months 6–12** for **$3k–15k/mo** *if* PMF + subscription ([ForaSoft 2026 playbook](https://www.forasoft.com/blog/article/app-revenue-potential)); **bottom 94%** apps **<$1k/mo**.
- Case: **~£394/mo** after 12 months solo Android with **~1.9k MAU** ([ExtensionBooster](https://extensionbooster.net/blog/solo-android-developer-first-year-lessons-app-growth/)) — proof point, not $100/day.
- **$100/day (~$3k/mo)** sits near “top ~800 App Store rank” band in some analyses — requires **retention + conversion + installs**, not paywall button color.
- **Implication:** RTT should target **first $1–400 MRR** with **$0 ads**, then reinvest only within cap.

---

## Sources / citations

### Internal (verified in session)

- `marketing/data/monetization_decision_brief.json` (2026-06-03)
- `marketing/data/paywall_conversion_report.json` (2026-06-03)
- `marketing/data/wqtu_health.json` (2026-06-03)
- `marketing/data/play_iap_catalog.json` (2026-06-03)
- `marketing/data/executive_metrics.json`
- PostHog MCP `execute-sql` — 2026-06-03 UTC
- `AGENTS.md` — Growth North Star section
- GitHub issue [#1684](https://github.com/IgorGanapolsky/Random-Timer/issues/1684)

### External (WebSearch fallback; not independently verified in app)

- [Google Play Billing — Handle errors](https://developer.android.com/google/play/billing/errors)
- [Migrate to Play Billing Library 6](https://developer.android.com/google/play/billing/migrate-gpblv6)
- [BillingClient.BillingResponseCode](https://developer.android.com/reference/com/android/billingclient/api/BillingClient.BillingResponseCode)
- [RevenueCat — State of Subscription Apps 2026: Health & Fitness](https://www.revenuecat.com/state-of-subscription-apps-2026-health-and-fitness/)
- [Adapty — Health & Fitness benchmarks 2026](https://adapty.io/blog/health-fitness-app-subscription-benchmarks/)
- [Adapty — State of in-app subscriptions 2026](https://adapty.io/state-of-in-app-subscriptions-report/)
- [Apps Finboard — Subscription pricing & paywall 2026](https://appsfinboard.com/blog/subscription-pricing-paywall-optimization-mobile-apps/)
- [GrowthPad — App distribution 2026](https://growthpad.blog/2026/04/15/whats-actually-working-in-app-distribution-in-2026/)
- [RocketShip HQ — Fitness paywall optimization](https://www.rocketshiphq.com/paywall-optimization-fitness-apps/)
- [ForaSoft — App revenue potential 2026](https://www.forasoft.com/blog/article/app-revenue-potential)
- [Stack Overflow — ProductDetails FEATURE_NOT_SUPPORTED](https://stackoverflow.com/questions/72317599/android-google-billing-integration-client-does-not-support-productdetails)

---

## Appendix: PostHog queries used (reproducible)

```sql
-- WQTU (7d)
SELECT count(*) AS wqtu_7d FROM (
  SELECT person_id FROM events
  WHERE event = 'timer_completed' AND timestamp > now() - interval 7 day
  GROUP BY person_id HAVING count() >= 3
);

-- Paywall + billing events (30d)
SELECT event, count() AS events, count(DISTINCT person_id) AS users
FROM events
WHERE timestamp > now() - interval 30 day
  AND event IN ('paywall_viewed', 'paywall_purchase_attempt', 'paywall_purchase_success',
                'billing_product_catalog_status', 'billing_diagnostic', 'billing_client_setup')
GROUP BY event ORDER BY events DESC;

-- Catalog status totals (30d)
SELECT
  countIf(properties.status = 'ok') AS catalog_ok,
  countIf(properties.status = 'empty') AS catalog_empty,
  countIf(properties.status NOT IN ('ok', 'empty')) AS catalog_other
FROM events
WHERE timestamp > now() - interval 30 day
  AND event = 'billing_product_catalog_status';
```
