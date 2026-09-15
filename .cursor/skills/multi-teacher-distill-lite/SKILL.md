---
name: multi-teacher-distill-lite
description: LinkedIn/InfoQ multi-teacher offline distillation with per-shard cache, stability switch, prune+compress (docs/MULTI_TEACHER_DISTILL.md).
---

# Skill: multi-teacher-distill-lite

Follow `docs/MULTI_TEACHER_DISTILL.md`.

- Primary: https://www.linkedin.com/blog/engineering/infrastructure/the-training-infrastructure-behind-ai-powered-job-search-eight-x-faster-multi-teacher-distillation
- Digest: https://www.infoq.com/news/2026/09/linkedin-ai-multi-teacher/

```bash
python3 scripts/multi_teacher_distill_gate.py --json
```

Rules:
1. **Offline first** — cache teacher soft labels/embeddings; iterate the student without re-running teachers.
2. **Per-shard invalidation** — never all-or-nothing teacher cache clears.
3. **Pluggable teachers** — relevance | engagement | embedding | policy | click | critic.
4. **Compact student for serving** — distill into skills/gates/fixtures; do not serve teacher fleets live.
5. **Stream, don’t full-stage** the corpus each run.
6. **Online while exploring** teachers; **offline when stable** (InfoQ).
7. **Compound gains** — stack moderate local wins; do not default FP8 on small models.
8. **Prune + compress** student serving; demand **NDCG** (or peer) before quality claims.
9. No GPU multi-node training SaaS under the hard monthly cap.
