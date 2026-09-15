---
name: gpt6-astra-harness-lite
description: Steal Astra harness patterns—computer-use, session notes, confirm, cyber deny (docs/GPT6_ASTRA_HARNESS.md).
---

# Skill: gpt6-astra-harness-lite

Follow `docs/GPT6_ASTRA_HARNESS.md`. Source: https://www.infoq.com/news/2026/09/openai-gpt6-astra/

```bash
python3 scripts/gpt6_astra_harness_gate.py --json
```

Rules:
1. **Computer-use first** for Play/ASC/GitHub UIs without reliable APIs.
2. **Searchable session notes** — write facts; do not rely on compaction alone.
3. **Confirm** store publish, force-push, Gmail send, production deploy.
4. **Tool search** — do not dump full MCP catalogs.
5. **Retry** only with new evidence; stop after 4 identical failures.
6. **Cyber defensive only** — never develop exploits.
7. **Do not default to Astra API** under the $20/mo cap.
