#!/usr/bin/env python3
"""ASO keyword rotation pipeline.

Pulls keyword ranking data (or simulates it from BID scores),
compares current rank vs. target, rotates underperforming keywords,
and updates fastlane metadata automatically.

Designed to run weekly via GitHub Actions.
"""

from __future__ import annotations

import argparse
import json
import datetime as dt
import random
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the keyword engine for BID scoring
import sys
sys.path.insert(0, str(Path(__file__).parent))
from growth_keyword_engine import (
    load_blueprint,
    build_backlog,
    normalize_keyword,
)

IOS_KEYWORDS_PATH = "native-ios/fastlane/metadata/en-US/keywords.txt"
ANDROID_TITLE_PATH = "native-android/fastlane/metadata/android/en-US/title.txt"
ANDROID_SHORT_DESC_PATH = "native-android/fastlane/metadata/android/en-US/short_description.txt"
HISTORY_PATH = "marketing/keywords/rotation_history.json"
STRATEGY_PATH = "marketing/keywords/strategy.json"
IOS_KEYWORD_LIMIT = 100  # App Store Connect char limit


def load_rotation_history(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / HISTORY_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"rotations": [], "current_keywords": {}}


def save_rotation_history(repo_root: Path, history: Dict[str, Any]) -> None:
    path = repo_root / HISTORY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def get_current_ios_keywords(repo_root: Path) -> List[str]:
    path = repo_root / IOS_KEYWORDS_PATH
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8").strip()
    return [k.strip() for k in text.split(",") if k.strip()]


def simulate_ranking(keyword: str, bid_score: int) -> Dict[str, Any]:
    """Simulate keyword ranking based on BID score.

    In production, replace with AppFollow/Sensor Tower/AppTweak API call.
    """
    random.seed(hash(keyword + str(dt.date.today().toordinal())))
    # Higher BID score = better simulated rank
    base_rank = max(1, 150 - bid_score * 2 + random.randint(-20, 20))
    return {
        "keyword": keyword,
        "rank": base_rank,
        "impressions_estimate": max(10, 500 - base_rank * 3 + random.randint(-50, 50)),
        "difficulty": random.randint(10, 60),
    }


def evaluate_keywords(
    current_keywords: List[str],
    backlog: List[Dict[str, Any]],
    target_rank: int = 50,
) -> Dict[str, List[Dict[str, Any]]]:
    """Evaluate current keywords and identify underperformers."""
    backlog_map = {row["keyword"]: row for row in backlog}
    performing = []
    underperforming = []

    for kw in current_keywords:
        normalized = normalize_keyword(kw)
        bid_row = backlog_map.get(normalized, {"bid_score": 30})
        ranking = simulate_ranking(normalized, bid_row.get("bid_score", 30))

        entry = {**ranking, "bid_score": bid_row.get("bid_score", 0)}
        if ranking["rank"] <= target_rank:
            performing.append(entry)
        else:
            underperforming.append(entry)

    return {"performing": performing, "underperforming": underperforming}


def select_replacements(
    underperforming: List[Dict[str, Any]],
    current_keywords: List[str],
    backlog: List[Dict[str, Any]],
    max_replacements: int = 3,
) -> List[str]:
    """Select replacement keywords from backlog with highest BID scores."""
    current_set = {normalize_keyword(k) for k in current_keywords}
    candidates = [
        row for row in backlog
        if not row.get("ai_trap")
        and row["keyword"] not in current_set
        and row["bid_score"] > 40
    ]
    candidates.sort(key=lambda r: -r["bid_score"])
    return [c["keyword"] for c in candidates[:max_replacements]]


def rotate_ios_keywords(
    repo_root: Path,
    performing: List[str],
    replacements: List[str],
) -> str:
    """Update iOS keywords.txt with performing keywords + replacements."""
    all_keywords = list(dict.fromkeys(performing + replacements))

    # Respect iOS 100-char limit
    final = []
    total_len = 0
    for kw in all_keywords:
        needed = len(kw) + (1 if final else 0)  # +1 for comma
        if total_len + needed <= IOS_KEYWORD_LIMIT:
            final.append(kw)
            total_len += needed

    keywords_str = ",".join(final)
    path = repo_root / IOS_KEYWORDS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(keywords_str + "\n", encoding="utf-8")
    return keywords_str


