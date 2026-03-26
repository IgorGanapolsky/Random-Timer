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

## Memory Gateway

The project memory backend is `mcp-memory-gateway`, not ad hoc local RAG claims.

Evidence-first workflow:
```bash
make memory-doctor
make memory-summary
make memory-lessons Q="verification"
```

When a session contains a confirmed mistake or correction, capture it with one sentence of context:
```bash
make memory-capture-down CONTEXT="Unverified browser-state claim" TAGS="truthfulness,verification"
```

Rules:
- Do not claim the memory system is active until `make memory-doctor`, `make memory-summary`, and `make memory-lessons` all read back successfully.
- Use `.mcp.json` as the Codex/Cursor MCP source of truth for the `rlhf` server.
- Treat `.rlhf/config.json` as tracked project config and `.rlhf/*.jsonl` / derived analytics as local runtime state.
