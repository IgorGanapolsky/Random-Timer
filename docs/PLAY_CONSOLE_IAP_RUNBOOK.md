# Play Console IAP Runbook (P0 Revenue)

**App:** Random Tactical Timer — `com.iganapolsky.randomtimer`  
**Code product IDs** (`native-android/.../billing/ProManager.kt`):

| Product ID | Billing type in app |
|------------|---------------------|
| `pro_base` | One-time (INAPP) |
| `elite_tactical` | Subscription (SUBS) |
| `elite_tactical_monthly` | Subscription (SUBS), P1M |

PostHog `billing_product_not_found` on Android means Play Billing returned none of these at runtime — fix in **Play Console**, not in app code alone.

**Console (App Distribution project is separate):** Monetize → Products in app `4976249162120849673`.

---

## Checklist (CEO / console)

### 1. One-time product: `pro_base`

1. Play Console → **Monetize with Play** → **Products** → **One-time products**
2. Create or open product ID **`pro_base`**
3. Set price, listing (en-US), **Activate**
4. Confirm product is **Active** and available in target countries

### 2. Subscriptions: `elite_tactical` (annual)

1. **Subscriptions** → product **`elite_tactical`**
2. Ensure at least one **base plan** (annual) is **Active**
3. Price and eligibility set for production countries

### 3. Subscription: `elite_tactical_monthly`

1. **Subscriptions** → **Create subscription** ID **`elite_tactical_monthly`**
2. Base plan: **Monthly (P1M)**, price **$3.99/month** (or intended price)
3. **Activate** base plan and subscription

### 4. Link to app

- Products must be on the same app package as the release users install
- After changes, allow **up to several hours** for Play Billing cache propagation

### 5. Verify (no purchase required)

- Install **production** build from Play (or latest Firebase after signoff)
- Open paywall → PostHog should stop spiking `billing_product_not_found`
- Optional: `billing_product_catalog_status` event should list IDs in `available_product_ids`

---

## Managed publishing (version parity)

If production upload succeeded but Play Store still shows older **versionName** (e.g. 1.3.33):

1. **Publishing overview** → **Publish N changes** (managed publishing ON)
2. Staged items may include production rollout + listing assets

Do not confuse **versionCode** in console (e.g. `1779125389`) with public **versionName** until publish completes.

---

## Evidence to capture

- Screenshot: Subscriptions list showing all product IDs and Active state
- Screenshot: One-time products showing `pro_base` Active
- PostHog: paywall funnel / catalog failure counts declining after 24–48h

---

## Related

- `docs/FIREBASE_ANDROID_INFRASTRUCTURE.md` — Firebase App Distribution (internal APK)
- `docs/AUTONOMOUS_OPERATIONS.md` — CI gates and 24/7 automation
- Merged paywall guard: PR #1562 — hides unbuyable SKUs until catalog probe completes
