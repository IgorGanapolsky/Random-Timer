# Semantic Search Stack lite

Source: [Reimagining LinkedIn’s search tech stack](https://www.linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack) (Fedor Borisyuk et al., LinkedIn Engineering).

LinkedIn rebuilt search as **semantic**: query understanding → embedding retrieval (broad candidates) → SLM cross-encoder ranking with a **ranking-depth controller**, **score caching**, and continuous **product policy** LLM judges backed by PM **golden** grades (Kappa ≥ 0.8). Precise entity lookups stay on a **keyword** path; ambiguous natural language uses **semantic** (or hybrid). Teachers are **distill**ed into students; long descriptions use **compression** / summarization; matches get **explainability** snippets.

## Anti-pattern

Score every document with a frontier LLM, skip product-policy eval, and deep-rank the entire retrieve set → latency and cost explode without measurable relevance gains.

## Highest-ROI steals (binding, $0)

| Improvement | Why it pays back |
|-------------|------------------|
| Retrieve then rank | Narrow candidates before expensive scoring |
| Ranking depth controller | `rank_k << retrieve_k` |
| Keyword vs semantic routing | Cheap exact lookups; semantic only when ambiguous |
| Product policy + golden grades | Continuous precision / recall / NDCG before quality claims |
| Score caching | Skip unchanged query–doc scores (pairs with LLM Response Cache) |
| Explainability snippets | Show *why* a hit matched |
| Distill, not always-frontier | Pair with HydraFusion Cascade |
| Context compression | Truncate / summarize long docs before rank |

## Pipeline

```text
Query → Understanding → Path(keyword|semantic|hybrid)
      → Retrieve(k) → Rank(depth-controlled) → Explain → Policy eval
```

Local proxies: `zvec_grep` / ripgrep hybrid, `scripts/search_isolation.py`, HydraFusion Cascade for model spend.

## Fitness

```bash
python3 scripts/semantic_search_stack_gate.py --json
```

Golden fixture: `marketing/data/search/product_policy_golden.json`.

## Explicitly rejected

- Ranking the full corpus with a frontier model
- GPU exhaustive-search SaaS under the $20/mo hard cap
- Shipping ranking changes without product-policy eval
- Uncontrolled rank depth on large candidate sets
