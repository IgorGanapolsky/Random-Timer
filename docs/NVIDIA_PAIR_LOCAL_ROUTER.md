# NVIDIA PAIR Local Router lite

Canonical upstream: [NVIDIA/Personal-AI-Router](https://github.com/NVIDIA/Personal-AI-Router) (Apache-2.0; releases `NVPAIR-Setup-*.dmg` / `.deb` / `.exe`).

Blog: [NVIDIA PAIR Virtual Inference Router](https://developer.nvidia.com/blog/nvidia-pair-virtual-inference-router-expands-available-compute-on-your-local-network/).

Digest: [InfoQ](https://www.infoq.com/news/2026/09/nvidia-pair-ai-task-router/).

**PAIR** is a virtual inference router — not a new engine. Ollama or LM Studio still runs the model. PAIR **proxies** the familiar local interface (`ollama-pr` on `:11434`, engine on `:11435`), discovers paired home/LAN/Tailscale nodes, and schedules each **independent** request to **one eligible node**. Multi-agent / Hermes subagent fanout stops queueing on a single GPU.

Ground truth for multi-node: **Jobs / Workloads UI**, or macOS `~/Library/Application Support/Nvidia Corporation/Personal AI Router/workloads-history.json` (`scheduledOn` distinct > 1). Never claim multinode from agent count alone.

## Anti-pattern

Point every subagent at one Ollama instance, claim “cluster speedup” from agent count alone, merge GPUs / pool VRAM, or rewrite the harness to a new cluster API.

## Highest-ROI steals (binding, $0)

| Improvement | Why it pays back |
|-------------|------------------|
| Proxy familiar interface | Harness keeps `baseUrl` → PAIR :11434 — no API rewrite |
| Workload-level concurrency | Parallel independent jobs → different nodes |
| One request, one node | No VRAM pooling; no single-request shard |
| Elastic home nodes | Mini / laptop sleep & rejoin; schedule around readiness |
| Eligibility filter | Online + engine + exact model + load / GPU util |
| Jobs / workloads-history | Multi-node only when `scheduledOn` spans >1 node |
| Tailscale / LAN pairing | Secure home mesh without paid GPU SaaS |
| S25 as edge Ollama | Termux + Ollama on Tailscale — **not** native PAIR OS |

## Fleet (this repo)

| Node | Role | PAIR native? | Notes |
|------|------|--------------|-------|
| MacBook Pro | primary + PAIR proxy | yes (Apple silicon) | Verified: `ollama-pr` :11434, engine :11435, chat `PAIR_OK` |
| Mac mini (`100.94.135.78`) | spare PAIR/Ollama | yes | Pair via Tailscale + Cluster 6-digit PIN |
| Galaxy S25 | edge Ollama | **no** | Termux/Ollama when online; not PAIR.app |

## Pipeline

```text
Hermes / Cursor / OpenClaw  →  PAIR proxy ollama-pr (:11434)
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              MacBook Ollama   Mac mini Ollama   S25 Termux Ollama
              (native PAIR)    (native PAIR)     (edge, not PAIR.app)
```

## Fitness

```bash
python3 scripts/nvidia_pair_local_router_gate.py --json
# Live probe of localhost proxy before placement (default):
python3 scripts/nvidia_pair_fleet.py --jobs 5 --model qwen2.5:3b-hermes-64k --json
# Jobs ground truth from Personal-AI-Router workloads-history:
python3 scripts/nvidia_pair_workloads.py --json
```

Local smoke (official OpenAI-compatible path):

```bash
lsof -nP -iTCP:11434,11435 -sTCP:LISTEN   # expect ollama-pr :11434 ; ollama :11435
curl -sS http://127.0.0.1:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5:3b-hermes-64k","messages":[{"role":"user","content":"Reply with exactly: PAIR_OK"}],"max_tokens":16,"temperature":0}'
```

Install / upgrade: [GitHub releases](https://github.com/NVIDIA/Personal-AI-Router/releases) (current: v0.1.1). Do not run `PAIR.app` and `nvpair-tui` at the same time.

## Explicitly rejected

- Paid remote GPU SaaS under the $20/mo hard cap
- Claiming multi-node without Jobs / workloads-history
- VRAM pooling / sharding one request across machines
- New cluster SDK in the agent harness
- Treating Galaxy S25 as a native PAIR app target
