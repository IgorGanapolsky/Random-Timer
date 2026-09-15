# GPT-6 Astra Harness lite

Source: [InfoQ — OpenAI Releases GPT-6 Astra for Coding and Computer Use](https://www.infoq.com/news/2026/09/openai-gpt6-astra/) (Daniel Dominguez, 2026-09-10).

Astra targets computer use, coding, professional workflows, science, and cybersecurity (critical preparedness level). InfoQ cites OSWorld 2.0 **72.6%**, Terminal-Bench 4.0 **57.9%**, hallucination **4.2%**, and Codex **searchable notes across context windows**. Highest ROI for Random Timer under the **$20/mo hard cap** is stealing **harness patterns**, not defaulting to the paid `gpt-6-astra` API.

## Anti-pattern

Default every turn to Astra API + dump all tools + rely on chat compaction + invent APIs for Play/ASC UIs + retry the same failed click four times with no new evidence → spend and loops without reliability.

## Highest-ROI bets (binding)

| Improvement | Why it pays back |
|-------------|------------------|
| Computer-use first when UI exists without a reliable API | Matches Astra OSWorld strength; unblocks Play/ASC/GitHub settings |
| Searchable session notes (not compaction alone) | Codex-style retrieval of requirements/tests/tool outputs across windows |
| Confirm consequential actions | Publish / force-push / send / deploy need approval |
| Tool search on demand | Avoid stuffing entire MCP catalogs into context |
| Evidence before retry; max 4 identical failures | Cuts token waste and thrash |
| Cybersecurity defensive only | Astra critical cyber: production restricts offense — we hard-block |
| Monitorability via evidence trails | Counter harder-to-monitor reasoning; lower hallucination claims |
| Budget-gate Astra API | Local/subscription first; named hard job + remaining budget only |
| Stay in scope | Do not expand past the CEO task (Astra alignment lesson) |

## Surfaces

```text
has_ui && !reliable_api  → computer_use
reliable_api             → cli_or_api
coding without UI        → coding_cli
```

## Fitness

```bash
python3 scripts/gpt6_astra_harness_gate.py --json
```

Example session notes: `marketing/data/session_notes/astra_harness_example.md`.

## Explicitly rejected

- Defaulting to paid Astra API under the hard monthly cap
- Offensive cyber / exploit development
- Compaction-only memory without searchable notes
- Full tool-catalog dumps
- Unconfirmed store publish / force-push / outbound send
- Inventing APIs when a logged-in UI path exists
- Claims without evidence
