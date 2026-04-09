#!/usr/bin/env bash
# Setup script for Mac Mini Local AI Forge (llama.cpp + local OpenAI-compatible endpoints)
# Run this once on the Mac Mini to download and start the local LLM servers.

set -euo pipefail

echo "=========================================================="
echo "🚀 Bootstrapping Mac Mini Autonomous Forge..."
echo "=========================================================="

mkdir -p ~/.local_forge/models
cd ~/.local_forge

# 1. Install llama.cpp (Metal optimized for M-Series)
if [ ! -f "llama-server" ]; then
    echo "⬇️ Downloading pre-compiled llama-server for macOS ARM64..."
    curl -L -o llama.zip "https://github.com/ggerganov/llama.cpp/releases/latest/download/llama-b4121-bin-macos-arm64.zip"
    unzip -o llama.zip
    rm llama.zip
fi

# 2. Download Qwen3-Coder (The Workhorse - Fast Edits)
QWEN_URL="https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF/resolve/main/qwen2.5-coder-32b-instruct-q4_k_m.gguf"
if [ ! -f "models/qwen3-coder-32b.gguf" ]; then
    echo "⬇️ Downloading Qwen3-Coder 32B (Q4_K_M)..."
    curl -L -o "models/qwen3-coder-32b.gguf" "$QWEN_URL"
fi

# 3. Download Kimi 2.5 (The Architect - Deep Reasoning)
# Note: Using an equivalent deep reasoning model proxy until official Kimi GGUFs are public, using DeepSeek R1 Distill as placeholder
KIMI_URL="https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf"
if [ ! -f "models/kimi-architect-32b.gguf" ]; then
    echo "⬇️ Downloading Kimi/Architect 32B (Q4_K_M)..."
    curl -L -o "models/kimi-architect-32b.gguf" "$KIMI_URL"
fi

echo "=========================================================="
echo "✅ Forge Provisioned. Starting API Servers via tmux..."
echo "=========================================================="

# Create tmux session to keep servers running in background
tmux new-session -d -s forge_servers

# Window 0: Qwen3 Workhorse on Port 8001
tmux rename-window -t forge_servers:0 'Qwen-Workhorse'
tmux send-keys -t forge_servers:0 "./llama-server -m models/qwen3-coder-32b.gguf --port 8001 --ctx-size 32768 --parallel 4 -ng 99" C-m

# Window 1: Kimi Architect on Port 8002
tmux new-window -t forge_servers -n 'Kimi-Architect'
tmux send-keys -t forge_servers:1 "./llama-server -m models/kimi-architect-32b.gguf --port 8002 --ctx-size 32768 --parallel 2 -ng 99" C-m

echo "🟢 Qwen3-Coder running on http://localhost:8001"
echo "🟢 Architect running on http://localhost:8002"
echo "Attach to view logs: tmux attach -t forge_servers"
echo ""
echo "Point any OpenAI-compatible client at http://localhost:8001 (or 8002) using OPENAI_API_BASE."
