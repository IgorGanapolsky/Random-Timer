#!/usr/bin/env python3
"""MCP (Model Context Protocol) server wrapping the Perplexity Agent API.

Exposes three tools to Amp/Claude:
  - perplexity_web_search: Real-time web search with citations
  - perplexity_fetch_url: Fetch and summarize a specific URL
  - perplexity_agent: Full multi-model orchestration with all tools

Runs as a stdio-based MCP server.

Usage:
    python scripts/perplexity_mcp_server.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Perplexity Agent API client (inline to keep MCP server self-contained)
# ---------------------------------------------------------------------------

AGENT_URL = "https://api.perplexity.ai/v1/agent"


def _api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        raise RuntimeError("PERPLEXITY_API_KEY not set")
    return key


def _agent_call(payload: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    resp = requests.post(AGENT_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _extract_text(data: dict) -> str:
    parts: list[str] = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    parts.append(c.get("text", ""))
                    for ann in c.get("annotations", []):
                        url = ann.get("url", "")
                        title = ann.get("title", "")
                        parts.append(f"  [{title}]({url})" if title else f"  {url}")
    usage = data.get("usage", {})
    cost = usage.get("cost", {})
    meta = f"\n\n[model={data.get('model','?')} tokens_in={usage.get('input_tokens','?')} tokens_out={usage.get('output_tokens','?')} cost=${cost.get('total_cost',0):.5f}]"
    return "\n".join(parts) + meta


# ---------------------------------------------------------------------------
# MCP Protocol (stdio JSON-RPC 2.0)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "perplexity_web_search",
        "description": "Search the web in real-time using Perplexity's Agent API with web_search tool. Returns cited results from across the internet. Use for current events, latest docs, market data, competitor research.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "model": {"type": "string", "description": "Model to use (default: perplexity/sonar). Options: perplexity/sonar, perplexity/sonar-pro, openai/gpt-5.4, anthropic/claude-sonnet-4, google/gemini-2.5-pro", "default": "perplexity/sonar"},
                "domains": {"type": "array", "items": {"type": "string"}, "description": "Filter to specific domains (e.g. ['arxiv.org', '.edu']). Use '-domain.com' to exclude."},
                "recency": {"type": "string", "enum": ["day", "week", "month", "year"], "description": "Time filter for results"},
                "max_tokens": {"type": "integer", "description": "Max output tokens", "default": 1024},
            },
            "required": ["query"],
        },
    },
    {
        "name": "perplexity_fetch_url",
        "description": "Fetch and extract content from a specific URL using Perplexity's Agent API with fetch_url tool. Use when you have a specific URL and need its full content summarized or analyzed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch and analyze"},
                "instruction": {"type": "string", "description": "What to do with the content (e.g. 'summarize', 'extract key points')"},
                "model": {"type": "string", "description": "Model to use (default: perplexity/sonar)", "default": "perplexity/sonar"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "perplexity_agent",
        "description": "Full Perplexity Agent API call with multi-model orchestration. Supports web_search + fetch_url combined, model fallback chains, presets (fast-search, pro-search, deep-research), and custom instructions. Use for complex research tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The research query or task"},
                "model": {"type": "string", "description": "Model (e.g. openai/gpt-5.4, sonar-pro)"},
                "preset": {"type": "string", "enum": ["fast-search", "pro-search", "deep-research"], "description": "Use a preset instead of model"},
                "tools": {"type": "array", "items": {"type": "string", "enum": ["web_search", "fetch_url"]}, "description": "Tools to enable (default: both)"},
                "instructions": {"type": "string", "description": "Custom system instructions"},
                "max_tokens": {"type": "integer", "description": "Max output tokens"},
            },
            "required": ["query"],
        },
    },
]


def handle_tool_call(name: str, arguments: dict) -> str:
    """Execute a tool call and return the result text."""
    if name == "perplexity_web_search":
        payload: dict[str, Any] = {
            "model": arguments.get("model", "perplexity/sonar"),
            "input": arguments["query"],
            "tools": [{"type": "web_search"}],
            "instructions": "Use web_search for current information. Always cite sources.",
        }
        filters: dict[str, Any] = {}
        if arguments.get("domains"):
            filters["search_domain_filter"] = arguments["domains"]
        if arguments.get("recency"):
            filters["search_recency_filter"] = arguments["recency"]
        if filters:
            payload["tools"][0]["filters"] = filters
        if arguments.get("max_tokens"):
            payload["max_output_tokens"] = arguments["max_tokens"]
        return _extract_text(_agent_call(payload))

    elif name == "perplexity_fetch_url":
        instruction = arguments.get("instruction", "Summarize the content at this URL")
        payload = {
            "model": arguments.get("model", "perplexity/sonar"),
            "input": f"{instruction}: {arguments['url']}",
            "tools": [{"type": "fetch_url"}],
            "instructions": "Use fetch_url to retrieve and analyze the page content.",
        }
        return _extract_text(_agent_call(payload))

    elif name == "perplexity_agent":
        tool_names = arguments.get("tools", ["web_search", "fetch_url"])
        built_tools = [{"type": t} for t in tool_names]
        payload = {"input": arguments["query"]}
        if arguments.get("preset"):
            payload["preset"] = arguments["preset"]
        else:
            payload["model"] = arguments.get("model", "perplexity/sonar")
        payload["tools"] = built_tools
        if arguments.get("instructions"):
            payload["instructions"] = arguments["instructions"]
        if arguments.get("max_tokens"):
            payload["max_output_tokens"] = arguments["max_tokens"]
        return _extract_text(_agent_call(payload))

    else:
        return f"Unknown tool: {name}"


def _send(msg: dict) -> None:
    """Write a JSON-RPC message to stdout."""
    out = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(out)}\r\n\r\n{out}")
    sys.stdout.flush()


def _read_message() -> dict | None:
    """Read a JSON-RPC message from stdin (Content-Length framed)."""
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if line == "":
            break
        if ":" in line:
            key, val = line.split(":", 1)
            headers[key.strip()] = val.strip()

    length = int(headers.get("Content-Length", "0"))
    if length == 0:
        return None
    body = sys.stdin.read(length)
    return json.loads(body)


def main() -> None:
    """Run the MCP stdio server loop."""
    while True:
        msg = _read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "perplexity-agent-mcp",
                        "version": "1.0.0",
                    },
                },
            })

        elif method == "notifications/initialized":
            pass  # no response needed

        elif method == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS},
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                result_text = handle_tool_call(tool_name, arguments)
                _send({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": result_text}],
                    },
                })
            except Exception as exc:
                _send({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {exc}"}],
                        "isError": True,
                    },
                })

        elif msg_id is not None:
            _send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })


if __name__ == "__main__":
    main()
