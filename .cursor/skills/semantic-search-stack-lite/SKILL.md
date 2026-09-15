---
name: semantic-search-stack-lite
description: LinkedIn-style retrieve→rank search stack with depth control and product-policy eval (docs/SEMANTIC_SEARCH_STACK.md).
---

# Skill: semantic-search-stack-lite

Follow `docs/SEMANTIC_SEARCH_STACK.md`. Source: https://www.linkedin.com/blog/engineering/search/reimagining-linkedins-search-stack

```bash
python3 scripts/semantic_search_stack_gate.py --json
```

Rules:
1. **Retrieve then rank** — never score the full corpus with a frontier model.
2. **Depth controller** — `rank_k` must be ≤ `retrieve_k` and controlled for large sets.
3. **Route** keyword (entities) vs semantic (ambiguous NL) vs hybrid.
4. **Product policy + golden** before claiming search quality (precision/recall/NDCG).
5. **Score cache + explainability snippets**.
6. Prefer local hybrid (zvec/FTS) — no paid GPU exhaustive search SaaS under the hard cap.
