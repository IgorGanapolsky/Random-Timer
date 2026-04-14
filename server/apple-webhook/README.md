# Apple App Store Server Notifications V2 — Cloudflare Worker

Receives, verifies, and stores Apple App Store Server Notifications V2 events.
Deployed as a Cloudflare Worker on the free tier (100K requests/day, 1K KV writes/day).

---

## What it does

- Accepts `POST /apple/notifications` from Apple's App Store servers.
- Verifies the JWS (JSON Web Signature) payload using Apple's certificate chain, rejecting any
  unsigned or spoofed requests with `403 Forbidden`.
- Parses notification types:
  - `REFUND` — logs `originalTransactionId`, `productId`, `refundDate`, `revocationReason`.
  - `DID_RENEW`, `EXPIRED`, `DID_FAIL_TO_RENEW`, `SUBSCRIBED`, `DID_CHANGE_RENEWAL_STATUS`,
    `GRACE_PERIOD_EXPIRED`, `REFUND_DECLINED`, `REFUND_REVERSED`, `REVOKE` — logs renewal/expiry.
- Stores all events in a Cloudflare KV namespace (`REFUND_EVENTS`) with a 90-day TTL.
- Returns `200 OK` to Apple on receipt (required; Apple retries on non-2xx).
- Returns `403 Forbidden` for invalid JWS signatures.
- Provides `GET /health` for uptime checks.

---

## Prerequisites

- [Node.js](https://nodejs.org/) 20+
- A Cloudflare account (free tier is sufficient)
- `wrangler` CLI (installed via `npm install`)

---

## Setup

### 1. Install dependencies

```bash
cd server/apple-webhook
npm install
```

### 2. Create the KV namespace

```bash
# Production namespace
npx wrangler kv:namespace create REFUND_EVENTS

# Optional: preview namespace for local dev
npx wrangler kv:namespace create REFUND_EVENTS --preview
```

Copy the `id` (and optionally `preview_id`) from the output and paste it into `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "REFUND_EVENTS"
id = "YOUR_KV_NAMESPACE_ID_HERE"
# preview_id = "YOUR_PREVIEW_ID_HERE"   # optional — for local wrangler dev
```

### 3. Deploy

```bash
npx wrangler deploy
```

The CLI will print the Worker URL, e.g.:
```
https://apple-webhook.<your-subdomain>.workers.dev
```

---

## Configure App Store Connect

1. Open [App Store Connect](https://appstoreconnect.apple.com).
2. Navigate to **Apps** → your app → **App Information**.
3. Scroll to **App Store Server Notifications**.
4. Enter the Worker URL:
   - **Production URL**: `https://apple-webhook.<your-subdomain>.workers.dev/apple/notifications`
   - **Sandbox URL**: same URL (the worker handles both; environment is logged per notification)
5. Click **Save**.

Apple will immediately send a `TEST` notification to verify the endpoint.

---

## Test with Apple's sandbox environment

Apple provides a sandbox notification endpoint. Use the [App Store Server API](https://developer.apple.com/documentation/appstoreserverapi/request_a_test_notification)
to trigger a test notification:

```bash
# Request a test notification (requires App Store Connect API key)
curl -X POST \
  https://api.storekit-sandbox.itunes.apple.com/inApps/v1/notifications/test \
  -H "Authorization: Bearer <YOUR_JWT>"
```

Or trigger directly from App Store Connect (App Information → Send Test Notification button).

Check the Worker logs via:

```bash
npx wrangler tail
```

---

## View stored events

List refund events stored in KV:

```bash
npx wrangler kv:key list --namespace-id YOUR_KV_NAMESPACE_ID --prefix "refund:"
```

Read a specific event:

```bash
npx wrangler kv:key get "refund:<notification_uuid>" --namespace-id YOUR_KV_NAMESPACE_ID
```

---

## Integration with executive_metrics_snapshot.py

The `scripts/check_refunds.py` script reads from this KV namespace via the Cloudflare REST API
and feeds data into `scripts/executive_metrics_snapshot.py`.

Required environment variables (`.env` or GitHub Actions secrets):

```
CLOUDFLARE_API_TOKEN=<token with KV:Read permission>
CLOUDFLARE_ACCOUNT_ID=<your Cloudflare account ID>
CLOUDFLARE_KV_NAMESPACE_ID=<the namespace id from wrangler.toml>
```

Create a scoped API token at:
[Cloudflare Dashboard → My Profile → API Tokens → Create Token](https://dash.cloudflare.com/profile/api-tokens)
with permission: **Account → Workers KV Storage → Read**

Run the refund check:

```bash
python scripts/check_refunds.py --days 30
python scripts/check_refunds.py --days 7 --json-stdout
```

---

## Architecture

```
Apple App Store
      │  POST /apple/notifications
      │  {signedPayload: "<JWS>"}
      ▼
Cloudflare Worker (src/index.ts)
      │
      ├── verify JWS signature (src/verify.ts)
      │   └── checks x5c chain → Apple Root CA G3/G4
      │
      ├── parse notification type
      │   ├── REFUND → log + store in KV
      │   ├── DID_RENEW, EXPIRED, ... → log + store in KV
      │   └── TEST → log only
      │
      └── return 200 OK
            │
            ▼
    Cloudflare KV (REFUND_EVENTS)
            │
            ▼
    scripts/check_refunds.py  (reads via REST API)
            │
            ▼
    executive_metrics_snapshot.py  (refunds.asn_v2_* fields)
```

---

## Cost

All within Cloudflare free tier:
- Workers: 100K requests/day free
- KV reads: 100K/day free
- KV writes: 1K/day free

Apple sends at most one notification per purchase event. Even at 10K daily active users,
this is well under the free limits.

---

## Security notes

- The worker rejects any request with an invalid or missing JWS signature (`403`).
- The certificate chain must terminate at Apple Root CA G3 or G4 (hardcoded in `src/verify.ts`).
- No secrets are stored in `wrangler.toml`. KV namespace IDs are not sensitive.
- Do not log full `raw_transaction` payloads to console in production — they are stored in KV only.
