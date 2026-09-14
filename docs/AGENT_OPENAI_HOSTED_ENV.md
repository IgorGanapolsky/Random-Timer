# OpenAI-hosted sandbox environment policy

Source: [OpenAI-hosted sandboxes](https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted)

## What we adopted

| Rule | Fleet behavior |
|---|---|
| Prefer local | Use `openai_hosted` only when isolated Linux is required and budget allows |
| Network default | `disabled` (safe + cheap). `restricted` = exact hostnames only |
| Secrets | Never put `OPENAI_API_KEY`, `PATH`, or `CODEX_*` in sandbox `env` |
| Setup | Nonzero `setup_commands` exit blocks agent start |
| Readiness | Wait for environment `connected` before live file ops |
| Outputs | Write under `/workspace/outputs`, then publish into the artifact vault |
| Templates | Session cannot broaden template network policy |
| Cleanup | Delete session when done; retry `409` while setup/execution finishes |
| Budget | Hosted container + model spend counted against **$20/mo** fleet cap |

## CLI

```bash
python3 scripts/agent_openai_hosted_env.py doctor
python3 scripts/agent_openai_hosted_env.py route --outputs
python3 scripts/agent_openai_hosted_env.py route --isolated-linux --outputs --mtd-usd 1 --est-usd 0.5
python3 scripts/agent_openai_hosted_env.py build-request \
  --input "Sum amounts.csv into /workspace/outputs/summary.json" \
  --network disabled
python3 scripts/agent_openai_hosted_env.py publish-outputs \
  --vault /tmp/artifact-vault \
  --run-id hosted-summary \
  --outputs-dir /tmp/outputs \
  --code /tmp/code.py \
  --trace-json /tmp/trace.json \
  --pre-text /tmp/transcript.txt
```

## Related

- Compaction-safe vault: `scripts/agent_artifact_transparency.py`
- Local-first router: `scripts/agent_local_first_router.py`

## Evidence status

Policy + unit tests landed. Live Agents API session create against OpenAI: **not verified** this turn (avoids unbudgeted container spend).
