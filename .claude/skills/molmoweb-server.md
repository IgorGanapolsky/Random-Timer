---
name: molmoweb-server
description: Start the local MolmoWeb 4B server on Apple Silicon using the installed local checkpoint and hf backend.
user_invocable: true
---

# MolmoWeb Server

Start the local MolmoWeb inference server used by repo-local browser verification.

## Canonical Invocation

From the local `molmoweb` checkout:

```bash
CKPT=./checkpoints/MolmoWeb-4B-infer \
PREDICTOR_TYPE=hf \
PORT=8001 \
uv run uvicorn agent.fastapi_model_server:app --host 127.0.0.1 --port 8001
```

## Environment Contract

- `MOLMOWEB_ENDPOINT=http://127.0.0.1:8001`
- Apple Silicon path uses `PREDICTOR_TYPE=hf`
- Local checkpoint is `./checkpoints/MolmoWeb-4B-infer`

## Validation

After startup, verify with:

```bash
uv run python scripts/test_server.py http://127.0.0.1:8001
```

Then from the Random-Timer repo:

```bash
python3 scripts/molmoweb_browser_verify.py \
  --query "Go to https://example.com and tell me the page title."
```
