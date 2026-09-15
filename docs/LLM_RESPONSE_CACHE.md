# LLM Response Cache (lite) — skip repeat inference when inputs did not change

Operating brief from [The New Stack — Why an old caching trick is your secret to lower LLM costs](https://thenewstack.io/llm-response-caching-costs/) (Abhilash Rao Mesala, 2026-09-14):

> Before paying for another answer, check whether anything that could change it has changed: the request, its context, the model settings, or the underlying data. Fingerprint those inputs; on an exact (or safe semantic) hit, return the stored answer **without calling the model**.

**Response caching ≠ prompt caching.** Prompt caching reuses provider-side prompt compute at reduced rates while output still bills. Response caching skips the call entirely when our infrastructure already holds a valid answer.

## Anti-pattern

**Re-answer unchanged work** — projecting token savings without a measured hit rate, caching PII/account-scoped or creative or live data, or conflating prompt-cache discounts with full call skips.

## Health signals (required)

| Signal | Meaning here |
|--------|----------------|
| `fingerprint_exact_match_first` | SHA-256 of normalized query + ctx (model, settings, source version, access scope) |
| `measure_hit_rate_before_savings` | Never claim % savings until hit rate is measured |
| `skip_pii_creative_realtime` | Do not cache personal/account, creative, or live-moving values |
| `shadow_then_promote` | Log would-be hits in shadow mode; validate before write-back |

## Random Timer proxies (operating budget hard cap — no Redis/vector SaaS)

Do **not** buy managed cache/vector products for this layer. Local proxies:

- Exact-match fingerprint helper in `scripts/llm_response_cache_gate.py`
- Gate decisions for cache vs miss vs no-cache categories
- Fixture: `marketing/data/code_health/llm_response_cache_discipline.json`
- Pair with Workflow Economics (completion loop) and Diff Delta (durable yield)

## Fitness

```bash
python3 scripts/llm_response_cache_gate.py --json
```

## Explicitly rejected

- Claiming savings without a measured hit rate
- Caching PII / account-specific answers across callers
- Caching creative or real-time (prices, live inventory) answers
- Treating provider prompt-cache discounts as response-cache skips
- Paid Redis / vector DB under the monthly hard cap when an in-process/file store suffices
