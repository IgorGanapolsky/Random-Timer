# Monetization Strategy — Hybrid Stack (June 2026)

**App:** Random Tactical Timer — native **Android (Kotlin/Compose)** + **iOS (Swift/SwiftUI)** only (not React Native).

**CEO thesis:** Retention-first hybrid monetization for tactical/fitness niche. **Not** paid download. **Not** ads-only.

**Constraints:** `$0` IAP revenue today; 7 purchase attempts / 0 success (all `user_cancelled`); Play IAP catalog OK; **`$20/mo`** total external spend cap.

---

## Target hybrid stack

| Layer | CEO target | Status in repo |
|-------|------------|----------------|
| **Free** | Rewarded ads; limited presets | **Partial** — free tier gates exist; **no AdMob / rewarded ads** |
| **Premium sub ($4.99–9.99/mo)** | No ads, custom drills, cloud sync, analytics, voice packs, wear sync | **Partial** — subs + Pro gates; **no** cloud sync, wear, or in-app analytics tier |
| **One-time IAP packs** | Special Forces, boxing HIIT, CrossFit, BJJ interval packs | **Missing** — no pack SKUs; Pro **audio** drops via manifest only |
| **Affiliate** | Tactical gear, supplements | **Missing** (defer) |

---

## Audit: what exists today

### Store SKUs (live catalog)

| Platform | IDs | Type |
|----------|-----|------|
| Android | `pro_base` | One-time INAPP |
| Android | `elite_tactical`, `elite_tactical_monthly` | Subscriptions (annual + P1M) |
| iOS | `com.iganapolsky.randomtimer.pro` | One-time |
| iOS | `com.iganapolsky.randomtimer.elite`, `.pro.monthly` | Subscriptions |

Paywall merchandises monthly + annual (+ lifetime on iOS where catalog returns `pro`).

### Paywall gates (`entry_point`)

- `setup_upgrade_cta`, `range_gate`, `voice_gate`, `repeat_gate`, `sound_arsenal_gate`
- **`qualified_training_gate`** (PR) — once after 3rd completed session (WQTU-aligned)
- Deep link: `randomtimer://open/upgrade` / GitHub Pages `/Random-Timer/upgrade`

### Free vs Pro product gates

- **Sounds:** free = intense + chime; Pro = full arsenal
- **Range:** free max 5 min; Pro up to 60 min
- **Voice callouts, repeat round caps:** Pro only
- **Presets:** one built-in (`Competition Warmup`); not paywalled per pack
- **Pro audio “packs”:** remote manifest (`ProAudioPackStore`) — **not** separate IAP products

### Ads

- **None** — no `google-mobile-ads`, no rewarded/interstitial SDK, no ad unit IDs in repo.

### Analytics (PostHog)

- Funnel: `paywall_viewed` → `paywall_offer_select` / `paywall_plan_selected` → `paywall_purchase_attempt` → `paywall_purchase_success`
- `subscription_funnel_step`, `feature_gate_hit`, `billing_product_catalog_status`
- **P0:** `qualified_training_paywall_eligible` — users who hit session threshold before sheet opens (`entry_point=qualified_training_gate`)

#### A/B paywall experiments (PostHog flags)

| Flag | Values | Purpose |
|------|--------|---------|
| `paywall_default_plan_annual` | on/off | Default plan card: annual vs monthly |
| `paywall_value_framing` | `control` / `outcomes_first` | Headline + subhead copy variant |
| `rewarded_ads_enabled` | on/off (default **off**) | Gate rewarded video on free tier |

#### RevenueCat-style subscription events (native StoreKit / Play Billing)

Same event names on Android + iOS for cross-platform funnels:

| Event | When |
|-------|------|
| `paywall_viewed` | Sheet opened (`entry_point`, `paywall_experiment_variant`, `paywall_value_framing_variant`) |
| `paywall_plan_selected` / `paywall_offer_select` | User taps a plan card |
| `paywall_purchase_attempt` | Purchase flow launched |
| `paywall_purchase_success` / `paywall_purchase_result` | Terminal purchase outcome |
| `paywall_restore_result` | Restore purchases tapped |
| `subscription_funnel_step` | Canonical step property (`funnel_step`: `paywall_viewed` → `purchase_succeeded`) |
| `free_trial_started` | Trial offer accepted |
| `billing_product_catalog_status` | Catalog probe (missing SKU diagnostics) |

Rewarded IAA (P1, flag off until AdMob account):

| Event | When |
|-------|------|
| `rewarded_ad_requested` | User starts watch-ad unlock |
| `rewarded_ad_completed` | Ad finishes (success/fail) |
| `rewarded_ad_unlock` | `pro_sound_trial` granted |

### Not built

- Rewarded ads, cloud sync, wear/watch sync, training analytics dashboard, discipline IAP packs, affiliate links, web checkout funnel.

---

## Phased roadmap

### P0 — Fix store IAP revenue (now → 2 weeks)

- Ship **`qualified_training_gate`** + `qualified_training_paywall_eligible` event.
- Tune paywall copy / default plan on that entry; measure attempt→success by `entry_point`.
- Optional: store intro offers (CEO approval for new offer IDs).
- **Success:** `paywall_purchase_success` > 0; blended sub ARPU path toward $4.99–9.99/mo positioning.

### P1 — Rewarded ads on free tier ($0 SDK if AdMob account exists)

- **Shipped (code):** PostHog flag `rewarded_ads_enabled` (default **off**), stub ad port, test unit IDs documented, events `rewarded_ad_*`.
- UX: watch ad → **one Pro sound trial** (`pro_sound_trial`); Elite sub copy includes ad-free.
- **Blocker:** AdMob publisher account + SDK wiring (Google test units ready for debug).
- **CEO:** approve AdMob publisher account to enable flag + SDK.

### P2 — One-time discipline IAP packs

- **Shipped (scaffold):** `DisciplinePackCatalog` — Android `pack_*`, iOS `com.iganapolsky.randomtimer.pack.*` (see `native-android/fastlane/metadata/android/en-US/iap_discipline_packs.txt`).
- Not in Play verify required list until Console products exist.
- Target price band: **$2.99–9.99** one-time per pack (CEO sets after P0 converts).
- Unlock preset bundles + pack-specific voice/sounds; sub remains “all access.”

### P3 — Web funnel + affiliate (later)

- Stripe/checkout on CEO domain for annual + pack bundles; deep link restore.
- Affiliate: curated gear/supplement links in post-session or community surfaces — **no** spend until P0 converts.

---

## Pricing direction (hybrid)

- **Sub:** reposition toward **$4.99–9.99/mo** (or ~$49–79/yr) vs current ~$3.99/mo / ~$29.99/yr — requires store price changes + paywall copy, not code-only.
- **Packs:** $2.99–9.99 one-time per discipline (CEO to set after P0 baseline).

---

## CEO decisions

1. **AdMob:** create/link publisher account for P1?
2. **Sub price ladder:** approve $4.99 vs $9.99/mo test and annual anchor?
3. **Pack SKUs:** confirm four discipline names and price points for P2?
4. **Web funnel domain** for P3 (apex vs GitHub Pages)?
5. **Affiliate:** any preferred partners, or defer until P2?

---

## North star guardrails

- **WQTU** (≥3 `timer_completed` / 7d) — monetization must not harm completion rate.
- Report funnel by `entry_point` + `platform`; never claim revenue without store ledger read-back.
