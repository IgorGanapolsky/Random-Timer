# PR review automation (live tooling)

This table is the **evidence-based** summary of bots and checks on pull requests. For branch rules and CI layout, see [`.github/INFRASTRUCTURE.md`](../.github/INFRASTRUCTURE.md) and [`ci.yml`](../.github/workflows/ci.yml).

| Bot / service | Role | Enforcement | Repo evidence |
|---------------|------|-------------|----------------|
| **Claude Review** | PR review + assist flows | Required check on protected branches | `.github/workflows/claude-review.yml`, `Claude Review` check |
| **GitHub Copilot code review** | Automatic PR review | GitHub rulesets with `copilot_code_review` on `develop`, `main`, `release/*`, and `hotfix/*` | Branch rulesets + `.github/copilot-instructions.md` |
| **Seer (Sentry)** | Safety / error-handling review comments | Required check plus unresolved AI-thread gate | `.github/seer.app.yml`, `Seer Code Review`, `Autonomous AI Review` |
| **SonarQube Cloud** | Quality gate, PR decoration | Required check on protected branches | `SonarCloud Code Analysis`, `config/sonar-project.properties` |
| **Cursor BugBot** | Bug-first review policy / repo guidance | Policy contract in repo; not a live GitHub status check unless the org-level app is installed separately | `BUGBOT.md` |

Protected-branch baseline:

- `develop`, `main`, `release/*`, and `hotfix/*` require GitHub Copilot code review.
- `develop` and release branches require the core CI gates plus Claude, Seer, Sonar, and platform build/test checks before merge.
- Unresolved AI review threads from Copilot and Sentry fail `Autonomous AI Review`.

Update this doc when tooling changes; do not duplicate long benchmark tables here — see `CLAUDE.md` for North Star and budget context.
