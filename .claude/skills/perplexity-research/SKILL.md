---
name: perplexity-research
description: Real-time web research via Perplexity Sonar API integrated with Claude/Amp workflows. Use when user needs live web data, current documentation, market research, or competitor analysis.
triggers:
  - "research"
  - "search the web for"
  - "what's the latest on"
  - "perplexity"
  - "sonar"
  - "live search"
---

# Perplexity Research Skill

## Overview
Calls the Perplexity Sonar API for real-time web research, returning cited answers that feed into Claude/Amp workflows.

## Prerequisites
- `PERPLEXITY_API_KEY` set in `.env` (already configured ✅)
- Python 3 with `requests` package (already installed ✅)

## Usage

### From CLI
```bash
# Quick research query
python3 scripts/perplexity_orchestrator.py --query "your question here"

# Use stronger model
python3 scripts/perplexity_orchestrator.py --query "complex topic" --model sonar-pro

# Raw JSON output for piping
python3 scripts/perplexity_orchestrator.py --query "topic" --json

# Self-test
python3 scripts/perplexity_orchestrator.py --test
```

### From Claude/Amp
When a user asks for live web research, run:
```bash
source .env && export PERPLEXITY_API_KEY && python3 scripts/perplexity_orchestrator.py --query "<user query>"
```

### Available Models
| Model | Use Case |
|-------|----------|
| `sonar` | Fast, general research (default) |
| `sonar-pro` | Deeper analysis, longer answers |
| `sonar-reasoning` | Step-by-step reasoning with citations |
| `sonar-reasoning-pro` | Complex multi-step research |

## Integration with Claude/Amp Skills
This skill augments existing workflows:
- **Growth pipeline**: Feed market research into `growth_content_pipeline.py`
- **Release context**: Research App Store guideline changes before releases
- **North Star tracking**: Research competitor benchmarks and industry baselines

## Limitations
- Perplexity Computer (cloud worker) is NOT controllable via this API — it's a separate Perplexity product requiring their web UI
- Comet browser is a Perplexity-internal component, not externally launchable
- API rate limits apply per your Perplexity subscription tier
- HTTP **401** from `api.perplexity.ai` may mean **`insufficient_quota`** (plan/billing), not a missing key — check [Perplexity API settings](https://www.perplexity.ai/settings/api). Scripts must load `.env` via `repo_dotenv` (or export `PERPLEXITY_API_KEY`) because bare `os.environ` in CI/agents often has no key.
