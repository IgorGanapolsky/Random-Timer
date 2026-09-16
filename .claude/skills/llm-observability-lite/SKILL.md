---
name: llm-observability-lite
description: Monitor LLM/agent ops — errors/latency/tokens, prompt-injection/PII, quality evals, e2e traces, cost alerts; prefer PostHog/local over paid Datadog (docs/LLM_OBSERVABILITY.md).
---

# Skill: llm-observability-lite

Follow `docs/LLM_OBSERVABILITY.md`.

```bash
python3 scripts/llm_observability_gate.py --json
```

Rules:
1. Track errors, latency, and token/cost for LLM/agent runs.
2. Enable prompt-injection / security / PII signals.
3. Functional quality evals — do not claim quality without them.
4. End-to-end chain/agent tracing for MTTR.
5. Prefer PostHog/local; budget-gate paid Datadog under the $20/mo hard cap.
