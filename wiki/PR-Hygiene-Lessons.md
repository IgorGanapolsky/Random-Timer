# PR Hygiene Lessons

## 2026-05-12

- If a feature PR targets `main` from a branch that is not based on `develop`, close it and rebuild a replacement branch from `origin/develop`; do not retarget a divergent branch and create a noisy PR.
- Treat any PAT exposed in chat or logs as compromised. Do not reuse it, do not store it in repo docs, and use existing `gh` authentication plus per-command Git auth headers instead of token-bearing remotes.
- CI failures can reveal base-branch regressions. Fix the root failing contract in the replacement branch, then rerun the same local and GitHub checks before merge.
- Runtime audio regression tests should read the active pack from `content/pro_audio/runtime/latest.json` rather than hard-coding retired pack IDs.
- External RAG and ML-pipeline logging were not verified in this session; only this repo `wiki/` file was updated.
