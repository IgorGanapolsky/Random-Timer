# HydraFusion-style agent orchestration

**Source:** [Project HydraFusion: Frontier quality via multi-model orchestration](https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/) (GitHub Blog, 2026-09-04)

**Digest:** [InfoQ — GitHub Copilot's Project HydraFusion](https://www.infoq.com/news/2026/09/github-hydrafusion/) (2026-09-13) — Single / Cascade / Critique + five operating principles + offline cost/quality numbers.

**Local implementation (zero incremental SaaS spend):**

| Artifact | Role |
| --- | --- |
| `scripts/hydrafusion_route.py` | Deterministic Single / Cascade / Critique planner + quality gate |
| `scripts/hydrafusion_routing_gate.py` | Presence + claim gate (anti always-frontier / tooling critic / unvalidated apply) |
| `scripts/tests/test_hydrafusion_route.py` | Router TDD coverage |
| `scripts/tests/test_hydrafusion_routing_gate.py` | Gate TDD coverage |
| `docs/HYDRAFUSION_ROUTING.md` | InfoQ-facing operating brief |
| `.claude/rules/agent-model-matching.md` | Categories, principles, prompt styles |
| `.cursor/rules/hydrafusion-orchestration.mdc` | Always-on Cursor reminder |

## Operator cheat sheet

```bash
# Plan a task
python3 scripts/hydrafusion_route.py \
  --task "Implement Play Billing Library 8 upgrade with unit tests" \
  --risk medium --files 8 \
  --capabilities code_generation,debugging

# Evaluate cascade gate signals
python3 scripts/hydrafusion_route.py --evaluate-gate '{"tests_passed":true,"evidence_present":true,"secrets_leaked":false,"patch_validated":true}'
```

## What we deliberately did not buy

GitHub Copilot HydraFusion research preview seats — would risk the **$20/mo** operating
budget. This repo copies the **workflow math** (least-complex pattern + isolated critique +
fail-safe apply), not the paid product.
