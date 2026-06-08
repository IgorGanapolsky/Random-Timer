---
generated_at: 2026-06-08T20:32:00Z
source: live_evidence_audit + web_research_june_2026
reliability_contract_doc: docs/OPERATIONAL_RELIABILITY.md
issue_ref: https://github.com/IgorGanapolsky/Random-Timer/issues/1684
budget_cap_usd_month: 20
---

# June 2026 Growth & Monetization Strategy Brief — Random Tactical Timer

**Audit window:** 2026-06-08 UTC  
**North Star:** WQTU (≥3 `timer_completed` / person / trailing 7d); Q2 target **25**  
**Business goal:** $100/day after-tax (not claimed achievable near-term)

---

## Executive snapshot (2026-06-08)

| Question | Answer | Evidence |
|----------|--------|----------|
| Published everywhere? | **Partial** | Android Play API **1.3.53** on production; iOS **not shipped**; public storefronts still **1.3.43** |
| Observability good? | **B−** | PostHog funnels + billing probes live; `$exception` not yet in taxonomy; executive HogQL had `http_400` |
| Monetization good? | **D** | 0 `paywall_purchase_success` (30d); catalog mostly non-ok on 1.3.50+; #1684 open |
| Promoting everywhere? | **No** | `paid_distinct_users_30d=0`; Apple Ads PAUSED $0; AdMob not production-ready |

---

## A. Live evidence (reproducible)

### Release / store ground truth

