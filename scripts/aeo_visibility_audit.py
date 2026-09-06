"""Zero-cost AEO visibility scoring (SEJ HubSpot SPA method, no paid tool).

Computes mention rate, recommendation rate (top-3), and share of voice from a
prompt × engine answer log. HubSpot AEO is $50/mo after trial — outside the
$20/mo operating budget — so this repo implements the spreadsheet math as code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


OUR_BRAND_ALIASES = (
    "random tactical timer",
    "random timer",
    "iganapolsky",
    "random-timer",
)


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def brand_mentioned(answer_text: str, aliases: tuple[str, ...] = OUR_BRAND_ALIASES) -> bool:
    hay = _normalize(answer_text)
    return any(alias in hay for alias in aliases)


def brand_in_top_three(ordered_brands: list[str], aliases: tuple[str, ...] = OUR_BRAND_ALIASES) -> bool:
    for brand in ordered_brands[:3]:
        if brand_mentioned(brand, aliases):
            return True
    return False


def score_engine_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Score one engine's prompt rows.

    Each row: {prompt, answer_text, ordered_brands: [str], cited_domains: [str]}
    """
    if not rows:
        return {
            "prompts_tested": 0,
            "mention_rate": 0.0,
            "recommendation_rate": 0.0,
            "share_of_voice": 0.0,
            "mentions": 0,
            "top_three": 0,
            "all_brand_mentions": 0,
            "gap_prompts": [],
        }

    mentions = 0
    top_three = 0
    all_brand_mentions = 0
    gap_prompts: list[str] = []

    for row in rows:
        answer = str(row.get("answer_text") or "")
        ordered = [str(b) for b in (row.get("ordered_brands") or [])]
        prompt = str(row.get("prompt") or "")
        mentioned = brand_mentioned(answer) or any(brand_mentioned(b) for b in ordered)
        if mentioned:
            mentions += 1
        if brand_in_top_three(ordered) or (
            mentioned and not ordered and brand_mentioned(answer)
        ):
            # If the model names us without an ordered list, treat mention as
            # recommendation only when answer leads with our brand name.
            if ordered:
                if brand_in_top_three(ordered):
                    top_three += 1
            elif _normalize(answer).startswith(OUR_BRAND_ALIASES[0]):
                top_three += 1
        if not mentioned:
            gap_prompts.append(prompt)
        all_brand_mentions += max(len(ordered), 1 if mentioned else 0)

    n = len(rows)
    return {
        "prompts_tested": n,
        "mention_rate": round(mentions / n, 4),
        "recommendation_rate": round(top_three / n, 4),
        "share_of_voice": round(mentions / all_brand_mentions, 4) if all_brand_mentions else 0.0,
        "mentions": mentions,
        "top_three": top_three,
        "all_brand_mentions": all_brand_mentions,
        "gap_prompts": gap_prompts,
    }


def score_audit(payload: dict[str, Any]) -> dict[str, Any]:
    engines = payload.get("engines") or {}
    per_engine = {name: score_engine_rows(rows) for name, rows in engines.items()}
    rates_m = [e["mention_rate"] for e in per_engine.values() if e["prompts_tested"]]
    rates_r = [e["recommendation_rate"] for e in per_engine.values() if e["prompts_tested"]]
    return {
        "brand": payload.get("brand") or "Random Tactical Timer",
        "source_article": payload.get("source_article"),
        "budget_note": payload.get("budget_note"),
        "per_engine": per_engine,
        "composite": {
            "mention_rate": round(sum(rates_m) / len(rates_m), 4) if rates_m else 0.0,
            "recommendation_rate": round(sum(rates_r) / len(rates_r), 4) if rates_r else 0.0,
            "engines_scored": len(rates_m),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to AEO answer log JSON")
    parser.add_argument("--output", help="Optional path to write scored JSON")
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    scored = score_audit(payload)
    text = json.dumps(scored, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
