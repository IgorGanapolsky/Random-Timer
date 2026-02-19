#!/usr/bin/env python3
"""Keyword research engine for daily growth content.

Implements a repeatable seed/modifier expansion pipeline with BID-style scoring,
AI-trap heuristics, and tool-keyword detection.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import zlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DEFAULT_BLUEPRINT: Dict[str, Any] = {
    "niche": "mobile timer app for tactical and reaction training",
    "monetization": "app installs, retention, and app store reviews",
    "audience": "athletes, tactical trainers, coaches, and users who need unpredictable interval drills",
    "seed_keywords": [
        "reaction training",
        "interval timer",
        "tactical timer",
        "random timer",
        "focus drills",
        "combat conditioning",
        "boxing drills",
        "home workout timer",
        "sparring prep",
        "mental readiness",
    ],
    "modifiers": [
        "best",
        "vs",
        "under 20",
        "review",
        "calculator",
        "checker",
        "generator",
        "template",
        "app",
        "for beginners",
    ],
}

TOOL_MODIFIERS: Tuple[str, ...] = ("calculator", "checker", "generator", "converter", "template")
COMMERCIAL_HINTS: Tuple[str, ...] = ("best", "vs", "review", "under", "app", "buy", "price", "alternative")
INFORMATIONAL_HINTS: Tuple[str, ...] = ("what is", "how to", "tips", "guide", "benefits")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_keyword(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip().lower())
    return cleaned


def dedupe_preserve(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        k = normalize_keyword(item)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def load_blueprint(path: Path) -> Dict[str, Any]:
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            "niche": str(payload.get("niche") or DEFAULT_BLUEPRINT["niche"]),
            "monetization": str(payload.get("monetization") or DEFAULT_BLUEPRINT["monetization"]),
            "audience": str(payload.get("audience") or DEFAULT_BLUEPRINT["audience"]),
            "seed_keywords": dedupe_preserve(payload.get("seed_keywords") or DEFAULT_BLUEPRINT["seed_keywords"]),
            "modifiers": dedupe_preserve(payload.get("modifiers") or DEFAULT_BLUEPRINT["modifiers"]),
        }

    ensure_dir(path.parent)
    path.write_text(json.dumps(DEFAULT_BLUEPRINT, indent=2) + "\n", encoding="utf-8")
    return {
        "niche": DEFAULT_BLUEPRINT["niche"],
        "monetization": DEFAULT_BLUEPRINT["monetization"],
        "audience": DEFAULT_BLUEPRINT["audience"],
        "seed_keywords": dedupe_preserve(DEFAULT_BLUEPRINT["seed_keywords"]),
        "modifiers": dedupe_preserve(DEFAULT_BLUEPRINT["modifiers"]),
    }


def expand_keywords(seeds: Iterable[str], modifiers: Iterable[str]) -> List[str]:
    expanded: List[str] = []
    for seed in dedupe_preserve(seeds):
        expanded.append(seed)
        for mod in dedupe_preserve(modifiers):
            # Most modifiers perform better as a prefix for commercial/tool intents.
            if mod in {"for beginners"}:
                expanded.append(f"{seed} {mod}")
            else:
                expanded.append(f"{mod} {seed}")
    return dedupe_preserve(expanded)


def infer_intent(keyword: str) -> str:
    k = normalize_keyword(keyword)
    if any(m in k for m in TOOL_MODIFIERS):
        return "tool"
    if any(h in k for h in COMMERCIAL_HINTS):
        return "commercial"
    if any(h in k for h in INFORMATIONAL_HINTS):
        return "informational"
    return "mixed"


def business_potential(keyword: str) -> int:
    k = normalize_keyword(keyword)
    score = 1
    if any(h in k for h in COMMERCIAL_HINTS):
        score += 1
    if "app" in k or any(m in k for m in TOOL_MODIFIERS):
        score += 1
    return max(0, min(3, score))


def deterministic_kd(keyword: str) -> int:
    digest = zlib.crc32(normalize_keyword(keyword).encode("utf-8"))
    return int(digest) % 51


def ai_trap(keyword: str, intent: str) -> bool:
    k = normalize_keyword(keyword)
    if intent in {"commercial", "tool"}:
        return False
    return any(h in k for h in INFORMATIONAL_HINTS)


def bid_score(intent: str, business: int, kd: int, trap: bool, is_tool: bool) -> int:
    score = business * 30
    if intent == "tool":
        score += 25
    elif intent == "commercial":
        score += 18
    elif intent == "mixed":
        score += 10
    else:
        score += 4

    if kd <= 20:
        score += 20
    elif kd <= 35:
        score += 12
    else:
        score += 4

    if trap:
        score -= 18
    if is_tool:
        score += 10
    return max(0, score)


def keyword_to_post_title(keyword: str) -> str:
    phrase = normalize_keyword(keyword)
    return f"{phrase.title()}: what we learned building Random Tactical Timer"


def build_backlog(blueprint: Dict[str, Any], max_keywords: int = 240) -> List[Dict[str, Any]]:
    expanded = expand_keywords(blueprint["seed_keywords"], blueprint["modifiers"])
    rows: List[Dict[str, Any]] = []

    for kw in expanded[:max_keywords]:
        intent = infer_intent(kw)
        business = business_potential(kw)
        kd = deterministic_kd(kw)
        trap = ai_trap(kw, intent)
        is_tool = any(m in kw for m in TOOL_MODIFIERS)
        score = bid_score(intent, business, kd, trap, is_tool)

        rows.append(
            {
                "keyword": kw,
                "intent": intent,
                "business_potential": business,
                "difficulty": kd,
                "ai_trap": trap,
                "tool_keyword": is_tool,
                "bid_score": score,
            }
        )

    rows.sort(key=lambda item: (item["ai_trap"], -item["bid_score"], item["difficulty"], item["keyword"]))
    return rows


def write_backlog(backlog: List[Dict[str, Any]], output_root: Path) -> Dict[str, str]:
    ensure_dir(output_root)
    json_path = output_root / "keyword_backlog.json"
    csv_path = output_root / "keyword_backlog.csv"
    md_path = output_root / "keyword_backlog.md"

    json_path.write_text(json.dumps(backlog, indent=2) + "\n", encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["keyword", "intent", "business_potential", "difficulty", "ai_trap", "tool_keyword", "bid_score"],
        )
        writer.writeheader()
        writer.writerows(backlog)

    lines = [
        "# Keyword Backlog",
        "",
        f"Generated: {dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()}",
        "",
        "| Keyword | Intent | BP | KD | AI Trap | Tool | BID |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    for row in backlog[:50]:
        lines.append(
            "| {keyword} | {intent} | {business_potential} | {difficulty} | {ai_trap} | {tool_keyword} | {bid_score} |".format(
                **row
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}


def select_daily_keyword(backlog: List[Dict[str, Any]], day: Optional[dt.date] = None) -> Optional[Dict[str, Any]]:
    valid = [row for row in backlog if not row.get("ai_trap")]
    if not valid:
        valid = backlog
    if not valid:
        return None
    cursor_day = day or dt.datetime.now(dt.timezone.utc).date()
    idx = cursor_day.toordinal() % len(valid)
    return valid[idx]


def run_build(output_root: Path, strategy_path: Path) -> Dict[str, Any]:
    blueprint = load_blueprint(strategy_path)
    backlog = build_backlog(blueprint)
    files = write_backlog(backlog, output_root)
    selected = select_daily_keyword(backlog)
    payload = {
        "status": "ok",
        "strategy": str(strategy_path),
        "keyword_count": len(backlog),
        "selected_keyword": selected,
        "outputs": files,
    }
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Growth keyword engine")
    parser.add_argument("--output-root", default="marketing/keywords")
    parser.add_argument("--strategy", default="marketing/keywords/strategy.json")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_build(Path(args.output_root).resolve(), Path(args.strategy).resolve())
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
