# Growth Content Artifacts

This folder is managed by `scripts/growth_content_pipeline.py` and `.github/workflows/daily-growth-publishing.yml`.

- `posts/`: source markdown posts
- `diagrams/`: PaperBanana-style diagram assets (`.svg`, `.mmd`)
- `data/`: publication + engagement logs (`.jsonl`)
- `keywords/`: seed/modifier strategy and BID-scored keyword backlog
- `site/`: generated static site deployed to GitHub Pages

Do not store secrets here. API keys/tokens are pulled from GitHub Actions secrets.
