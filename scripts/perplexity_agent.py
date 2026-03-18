#!/usr/bin/env python3
"""Perplexity Agent API client.

Wraps the /v1/agent endpoint with web_search, fetch_url, and function calling.
API key is read from PERPLEXITY_API_KEY env var (never hardcoded).

Usage:
    python scripts/perplexity_agent.py --query "latest iOS 20 changes" --tools web_search
    python scripts/perplexity_agent.py --query "summarize https://example.com/article" --tools fetch_url
    python scripts/perplexity_agent.py --query "complex research topic" --tools web_search fetch_url --model openai/gpt-5.4
    python scripts/perplexity_agent.py --query "simple question" --preset pro-search
    python scripts/perplexity_agent.py --test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests

AGENT_URL = "https://api.perplexity.ai/v1/agent"

AVAILABLE_MODELS = [
    "perplexity/sonar",
    "perplexity/sonar-pro",
    "perplexity/sonar-reasoning",
    "perplexity/sonar-reasoning-pro",
    "openai/gpt-5.4",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-opus-4",
    "xai/grok-4-1",
    "google/gemini-2.5-pro",
]

PRESETS = ["fast-search", "pro-search", "deep-research"]


def _get_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        print("ERROR: PERPLEXITY_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return key


def _build_tools(tool_names: list[str], domain_filter: list[str] | None = None,
                 recency: str | None = None) -> list[dict]:
    """Build the tools array from human-readable names."""
    tools: list[dict] = []
    for name in tool_names:
        if name == "web_search":
            tool: dict[str, Any] = {"type": "web_search"}
            filters: dict[str, Any] = {}
            if domain_filter:
                filters["search_domain_filter"] = domain_filter
            if recency:
                filters["search_recency_filter"] = recency
            if filters:
                tool["filters"] = filters
            tools.append(tool)
        elif name == "fetch_url":
            tools.append({"type": "fetch_url"})
    return tools


def agent_call(
    query: str,
    *,
    model: str | None = None,
    preset: str | None = None,
    tools: list[str] | None = None,
    instructions: str | None = None,
    domain_filter: list[str] | None = None,
    recency: str | None = None,
    max_output_tokens: int | None = None,
) -> dict:
    """Call the Perplexity Agent API."""
    api_key = _get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {"input": query}

    if preset:
        payload["preset"] = preset
    elif model:
        payload["model"] = model
    else:
        payload["model"] = "perplexity/sonar"

    if tools:
        payload["tools"] = _build_tools(tools, domain_filter, recency)

    if instructions:
        payload["instructions"] = instructions
    elif tools:
        payload["instructions"] = (
            "You have access to web_search and fetch_url tools. "
            "Use web_search for current information. "
            "Use fetch_url when you need full content from a specific URL. "
            "Always cite your sources."
        )

    if max_output_tokens:
        payload["max_output_tokens"] = max_output_tokens

    resp = requests.post(AGENT_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def extract_text(data: dict) -> str:
    """Extract the final text response from the Agent API output."""
    parts: list[str] = []
    for item in data.get("output", []):
        item_type = item.get("type", "")
        if item_type == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text = content.get("text", "")
                    parts.append(text)
                    annotations = content.get("annotations", [])
                    if annotations:
                        parts.append("\n--- Citations ---")
                        for ann in annotations:
                            title = ann.get("title", "")
                            url = ann.get("url", "")
                            parts.append(f"  • {title}: {url}" if title else f"  • {url}")
    return "\n".join(parts)


def format_usage(data: dict) -> str:
    """Format usage/cost info."""
    usage = data.get("usage", {})
    if not usage:
        return ""
    cost = usage.get("cost", {})
    lines = [
        f"[tokens] in={usage.get('input_tokens', '?')} out={usage.get('output_tokens', '?')}",
    ]
    if cost:
        lines.append(f"[cost] ${cost.get('total_cost', 0):.6f} USD")
    return "  ".join(lines)


def run_self_test() -> bool:
    """Smoke test the Agent API with web_search."""
    print("=== Perplexity Agent API Self-Test ===\n")
    tests = [
        ("Basic call (no tools)", {"query": "What is 2+2? One word answer.", "model": "perplexity/sonar", "max_output_tokens": 32}),
        ("web_search tool", {"query": "What day is it today?", "model": "perplexity/sonar", "tools": ["web_search"], "max_output_tokens": 128}),
        ("fetch_url tool", {"query": "Summarize in one sentence: https://docs.perplexity.ai/docs/getting-started/overview", "model": "perplexity/sonar", "tools": ["fetch_url"], "max_output_tokens": 128}),
    ]
    all_ok = True
    for label, kwargs in tests:
        print(f"Test: {label}")
        try:
            data = agent_call(**kwargs)
            text = extract_text(data)
            model_used = data.get("model", "?")
            status = data.get("status", "?")
            print(f"  Status: {status}")
            print(f"  Model:  {model_used}")
            print(f"  Output: {text[:200]}")
            print(f"  {format_usage(data)}")
            if status == "completed":
                print("  ✅ PASS\n")
            else:
                print(f"  ❌ FAIL (status={status})\n")
                all_ok = False
        except Exception as exc:
            print(f"  ❌ FAIL: {exc}\n")
            all_ok = False

    print("ALL TESTS PASSED ✅" if all_ok else "SOME TESTS FAILED ❌")
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Perplexity Agent API client")
    parser.add_argument("--query", "-q", type=str, help="Query to send")
    parser.add_argument("--model", "-m", type=str, default=None, help=f"Model (e.g. {', '.join(AVAILABLE_MODELS[:3])})")
    parser.add_argument("--preset", "-p", type=str, default=None, choices=PRESETS, help="Use a preset instead of model")
    parser.add_argument("--tools", "-t", nargs="+", choices=["web_search", "fetch_url"], help="Tools to enable")
    parser.add_argument("--instructions", type=str, help="Custom system instructions")
    parser.add_argument("--domains", nargs="+", help="Domain filter for web_search (e.g. arxiv.org .edu)")
    parser.add_argument("--recency", choices=["day", "week", "month", "year"], help="Recency filter")
    parser.add_argument("--max-tokens", type=int, default=None, help="Max output tokens")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--test", action="store_true", help="Run self-test suite")
    args = parser.parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.query:
        parser.error("--query is required (or use --test)")

    data = agent_call(
        args.query,
        model=args.model,
        preset=args.preset,
        tools=args.tools,
        instructions=args.instructions,
        domain_filter=args.domains,
        recency=args.recency,
        max_output_tokens=args.max_tokens,
    )

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(extract_text(data))
        print()
        print(format_usage(data))


if __name__ == "__main__":
    main()
