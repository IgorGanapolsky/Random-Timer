## RLHF Project Config

Tracked files:
- `config.json`: project-local `mcp-memory-gateway` config

Ignored runtime state:
- `*.jsonl` feedback, memory, telemetry, and audit logs
- derived analytics such as `feedback-summary.json` and `risk-model.json`

Verification:
```bash
make memory-doctor
make memory-summary
make memory-lessons Q="verification"
```
