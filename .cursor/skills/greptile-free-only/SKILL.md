---
name: greptile-free-only
description: Keep Greptile free-only — never pay; disable reviews on private and under-50-star public repos (docs/GREPTILE_FREE_ONLY.md).
---

# Skill: greptile-free-only

Follow `docs/GREPTILE_FREE_ONLY.md`.

```bash
python3 scripts/greptile_free_only_gate.py --json
```

Rules:
1. Never add a Greptile payment method or flex/paid credits.
2. Disable reviews on private repos and public repos with &lt;50 stars.
3. Prefer label filter `needs-greptile-review` on free-eligible repos only.
4. Paid credit usage was a mistake — free-tier only going forward.
