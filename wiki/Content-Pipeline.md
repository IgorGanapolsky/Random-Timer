# Content Pipeline

Daily automated blog publishing with keyword targeting and engagement tracking.

## Daily Flow (13:15 UTC)

```
1. Keyword Plan     → Select daily keyword from BID-score backlog
2. Generate Post    → Build markdown (commits + keyword + rotating sections)
3. Build Site       → GitHub Pages: HTML, sitemap.xml, llms.txt, agents.md
4. Publish          → DEV.to, LinkedIn, X/Twitter
5. Engagement       → Collect metrics from platform APIs
6. Deploy           → Push to GitHub Pages (develop branch)
```

## Post Structure

Each generated post includes:
- **What changed today** — Recent git commit summaries
- **AI/LLM flow** — How AI tools contributed
- **Metrics** — Build/test/deploy stats
- **FAQ for AI assistants** — Structured for `llms.txt` consumption

## UTM Links in Posts

Every app store link is tagged:
```
https://apps.apple.com/...?utm_source=github_pages&utm_medium=organic&utm_campaign=daily_blog_20260220&utm_content=daily_blog
```

## Engagement Collection

| Platform | Method | Metrics |
|----------|--------|---------|
| DEV.to | API | Views, reactions, comments |
| X/Twitter | API | Impressions, engagements |
| Bot traffic | Log analysis | AI crawler hits by type/model/path |

### Bot Traffic Classification

`growth_bot_analytics.py` classifies user agents:
- **AI Training:** OpenAI, Anthropic, Google crawlers
- **AI Retrieval:** Perplexity, ByteDance
- **Search Crawler:** Googlebot, Bingbot, Meta

## Source Files

- `scripts/growth_content_pipeline.py` — Full pipeline
- `scripts/growth_keyword_engine.py` — Keyword BID scoring
- `scripts/growth_bot_analytics.py` — Bot traffic analysis
- `marketing/data/posts.jsonl` — Post index
- `.github/workflows/daily-growth-publishing.yml` — Daily 13:15 UTC
