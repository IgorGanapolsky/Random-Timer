# Codex Instructions — Random Timer

## Perplexity Agent API Integration

Real-time web research is available via the Perplexity Sonar API.

### Make Targets (recommended)
```bash
make perplexity-search Q="latest iOS 20 changes"
make perplexity-fetch Q="summarize https://developer.apple.com/news/"
make perplexity Q="complex research topic"    # uses pro-search preset
make perplexity-test                          # smoke test
```

### Direct CLI
```bash
source .env && export PERPLEXITY_API_KEY
python3 scripts/perplexity_agent.py --query "your question" --tools web_search
python3 scripts/perplexity_agent.py --query "summarize URL" --tools fetch_url
python3 scripts/perplexity_agent.py --query "topic" --preset pro-search
python3 scripts/perplexity_agent.py --query "topic" --tools web_search fetch_url --json
```

### Models
- `perplexity/sonar` (default, fast)
- Presets: `fast-search`, `pro-search`, `deep-research`

### Key Rule
API key is in `.env` as `PERPLEXITY_API_KEY`. Never hardcode.

## ThumbGate Pro

The project is governed by **ThumbGate Pro**. Feedback is captured as lessons that protect future agents.

Evidence-first workflow:
```bash
make thumbgate-doctor
make thumbgate-summary
make thumbgate-lessons Q="verification"
```

When a session contains a confirmed mistake or correction, capture it with context:
```bash
make thumbgate-capture-down CONTEXT="Unverified browser-state claim"
```

Rules:
- Do not claim the memory system is active until `make thumbgate-doctor`, `make thumbgate-summary`, and `make thumbgate-lessons` all read back successfully.
- Use `.mcp.json` as the Codex/Cursor MCP source of truth for the `thumbgate` server.
- Treat `.thumbgate/config.json` as tracked project config and `.thumbgate/*.jsonl` / contextfs as local runtime state.
