# Money Today Close Packet - 2026-05-11

## Objective

Generate same-day revenue with $0 new spend by publishing a concrete $499 Workflow/Voice Agent Reliability Diagnostic through existing Stripe and Zernio/GitHub channels.

## Money truth

Stripe live balance read-back:

```json
{
  "available_usd_cents": 0,
  "pending_usd_cents": 0,
  "livemode": true
}
```

Stripe search window: 2026-05-11 00:00:00 America/New_York through 2026-05-12 00:00:00 America/New_York (`created>=1778472000 AND created<1778558400`).

```json
{
  "charges_results": [],
  "payment_intents_results": []
}
```

Result at execution time: no confirmed revenue today yet.

## Offer asset

- Product: AI Agent Reliability Diagnostic (`prod_UUyLoensNMyVgI`)
- Price: `price_1TVyPHGGBpd520QYThH5YIcv`
- Amount: `$499.00 USD`
- Stripe payment link: https://buy.stripe.com/9B63cveyU1eS7xT9uj3sI2g
- Intake: https://cal.com/igorganapolsky/diagnostic

## Published content

- Offer post: `marketing/posts/2026-05-11-workflow-voice-agent-reliability-diagnostic.md`
- Canonical page after GitHub Pages build: `https://igorganapolsky.github.io/Random-Timer/marketing/site/posts/2026-05-11-workflow-voice-agent-reliability-diagnostic.html`
- Stripe checkout HTTP read-back: `200`
- Canonical page HTTP read-back: `200`

## Zernio fan-out read-back

Workflow: `Zernio growth orchestration`, run `25694174790`, `workflow_dispatch` on `develop`.

Health:

```json
{
  "status": "ok",
  "account_count": 6
}
```

Publish result:

```json
{
  "status": "published",
  "fallback": "retried_with_current_text_accounts",
  "platform_count": 4,
  "platform_results": [
    {"platform": "threads", "status": "published", "url": "https://www.threads.com/@igorganapolsky/post/DYNguPflxWA"},
    {"platform": "twitter", "status": "published"},
    {"platform": "bluesky", "status": "failed", "reason": "post exceeded 300 characters"},
    {"platform": "reddit", "status": "failed", "reason": "selected community does not allow text posts"}
  ]
}
```

Public Threads URL HTTP read-back: `200`.

## Direct buyer CTA dispatch read-back

PR `#1472` merged to `develop` as `0b257afedad0f1d1d4e94135a69dbd2ee01031d0`, adding exact-text Zernio dispatch for short buyer CTAs.

Workflow: `Zernio growth orchestration`, run `25695153772`, `workflow_dispatch` on `develop`.

Workflow read-back:

```json
{
  "conclusion": "success",
  "headSha": "0b257afedad0f1d1d4e94135a69dbd2ee01031d0",
  "createdAt": "2026-05-11T20:23:29Z",
  "updatedAt": "2026-05-11T20:23:57Z"
}
```

Publish result artifact row:

```json
{
  "timestamp": "2026-05-11T20:23:54+00:00",
  "slug": "custom-buyer-cta-20260511202342",
  "channel": "zernio_custom",
  "status": "published",
  "content_chars": 215,
  "platform_count": 3,
  "allowed_platforms": ["bluesky", "threads", "twitter"]
}
```

Published URLs and HTTP read-back:

- Bluesky: `https://bsky.app/profile/iganapolsky.bsky.social/post/3mlm453667g2c` -> `200`
- Threads: `https://www.threads.com/@igorganapolsky/post/DYNi9X1F0jo` -> `200`
- Twitter/X: `https://twitter.com/i/web/status/2053934104794603523` -> `200`
- Stripe checkout: `https://buy.stripe.com/9B63cveyU1eS7xT9uj3sI2g` -> `200`

Post text:

```text
AI agent/voice workflow stuck, looping, or blocking releases? I will do a same-day reliability diagnostic for $499 and give you the failure points + fix plan. Pay/book: https://buy.stripe.com/9B63cveyU1eS7xT9uj3sI2g
```

Post-dispatch Stripe live read-back:

```json
{
  "balance": {
    "available_usd_cents": 0,
    "pending_usd_cents": 0,
    "livemode": true
  },
  "charges_results": [],
  "payment_intents_results": []
}
```

## Budget

- New paid spend: `$0.00`
- Monthly cap: `$20.00`
- Remaining budget before any external spend approval: `$20.00`

## Verification commands

```bash
python3 scripts/growth_content_pipeline.py --output-root marketing build-site
curl -L -s -o /dev/null -w '%{http_code}\n' https://buy.stripe.com/9B63cveyU1eS7xT9uj3sI2g
gh workflow run "Zernio growth orchestration" --ref develop
gh run watch <run_id> --exit-status
```
