#!/usr/bin/env python3
"""AI crawler classification and analytics summaries for growth content."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BOT_PATTERNS = [
    (re.compile(r"gptbot|openai", re.I), "ai_training", "openai"),
    (re.compile(r"claudebot|anthropic", re.I), "ai_training", "anthropic"),
    (re.compile(r"google-extended", re.I), "ai_training", "google"),
    (re.compile(r"perplexity", re.I), "ai_retrieval", "perplexity"),
    (re.compile(r"bytespider|bytedance", re.I), "ai_retrieval", "bytedance"),
    (re.compile(r"facebookexternalhit|meta-externalagent", re.I), "search_crawler", "meta"),
    (re.compile(r"googlebot|bingbot|duckduckbot", re.I), "search_crawler", "search"),
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def classify_user_agent(ua: str) -> Dict[str, str]:
    token = ua.strip()
    for pattern, bot_type, model in BOT_PATTERNS:
        if pattern.search(token):
            return {"bot_type": bot_type, "model": model}
    return {"bot_type": "unknown", "model": "unknown"}


def _read_ndjson(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def analyze_logs(log_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    per_model: Dict[str, int] = {}
    per_bot_type: Dict[str, int] = {}
    per_path: Dict[str, int] = {}

    total = 0
    for row in log_rows:
        ua = str(row.get("user_agent") or row.get("ua") or "")
        path = str(row.get("path") or row.get("url") or "/")
        info = classify_user_agent(ua)
        bot_type = info["bot_type"]
        model = info["model"]
        if bot_type == "unknown":
            continue

        total += 1
        per_model[model] = per_model.get(model, 0) + 1
        per_bot_type[bot_type] = per_bot_type.get(bot_type, 0) + 1
        per_path[path] = per_path.get(path, 0) + 1

    top_paths = sorted(per_path.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    return {
        "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "total_ai_bot_hits": total,
        "bot_types": per_bot_type,
        "models": per_model,
        "top_paths": [{"path": p, "hits": h} for p, h in top_paths],
    }


def write_reports(summary: Dict[str, Any], output_root: Path) -> Dict[str, str]:
    ensure_dir(output_root)
    json_path = output_root / "bot_traffic_summary.json"
    md_path = output_root / "bot_traffic_summary.md"

    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# AI Bot Traffic Summary",
        "",
        f"Timestamp: {summary.get('timestamp')}",
        f"Total classified AI bot hits: {summary.get('total_ai_bot_hits', 0)}",
        "",
        "## Bot Types",
    ]
    for key, val in sorted((summary.get("bot_types") or {}).items()):
        lines.append(f"- {key}: {val}")

    lines.append("")
    lines.append("## Models")
    for key, val in sorted((summary.get("models") or {}).items()):
        lines.append(f"- {key}: {val}")

    lines.append("")
    lines.append("## Top Paths")
    for item in summary.get("top_paths") or []:
        lines.append(f"- {item['path']}: {item['hits']}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def run(input_path: Path, output_root: Path) -> Dict[str, Any]:
    rows = _read_ndjson(input_path)
    summary = analyze_logs(rows)
    files = write_reports(summary, output_root)
    return {
        "status": "ok" if rows else "no_input",
        "input": str(input_path),
        "input_rows": len(rows),
        "summary": summary,
        "outputs": files,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI bot traffic analytics")
    parser.add_argument("--input", default="marketing/data/access-log.ndjson")
    parser.add_argument("--output-root", default="marketing/data")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run(Path(args.input).resolve(), Path(args.output_root).resolve())
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
