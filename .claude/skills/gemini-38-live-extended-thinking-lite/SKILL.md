---
name: gemini-38-live-extended-thinking-lite
description: Dual-mode Gemini 3.8 Live vs Extended Thinking — early ack, progress narration, background tools, budget-gated Live API (docs/GEMINI_38_LIVE_EXTENDED_THINKING.md).
---

# Skill: gemini-38-live-extended-thinking-lite

Follow `docs/GEMINI_38_LIVE_EXTENDED_THINKING.md`.

```bash
python3 scripts/gemini_38_live_extended_thinking_gate.py --json
```

Rules:
1. Route simple/cost-sensitive turns to **Live**; complex/multi-step/agentic to **Extended Thinking**.
2. Early verbal cue (“Let me check that…”) before long work.
3. Extended Thinking: live progress narration while tools run in the background.
4. Never default to paid Live API under the $20/mo hard cap — prefer free/subscription surfaces; budget-gate API.
5. Visual grounding only when a frame is available; SynthID-aware for AI audio.
