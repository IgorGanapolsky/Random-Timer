# Multi-Teacher Distill lite

Primary: [The training infrastructure behind AI-Powered Job Search: 8X faster multi-teacher distillation](https://www.linkedin.com/blog/engineering/infrastructure/the-training-infrastructure-behind-ai-powered-job-search-eight-x-faster-multi-teacher-distillation) (LinkedIn Engineering).

Digest: [How LinkedIn Trains AI Job Search 8x Faster with Multi-Teacher Distillation](https://www.infoq.com/news/2026/09/linkedin-ai-multi-teacher/) (InfoQ, Claudio Masolo).

LinkedIn’s job-search ranking uses **multi-teacher** knowledge distillation: specialized teachers (relevance soft labels, engagement multi-task targets, embedding representations) train a compact **student** SLM (0.6B from ~8B relevance + ~1.7B engagement oracles) that meets a hard serving latency budget. The infrastructure win is **offline distillation** — cache teacher outputs keyed by model version + data fingerprint with **per-shard** invalidation, then iterate the student without re-running teachers (~45h → &lt;5h, ~**8x**). **Online** co-locates teachers with the student via an **async** SGLang-style serving loop; a **unified** framework shares plumbing. Prefer **stream** reads over staging the full corpus.

InfoQ emphasizes: query teachers **online** early while teacher choices change; switch to **offline** caching once teachers are **stable** and query volume rises. The **8x** is **compound** moderate gains (LiGer-class memory, multi-node, FSDP2, newer GPUs) — not one trick. **FP8** mixed precision showed **no benefit under ~8B**. Inference-side **structured pruning** + context **compression** lifted ranking throughput ~290 → 2,000+ items/sec/GPU. Demand **NDCG** (or equivalent) evidence before claiming distill wins (InfoQ cites NDCG@10 +24.48%).

## Anti-pattern

Re-run every teacher (or a frontier fleet) on every student/prompt iteration, invalidate caches all-or-nothing, serve multi-billion teachers / frontier LLMs at every ranking request, and default to FP8 on small students → cost and latency explode while product iteration stalls.

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
| Async teacher serving | Overlap teacher inference with student work (SGLang-pattern locally via cache) |
| Stability mode switch | Online while exploring; offline when teachers stable |
| Compound moderate gains | Stack local wins; don’t chase a single silver bullet |
| Reject FP8 default (small) | Casting overhead can erase savings under ~8B |
| Prune + compress serving | Throughput without frontier-per-request |
| Ranking quality evidence | NDCG (or peer metric) before “distill worked” claims |

## Pipeline

```text
Teachers (pluggable, async-served) → soft labels + embeddings
       │
       ├─ Online: explore while teachers change (SGLang-style loop)
       └─ Offline: cache when stable → student-only loops (reuse_cache)
                → prune + compress student for serving
```

Local proxies: `docs/LLM_RESPONSE_CACHE.md` (signal cache), HydraFusion Cascade (cheap draft teacher → escalate), Semantic Search Stack (distill ranking teachers), golden product-policy grades.

## Fitness

```bash
python3 scripts/multi_teacher_distill_gate.py --json
```

## Explicitly rejected

- GPU multi-node / FSDP training SaaS under the $20/mo hard cap
- Full teacher re-run on every student iteration
- Serving multi-teacher / frontier fleets at query time
- Hardcoded single-teacher assumptions
- All-or-nothing cache invalidation
- Default FP8 for small (&lt;~8B) students without measured win
- Distill quality claims without NDCG (or equivalent) evidence