| Layer | Android | iOS |
|-------|---------|-----|
| GitHub latest release | **v1.3.53** (2026-06-08T20:01:41Z) | same tag |
| Play Publisher API (tier0) | **1.3.53**, VC **1780947164**, `completed` on `production` — native-release run [27161374477](https://github.com/IgorGanapolsky/Random-Timer/actions/runs/27161374477) | n/a |
| ASC API (tier1) | n/a | Latest **READY_FOR_SALE: 1.3.43** (`executive_metrics.json` CI snapshot) |
| Public storefront (tier2 advisory) | **1.3.43** HTML proxy — `verify_play_public_listing.py` + `post_publish_gate.json` | **1.3.43** — iTunes lookup `id=6758355312` |
| iOS submit-for-review | **Skipped** — `platform=android`, `submit_review=false` in run 27161374477 | |

**Proxy labeling:** Public HTML version is `android_listing_semantics=embedded_play_html_141_string_proxy_not_Play_Console_ground_truth`. Play API `completed` is upload ground truth, not user-visible listing version.

### PostHog (live MCP `execute-sql`, 2026-06-08 UTC)

| Metric | Window | Value | Notes |
|--------|--------|-------|-------|
| WQTU | 7d | **8** | Q2 target 25 — **not on track** |
| Paywall views | 30d | **752** / **229** users | telemetry |
| Purchase attempts | 30d | **4** / **3** users | telemetry |
| Purchase success | 30d | **0** | **not** store ledger |
| Billing catalog (7d) | status breakdown | empty **19**, missing_required **15**, product_details_unsupported **13**, ok **4** | client probe |
| 1.3.50+ catalog (7d) | by version | 1.3.51: 9 unsupported; 1.3.52: 3 unsupported; 1.3.53: 2 events (1 unsupported, 1 billing_not_ready) | too early for proof |
| `$exception` on 1.3.53 | 7d | **0** | event not in project taxonomy yet (shipped today) |

### Monetization / growth artifacts

- `monetization_decision_brief.json`: decision **keep #1684 open** until retail catalog `ok`
- `post_publish_gate.json`: `store_public_pass=false` (both platforms VERSION_MISMATCH vs 1.3.53)
- `admob_status.json`: app-ads.txt **pass**; production rewarded **blocked** (payment setup, SDK stub, IAP health)
- `apple_ads_live_metrics.json`: 1 campaign **PAUSED**, 30d taps **0**, spend **$0.00**
- `north_star.json`: `paid_distinct_users_30d=0`, `active_campaign_count=0`
- OVB: `blocking_failures=0`; advisory fails on public iOS/Android version mismatch

---

## B. June 2026 research vs our state

### Hybrid monetization (IAP + ads)

**Best practice (2026):** Fix subscription/IAP collection first; add rewarded ads only for non-subscribers after catalog health; suppress ads for paying users; measure blended ARPU, not siloed streams.

**Sources:**
- [MonetizationGuy — Hybrid decision framework](https://monetizationguy.com/articles/hybrid-monetization-ads-iap-subscription-decision)
- [RevenueCat — Hybrid techniques](https://www.revenuecat.com/blog/growth/hybrid-monetization-techniques/)
- [Adapty — Hybrid guide 2026](https://adapty.io/blog/hybrid-monetization-for-subscription-apps/)

**Our gap:** IAP path broken on production cohort (`product_details_unsupported` dominant on 1.3.51–1.3.53). AdMob scaffold ready but `StubRewardedAdPort` default — **do not mix ads + broken paywall**.

### PostHog mobile observability

**Best practice:** SDK error tracking + symbol upload (ProGuard/dSYM); billing funnel saved queries; session replay on paywall drop-offs; funnel → replay drill-down.

**Sources:**
- [PostHog Android SDK — error tracking + session replay](https://posthog.com/docs/libraries/android)
- [PostHog mobile session replay](https://posthog.com/docs/session-replay/mobile)
- [PostHog error tracking](https://posthog.com/docs/error-tracking)

**Our gap:** Billing HogQL templates exist (`posthog_observability.json`); Android `$exception` shipped in **1.3.53** but **0 events / not in taxonomy** yet; enable replay on paywall gates after catalog fix.

### Zero-budget growth ($0–20/mo)

**Best practice:** ASO long-tail keywords (SP 35–55, difficulty <35); community/build-in-public; no Branch/paid stack until funnel converts; Apple Search Ads only after IAP proof, use discovery campaigns within cap.

**Sources:**
- [Applyra — ASO guide indie 2026](https://www.applyra.io/blog/complete-aso-guide-indie-developers)
- [Appalize — Zero-budget indie marketing](https://www.appalize.com/blog/app-marketing/how-to-market-an-indie-app-with-zero-budget)
- [Sonar — Low-competition keywords](https://trysonar.app/blog/low-competition-keywords)

**Our gap:** No active paid campaigns; organic WQTU rising (8) but quarter target missed; listing still shows **1.3.43** — ASO/changelog stale on storefront.

### Play API ship vs public listing

**Best practice:** Treat Publisher API `completed` as upload truth; public HTML can lag hours (CI polled 900s, still 1.3.43). IAP catalog client propagation separate (minutes–hours; device cache).

**Sources:**
- [Google Play Edits API](https://developers.google.com/android-publisher/edits)
- [ProductUpdateLatencyTolerance](https://developers.google.com/android-publisher/api-ref/rest/v3/ProductUpdateLatencyTolerance)

**Our gap:** **Split-brain** — API **1.3.53**, storefront **1.3.43** (10-version skew). Users installing from search still get old binary → invalidates billing telemetry cohort analysis.

### Store policy (tactical timer / fitness)

**Best practice:** Subscriptions need sustained value + in-app cancel (≤2 taps); use platform billing; disclose auto-renewal; age APIs where required (2026 state laws).

**Sources:**
- [Apple auto-renewable subscriptions](https://developer.apple.com/app-store/subscriptions/)
- [Google Play subscriptions policy](https://support.google.com/googleplay/android-developer/answer/9900533)
- [FTC / fitness app renewal guidance 2026](https://newagesysit.com/blog/ftc-guidelines-app-store-health-data-rules-for-fitness-platforms-in-the-united-states/)

**Our gap:** Policy-compliant paywall UX exists; **revenue blocked by catalog**, not policy.

---

## C. Strategy grades

| Area | Grade | Top gaps |
|------|-------|----------|
| Observability | **B−** | `$exception` not flowing; executive `http_400`; no session replay on paywall leaks |
| Monetization | **D** | 0 purchase success; catalog ok **4/58** events (7d); #1684 open |
| Growth / ads | **F** | No serving paid traffic; Apple Ads paused; AdMob not live |

---

## D. Ranked action plan (salience × $20 cap)

| Rank | Action | WQTU / paywall impact | Cost |
|------|--------|----------------------|------|
| **1** | Close **#1684**: `billing_product_catalog_status=ok` on Play-installed **Samsung/Pixel** on ≥1.3.53; ≥1 `paywall_purchase_attempt` with loaded offers | Unblocks all revenue | $0 |
| **2** | **Ship iOS 1.3.53+**: `native-release platform=ios` + `submit_review=true` after TestFlight signoff | Captures iOS training cohort | $0 |
| **3** | Monitor **public listing** catch-up to 1.3.53; re-run `post_publish_gate` daily until pass | Aligns installed binary with fixes | $0 |
| **4** | Fix **voice_gate / repeat_gate** paywall leak (232+ views, ~0 attempts in prior report) | Raises attempt→success denominator | $0 |
| **5** | **ASO long-tail** refresh (MMA, round timer, reaction training) + 15 authentic reviews | Organic WQTU lift | $0 |

**Hold until catalog ok:** Apple Ads resume, AdMob rewarded rollout, any paid spend.

**Budget:** MTD external spend **~$0**; cap **$20/mo** — no new SaaS.

---

## E. Contradiction protocol

If CEO device shows different version than API: run Play API readback + public HTML + PostHog `$app_version` breakdown before changing course.
