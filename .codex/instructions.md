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
