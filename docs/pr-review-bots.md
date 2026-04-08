# PR review automation (live tooling)

This table is the **evidence-based** summary of bots and checks on pull requests. For branch rules and CI layout, see [`.github/INFRASTRUCTURE.md`](../.github/INFRASTRUCTURE.md) and [`ci.yml`](../.github/workflows/ci.yml).

| Bot / service | Role | Repo evidence |
|---------------|------|----------------|
| **Seer (Sentry)** | Safety / error-handling review comments | `.github/seer.app.yml`, `Seer Code Review` check |
| **Claude Review** | PR review + assist flows | `.github/workflows/claude-review.yml` |
| **GitHub Copilot code review** | PR review (branch rules) | Branch rulesets with `copilot_code_review` |
| **SonarQube Cloud** | Quality gate, PR decoration | `SonarCloud Code Analysis` check |
| **Cursor** | `@cursor` / BugBot (per org setup) | `BUGBOT.md`, Cursor docs |

Update this doc when tooling changes; do not duplicate long benchmark tables here — see `CLAUDE.md` for North Star and budget context.
