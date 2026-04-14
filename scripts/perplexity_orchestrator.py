#!/usr/bin/env python3
"""Perplexity Sonar + Claude/Amp skill orchestrator.

Calls the Perplexity Sonar API for real-time web research, then feeds
results into local Claude/Amp skill workflows.  The API key is read
from the PERPLEXITY_API_KEY environment variable (never hardcoded).

Usage:
    python scripts/perplexity_orchestrator.py --query "latest React Native performance tips"
    python scripts/perplexity_orchestrator.py --query "App Store review guidelines 2026" --model sonar-pro
    python scripts/perplexity_orchestrator.py --test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SONAR_MODELS = {
    "sonar": "sonar",
    "sonar-pro": "sonar-pro",
    "sonar-reasoning": "sonar-reasoning",
    "sonar-reasoning-pro": "sonar-reasoning-pro",
}

API_URL = "https://api.perplexity.ai/chat/completions"

DEFAULT_SYSTEM_PROMPT = (
    "You are a research assistant integrated with Claude/Amp developer workflows. "
    "Provide concise, actionable answers with source citations. "
    "Focus on technical accuracy and include code examples when relevant."
)


def _get_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        print("ERROR: PERPLEXITY_API_KEY not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(1)
    return key


def query_sonar(
    query: str,
    *,
    model: str = "sonar",
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict:
    """Send a query to the Perplexity Sonar API and return the parsed response."""
    api_key = _get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def format_response(data: dict) -> str:
    """Extract and format the assistant reply + citations."""
    lines: list[str] = []
    choice = data.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "(no content)")
    lines.append(content)

    citations = data.get("citations", [])
    if citations:
        lines.append("\n--- Sources ---")
        for i, url in enumerate(citations, 1):
            lines.append(f"  [{i}] {url}")

    usage = data.get("usage", {})
    if usage:
        lines.append(
            f"\n[tokens] prompt={usage.get('prompt_tokens', '?')}  "
            f"completion={usage.get('completion_tokens', '?')}"
        )
    return "\n".join(lines)


def run_self_test() -> bool:
    """Quick smoke test: hit the API with a trivial query and verify structure."""
    print("Running self-test against Perplexity Sonar API...")
    try:
        data = query_sonar("What is 2+2? Answer in one word.", max_tokens=64)
        content = data["choices"][0]["message"]["content"]
        model_used = data.get("model", "unknown")
        usage = data.get("usage", {})
        print(f"  Model:      {model_used}")
        print(f"  Response:   {content[:200]}")
        print(f"  Prompt tk:  {usage.get('prompt_tokens', '?')}")
        print(f"  Compl. tk:  {usage.get('completion_tokens', '?')}")
        print("SELF-TEST PASSED ✅")
        return True
    except Exception as exc:
        print(f"SELF-TEST FAILED ❌  {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from repo_dotenv import load_repo_dotenv

        load_repo_dotenv(repo_root)
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Perplexity Sonar + Claude/Amp orchestrator")
    parser.add_argument("--query", "-q", type=str, help="Research query to send")
    parser.add_argument("--model", "-m", type=str, default="sonar", choices=SONAR_MODELS.keys())
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    args = parser.parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.query:
        parser.error("--query is required (or use --test)")

    data = query_sonar(args.query, model=args.model)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_response(data))


if __name__ == "__main__":
    main()
