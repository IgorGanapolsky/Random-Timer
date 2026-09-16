# LLM Observability lite

Source: [Datadog — Best Practices for Monitoring, Optimizing, and Securing Your LLM Applications](https://lp.datadoghq.com/rs/875-UVY-685/images/eBook-LLMObservabilityBestPractices.pdf?version=1) (PDF).

Steal the **practices**, not a paid Datadog default. Under the **$20/mo hard cap**, prefer PostHog, local traces/logs, and existing CI evidence.

## Anti-pattern

Ship LLM/agent features with no error/latency/token visibility, no security signals, no quality evals, and no end-to-end traces → slow MTTR, silent cost burn, and undetected prompt-injection / PII leaks (“flying blind”).

## Highest-ROI steals (binding)

| Practice | Why it makes money faster |
|----------|---------------------------|
| Operational metrics: errors, latency, request volume | Stability; alert before outages eat conversion |
| Token usage + cost-per-query + budget alerts | Stays under hard monthly cap |
| Prompt injection / toxic / unauthorized-behavior signals | Stops security incidents that kill trust and launches |
| PII scrub or detect on prompts/responses | Avoids leakage and compliance hits |
| Functional quality evals (failure to answer, toxicity, sentiment, custom) | Quality without waiting for store reviews |
| End-to-end chain/agent tracing | Faster root cause across RAG, tools, LLM calls |
| Prefer free/local/PostHog surfaces | Zero incremental SaaS until a named hard job needs it |

## Random Timer binding

- PostHog remains primary product telemetry (WQTU, paywall funnel).
- Agent/LLM runs should carry correlation IDs and step-level outcomes when practical.
- Do not claim “observability ready” without errors + latency + token/cost tracking.

## Fitness

```bash
python3 scripts/llm_observability_gate.py --json
```

## Explicitly rejected

- Default paid Datadog Agent Observability under the monthly hard cap
- Ignoring token/cost metering
- Quality claims without evals
- Debugging multi-step agents without end-to-end traces
