# AgentZip Memory (lite) — compress redundant agent-sandbox pages

Operating brief from [elvis @omarsar0 on X](https://x.com/omarsar0/status/2098531286319341932) summarizing HKUST **AgentZip** ([arXiv 2609.11294](https://arxiv.org/abs/2609.11294); DAIR chat: [academy.dair.ai papers](https://academy.dair.ai/papers)):

> Parallel agent sandboxes for RL/evals share templates and related trajectories. Measured **76–96%** pages with template-relative or cross-sandbox redundancy. Compressing against the template **and** sibling sandboxes drops sandbox-owned memory by up to **8.7×** (vs ~2.1× Linux). Run expensive compression during **LLM wait**; prefetch on restore. Aggressive compression alone ~3.1× slowdown; scheduling + prefetch → ~**1.40×**.

## Anti-pattern

**High-fanout without memory discipline** — spawning many concurrent sandboxes/worktrees that each hold full template copies, then claiming “parallelism” while the box OOMs or hangs (often misread as a hang, not OOM).

## Health signals (required)

| Signal | Meaning here |
|--------|----------------|
| `share_template_not_full_forks` | Prefer one template + deltas over N full environment clones |
| `compress_during_llm_wait` | Heavy compress/dedupe work runs in LLM idle windows |
| `cap_fanout_before_oom` | Bound concurrent sandboxes/worktrees to measured RAM headroom |
| `measure_redundancy_before_scale` | Never claim × memory wins without a measured redundancy/hit rate |

## Random Timer proxies (hard monthly budget — no AgentZip product)

Do **not** buy specialized sandbox-compression products. Local proxies:

- Cap concurrent agent worktrees / Task fanout
- Prefer shared checkout + path-scoped edits over full clones
- Run expensive cleanup during model wait (not on the critical path)
- Fixture: `marketing/data/code_health/agentzip_memory_discipline.json`

## Fitness

```bash
python3 scripts/agentzip_memory_gate.py --json
```

## Explicitly rejected

- Unbounded parallel sandboxes without a memory budget
- Claiming 8.7× (or any ×) without measuring redundancy
- Paying for AgentZip / similar SaaS under the hard monthly cap
- Ignoring 1.4× slowdown when trading memory for latency