def generate_title_variants(base_title: str, top_keywords: List[str]) -> List[str]:
    """Generate A/B title variants incorporating top keywords."""
    variants = [base_title]
    for kw in top_keywords[:3]:
        title_kw = kw.title()
        variant = f"{base_title} - {title_kw}"
        if len(variant) <= 50:  # Play Store title limit
            variants.append(variant)
    return variants


def run_rotation(
    repo_root: Path,
    target_rank: int = 50,
    max_replacements: int = 3,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Main rotation pipeline."""
    strategy_path = repo_root / STRATEGY_PATH
    blueprint = load_blueprint(strategy_path)
    backlog = build_backlog(blueprint)
    current_ios = get_current_ios_keywords(repo_root)

    evaluation = evaluate_keywords(current_ios, backlog, target_rank)
    performing_kws = [e["keyword"] for e in evaluation["performing"]]
    underperforming_kws = [e["keyword"] for e in evaluation["underperforming"]]

    replacements = select_replacements(
        evaluation["underperforming"],
        current_ios,
        backlog,
        max_replacements,
    )

    result = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "current_keyword_count": len(current_ios),
        "performing": len(evaluation["performing"]),
        "underperforming": len(evaluation["underperforming"]),
        "replacements_selected": replacements,
        "removed_keywords": underperforming_kws[:max_replacements],
        "dry_run": dry_run,
    }

    if not dry_run:
        new_keywords_str = rotate_ios_keywords(repo_root, performing_kws, replacements)
        result["new_ios_keywords"] = new_keywords_str

        # Generate title variants report
        android_title_path = repo_root / ANDROID_TITLE_PATH
        if android_title_path.is_file():
            base_title = android_title_path.read_text(encoding="utf-8").strip()
            result["title_variants"] = generate_title_variants(base_title, replacements)

        # Update rotation history
        history = load_rotation_history(repo_root)
        history["rotations"].append(result)
        history["current_keywords"] = {
            "ios": new_keywords_str.split(","),
            "updated_at": result["timestamp"],
        }
        save_rotation_history(repo_root, history)

    return result


def build_report(result: Dict[str, Any]) -> str:
    """Build a markdown report of the rotation."""
    lines = [
        "# ASO Keyword Rotation Report",
        "",
        f"**Date:** {result['timestamp']}",
        f"**Mode:** {'Dry Run' if result.get('dry_run') else 'Live'}",
        "",
        "## Summary",
        f"- Current keywords: {result['current_keyword_count']}",
        f"- Performing (rank <= target): {result['performing']}",
        f"- Underperforming: {result['underperforming']}",
        "",
        "## Removed (underperforming)",
    ]
    for kw in result.get("removed_keywords", []):
        lines.append(f"- `{kw}`")

    lines.extend(["", "## Added (high BID score)"])
    for kw in result.get("replacements_selected", []):
        lines.append(f"- `{kw}`")

    if result.get("new_ios_keywords"):
        lines.extend([
            "",
            "## New iOS Keywords",
            f"```\n{result['new_ios_keywords']}\n```",
        ])

    if result.get("title_variants"):
        lines.extend(["", "## Title A/B Variants"])
        for i, v in enumerate(result["title_variants"]):
            lines.append(f"{i+1}. `{v}`")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="ASO keyword rotation pipeline")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--target-rank", type=int, default=50, help="Target rank threshold")
    parser.add_argument("--max-replacements", type=int, default=3, help="Max keywords to replace per cycle")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--report-out", default=None, help="Path to write markdown report")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    result = run_rotation(repo_root, args.target_rank, args.max_replacements, args.dry_run)
    report = build_report(result)

    print(report)
    print(json.dumps(result, indent=2))

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
