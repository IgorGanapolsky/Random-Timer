# Multi-Teacher Distill lite

Source: [The training infrastructure behind AI-Powered Job Search: 8X faster multi-teacher distillation](https://www.linkedin.com/blog/engineering/infrastructure/the-training-infrastructure-behind-ai-powered-job-search-eight-x-faster-multi-teacher-distillation) (LinkedIn Engineering).

LinkedIn’s job-search ranking uses **multi-teacher** knowledge distillation: specialized teachers (relevance soft labels, engagement multi-task targets, embedding representations) train a compact **student** SLM that meets a hard serving latency budget. The infrastructure win is **offline distillation** — cache teacher outputs keyed by model version + data fingerprint with **per-shard** invalidation, then iterate the student without re-running teachers (~45h → &lt;5h, ~**8x**). **Online** co-locates teachers with the student; a **unified** framework shares plumbing. Prefer **stream** reads over staging the full corpus.

## Anti-pattern

Re-run every teacher (or a frontier fleet) on every student/prompt iteration, invalidate caches all-or-nothing, and serve multi-billion teachers at query time → cost and latency explode while product iteration stalls.

## Highest-ROI steals (binding, $0)

| Improvement | Why it pays back |
|-------------|------------------|
| Offline teacher-signal cache | Student iterates free of teacher GPUs/API $ |
| Per-shard invalidation | Only regen changed shards; amortize cache gen |
| Pluggable teachers | Swap relevance / engagement / embedding / policy without rewriting the stack |
| Compact student for serving | Distill into skills, gates, fixtures — not live teacher fleets |
| Hard + soft labels | Combine golden/hard grades with teacher soft signals |
| Stream, don’t full-stage | Chunk context; avoid loading the whole corpus each run |
| Unified online/offline | One plumbing path; mode is a parameter |

## Pipeline

```text
Teachers (pluggable) → soft labels + embeddings
       │
       ├─ Online: live alongside student (when teachers/data both change)
       └─ Offline: cache by version+fingerprint → student-only loops (reuse_cache)
```

Local proxies: `docs/LLM_RESPONSE_CACHE.md` (signal cache), HydraFusion Cascade (cheap draft teacher → escalate), Semantic Search Stack (distill ranking teachers), golden product-policy grades.

## Fitness

```bash
python3 scripts/multi_teacher_distill_gate.py --json
```

## Explicitly rejected

- GPU multi-node / FSDP training SaaS under the $20/mo hard cap
- Full teacher re-run on every student iteration
- Serving multi-teacher fleets at query time
- Hardcoded single-teacher assumptions
- All-or-nothing cache invalidation
