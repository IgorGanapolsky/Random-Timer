---
name: nvidia-pair-local-router-lite
description: NVIDIA PAIR local inference router — proxy Ollama/LM Studio, schedule independent jobs across Mac/mini/S25 edge (docs/NVIDIA_PAIR_LOCAL_ROUTER.md).
---

# Skill: nvidia-pair-local-router-lite

Follow `docs/NVIDIA_PAIR_LOCAL_ROUTER.md`.

- Primary: https://developer.nvidia.com/blog/nvidia-pair-virtual-inference-router-expands-available-compute-on-your-local-network/
- Digest: https://www.infoq.com/news/2026/09/nvidia-pair-ai-task-router/

```bash
python3 scripts/nvidia_pair_local_router_gate.py --json
python3 scripts/nvidia_pair_fleet.py --jobs 5 --model qwen2.5:3b-hermes-64k --json
```

Rules:
1. Keep harness on PAIR proxy (`http://127.0.0.1:11434`) — no new cluster API.
2. One independent request → one eligible node (engine + exact model + ready).
3. Never claim multi-node without Jobs/telemetry on >1 node.
4. No VRAM pooling / single-request sharding.
5. MacBook + Mac mini = native PAIR peers via Tailscale/LAN.
6. Galaxy S25 = Termux/Ollama **edge** only (`native_pair=false`).
7. No paid remote GPU under the $20/mo hard cap.
