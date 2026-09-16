# Gemini 3.8 Live + Extended Thinking lite

Source: [Introducing Gemini 3.8 Live and 3.8 Live Extended Thinking](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/) (Google, 2026-09-15).

Google shipped two Live dialogue models: **3.8 Live** (fluid, cost-efficient, visual grounding) and **3.8 Live Extended Thinking** (high-complexity multi-step agentic work that reasons and speaks simultaneously). Tools run in the background while conversation continues. Highest ROI under the **$20/mo hard cap** is **dual-mode routing + narration discipline**, not defaulting to paid Live API.

## Anti-pattern

Default every voice/agent turn to paid Gemini Live API + freeze the dialogue until tools finish + stay silent during long Extended Thinking runs → spend and a stalled UX.

## Highest-ROI steals (binding)

| Improvement | Why it pays back |
|-------------|------------------|
| Dual-mode: Live vs Extended Thinking | Live for scale/cost; Extended Thinking for complex agent workflows |
| Early verbal ack cues | “Let me check that…” keeps turns human while work starts |
| Live progress narration | Extended Thinking walks multi-step background tasks without silence |
| Background tools while speaking | No frozen UI while APIs/tools complete |
| Visual grounding when a frame exists | Near real-time UI/camera context for better answers |
| Barge-in friendly turns | Interruptions are first-class in Live dialogue |
| SynthID audio watermark awareness | Detectable AI audio; honesty for voice outputs |
| Prefer free/subscription surfaces | Gemini app / Workspace Live / AI Studio free tiers first |
| Budget-gate Live API | Named hard job + remaining budget only |

## Routing

```text
simple / cost_sensitive     → live
complex / multi_step / agentic → extended_thinking
visual frame available      → enrich either mode (do not invent vision)
```

## Fitness

```bash
python3 scripts/gemini_38_live_extended_thinking_gate.py --json
```

## Explicitly rejected

- Default paid Gemini Live API under the monthly hard cap
- Freezing dialogue until tools complete
- Silent Extended Thinking / long tool runs without progress narration
- Visual grounding without an available frame
- AI audio claims without SynthID awareness
- Treating Live API as always-on for Random Timer agents
