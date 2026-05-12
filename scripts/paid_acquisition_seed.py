#!/usr/bin/env python3
"""Paid acquisition seed automation.

Generates campaign configurations for Apple Search Ads and Google UAC
based on keyword research and ASO data. Manages budget allocation,
keyword bids, and campaign structure.

Designed to run weekly via GitHub Actions for campaign optimization.
"""

from __future__ import annotations

import argparse
import json
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent))
from growth_keyword_engine import load_blueprint, build_backlog

CAMPAIGNS_PATH = "marketing/data/paid_campaigns.json"
STRATEGY_PATH = "marketing/keywords/strategy.json"
MONTHLY_EXTERNAL_SPEND_CAP_USD = 20.0
MONTHLY_BUDGET_DAYS = 31

# Default budget configuration
DEFAULT_BUDGET = {
    "daily_budget_usd": round(MONTHLY_EXTERNAL_SPEND_CAP_USD / MONTHLY_BUDGET_DAYS, 2),
    "launch_week_multiplier": 1.5,
    "max_cpt_usd": 1.50,  # max cost per tap (Apple) / click (Google)
    "target_cpa_usd": 3.00,  # target cost per acquisition
}


def _monthly_cap_daily_budget() -> float:
    return round(MONTHLY_EXTERNAL_SPEND_CAP_USD / MONTHLY_BUDGET_DAYS, 2)


def _safe_daily_budget_cap(previous_daily_budget: float) -> float:
    monthly_cap = _monthly_cap_daily_budget()
    if previous_daily_budget <= 0:
        return monthly_cap
    return round(min(previous_daily_budget * 1.25, previous_daily_budget + 5.0, monthly_cap), 2)


def _apply_budget_override_guardrails(
    current_budget: Dict[str, float],
    budget_override: Optional[Dict[str, float]],
) -> tuple[Dict[str, float], float, float, bool]:
    requested_daily_budget = float(current_budget.get("daily_budget_usd", DEFAULT_BUDGET["daily_budget_usd"]))
    applied_daily_budget = requested_daily_budget
    budget_capped = False
    merged_budget = dict(current_budget)

    if budget_override is not None:
        merged_budget.update(budget_override)
    requested_daily_budget = float(merged_budget.get("daily_budget_usd", requested_daily_budget))
    previous_daily_budget = float(current_budget.get("daily_budget_usd", DEFAULT_BUDGET["daily_budget_usd"]))
    max_allowed_daily_budget = _safe_daily_budget_cap(previous_daily_budget)
    applied_daily_budget = min(requested_daily_budget, max_allowed_daily_budget)
    budget_capped = applied_daily_budget < requested_daily_budget
    merged_budget["daily_budget_usd"] = applied_daily_budget
    return merged_budget, requested_daily_budget, applied_daily_budget, budget_capped


def _merge_managed_campaign(
    existing_campaign: Optional[Dict[str, Any]],
    generated_campaign: Dict[str, Any],
) -> Dict[str, Any]:
    merged = dict(generated_campaign)
    if not isinstance(existing_campaign, dict):
        return merged

    # Preserve historical launch metadata for managed campaigns.
    for key in ("created", "status", "campaign_id", "launched_at"):
        if key in existing_campaign:
            merged[key] = existing_campaign[key]
    return merged


def _guard_unmanaged_campaign(
    campaign: Dict[str, Any],
    total_daily_budget: float,
) -> Dict[str, Any]:
    """Prevent stale unmanaged configs from bypassing the monthly budget cap."""
    guarded = dict(campaign)
    daily_budget = float(guarded.get("daily_budget_usd") or 0.0)
    if daily_budget <= 0:
        return guarded

    guarded["budget_guardrail_blocked"] = True
    guarded["budget_guardrail_reason"] = (
        "unmanaged_paid_channel_requires_explicit_budget_allocation_under_monthly_cap"
    )
    guarded["daily_budget_requested_usd"] = daily_budget
    guarded["daily_budget_usd"] = 0.0
    if guarded.get("status") in {"draft", "ready_to_launch"}:
        guarded["status"] = "blocked_budget_guardrail"
    guarded["monthly_budget_cap_usd"] = MONTHLY_EXTERNAL_SPEND_CAP_USD
    guarded["total_managed_daily_budget_usd"] = total_daily_budget
    return guarded


def load_campaigns(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / CAMPAIGNS_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"campaigns": [], "budget_config": DEFAULT_BUDGET, "history": []}


def save_campaigns(repo_root: Path, data: Dict[str, Any]) -> None:
    path = repo_root / CAMPAIGNS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_apple_search_ads_campaign(
    backlog: List[Dict[str, Any]],
    budget: Dict[str, float],
) -> Dict[str, Any]:
    """Build Apple Search Ads campaign config."""
    # Select top keywords by BID score for exact match
    exact_match = [
        row for row in backlog
        if not row.get("ai_trap") and row["bid_score"] >= 60
    ][:15]

    # Broader keywords for search match
    search_match = [
        row for row in backlog
        if not row.get("ai_trap") and 40 <= row["bid_score"] < 60
    ][:20]

    # Discovery campaign keywords (competitors + category)
    discovery = [
        row for row in backlog
        if row.get("intent") in ("commercial", "tool") and row["bid_score"] >= 50
    ][:10]

    campaign = {
        "platform": "apple_search_ads",
        "created": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "draft",
        "daily_budget_usd": budget["daily_budget_usd"],
        "ad_groups": [
            {
                "name": "Exact Match - High Intent",
                "match_type": "exact",
                "max_cpt_usd": budget["max_cpt_usd"],
                "keywords": [
                    {"text": row["keyword"], "bid_score": row["bid_score"]}
                    for row in exact_match
                ],
            },
            {
                "name": "Search Match - Discovery",
                "match_type": "search",
                "max_cpt_usd": budget["max_cpt_usd"] * 0.7,
                "keywords": [
                    {"text": row["keyword"], "bid_score": row["bid_score"]}
                    for row in search_match
                ],
            },
            {
                "name": "Competitor - Brand",
                "match_type": "exact",
                "max_cpt_usd": budget["max_cpt_usd"] * 1.2,
                "keywords": [
                    {"text": row["keyword"], "bid_score": row["bid_score"]}
                    for row in discovery
                ],
            },
        ],
        "negative_keywords": [
            "free timer online",
            "timer website",
            "countdown website",
            "clock widget",
        ],
        "target_cpa_usd": budget["target_cpa_usd"],
    }
    return campaign


def build_google_uac_campaign(
    backlog: List[Dict[str, Any]],
    budget: Dict[str, float],
) -> Dict[str, Any]:
    """Build Google Universal App Campaign config."""
    # UAC uses machine learning, so we provide creative assets + targeting hints
    top_keywords = [
        row["keyword"] for row in backlog
        if not row.get("ai_trap") and row["bid_score"] >= 50
    ][:25]

    campaign = {
        "platform": "google_uac",
        "created": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "draft",
        "daily_budget_usd": budget["daily_budget_usd"],
        "campaign_type": "installs",
        "target_cpa_usd": budget["target_cpa_usd"],
        "ad_assets": {
            "headlines": [
                "Random Timer for HIIT & Drills",
                "Surprise Interval Timer App",
                "Tactical Timer - Train Smarter",
                "Random Countdown Timer",
            ],
            "descriptions": [
                "Set a range, press start. You never know when it fires. Perfect for HIIT.",
                "Unpredictable timer for workouts, drills & party games. No ads, no tracking.",
                "Keep sharp with random intervals. Used by athletes, coaches & gamers.",
            ],
        },
        "targeting": {
            "locations": ["US", "GB", "CA", "AU", "DE"],
            "languages": ["en", "de"],
            "keyword_themes": top_keywords[:10],
        },
        "optimization_goal": "installs",
    }
    return campaign


def compute_budget_allocation(
    campaigns: List[Dict[str, Any]],
    total_daily_budget: float,
) -> Dict[str, float]:
    """Allocate budget across campaigns."""
    # 60% Apple (higher intent), 40% Google (broader reach)
    return {
        "apple_search_ads": round(total_daily_budget * 0.6, 2),
        "google_uac": round(total_daily_budget * 0.4, 2),
    }


def run_acquisition(repo_root: Path, budget_override: Optional[Dict] = None) -> Dict[str, Any]:
    """Main paid acquisition pipeline."""
    campaigns_data = load_campaigns(repo_root)
    current_budget = campaigns_data.get("budget_config", DEFAULT_BUDGET)
    budget, requested_daily_budget, applied_daily_budget, budget_capped = _apply_budget_override_guardrails(
        current_budget=current_budget,
        budget_override=budget_override,
    )

    strategy_path = repo_root / STRATEGY_PATH
    blueprint = load_blueprint(strategy_path)
    backlog = build_backlog(blueprint)

    # Build campaign configs
    apple_campaign = build_apple_search_ads_campaign(backlog, budget)
    google_campaign = build_google_uac_campaign(backlog, budget)

    allocation = compute_budget_allocation(
        [apple_campaign, google_campaign],
        budget["daily_budget_usd"],
    )
    apple_campaign["daily_budget_usd"] = allocation["apple_search_ads"]
    google_campaign["daily_budget_usd"] = allocation["google_uac"]

    # Update managed campaigns while preserving unrelated platforms.
    existing_campaigns = campaigns_data.get("campaigns", [])
    if not isinstance(existing_campaigns, list):
        existing_campaigns = []
    existing_by_platform = {
        str(item.get("platform")): item for item in existing_campaigns if isinstance(item, dict) and item.get("platform")
    }

    managed_updates = {
        "apple_search_ads": _merge_managed_campaign(existing_by_platform.get("apple_search_ads"), apple_campaign),
        "google_uac": _merge_managed_campaign(existing_by_platform.get("google_uac"), google_campaign),
    }

    updated_campaigns: List[Dict[str, Any]] = []
    managed_inserted: set[str] = set()
    for campaign in existing_campaigns:
        if not isinstance(campaign, dict):
            continue
        platform = str(campaign.get("platform", ""))
        if platform in managed_updates:
            updated_campaigns.append(managed_updates[platform])
            managed_inserted.add(platform)
        else:
            updated_campaigns.append(_guard_unmanaged_campaign(campaign, budget["daily_budget_usd"]))
    for platform, campaign in managed_updates.items():
        if platform not in managed_inserted:
            updated_campaigns.append(campaign)

    campaigns_data["campaigns"] = updated_campaigns
    campaigns_data["budget_config"] = budget
    campaigns_data["budget_allocation"] = allocation
    campaigns_data["history"].append({
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "action": "campaign_refresh",
        "apple_keywords": len(apple_campaign["ad_groups"][0]["keywords"]),
        "google_themes": len(google_campaign["targeting"]["keyword_themes"]),
        "daily_budget_requested_usd": requested_daily_budget,
        "daily_budget_applied_usd": applied_daily_budget,
        "monthly_budget_cap_usd": MONTHLY_EXTERNAL_SPEND_CAP_USD,
        "budget_capped": budget_capped,
    })
    campaigns_data["history"] = campaigns_data["history"][-50:]

    save_campaigns(repo_root, campaigns_data)

    return {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "budget": budget,
        "allocation": allocation,
        "apple_ad_groups": len(apple_campaign["ad_groups"]),
        "apple_total_keywords": sum(len(ag["keywords"]) for ag in apple_campaign["ad_groups"]),
        "google_themes": len(google_campaign["targeting"]["keyword_themes"]),
        "google_headlines": len(google_campaign["ad_assets"]["headlines"]),
        "monthly_budget_cap_usd": MONTHLY_EXTERNAL_SPEND_CAP_USD,
        "budget_capped": budget_capped,
        "unmanaged_budget_guardrails": [
            {
                "platform": campaign.get("platform"),
                "daily_budget_requested_usd": campaign.get("daily_budget_requested_usd"),
                "status": campaign.get("status"),
            }
            for campaign in updated_campaigns
            if campaign.get("budget_guardrail_blocked")
        ],
    }


def build_report(result: Dict[str, Any]) -> str:
    lines = [
        "# Paid Acquisition Seed Report",
        "",
        f"**Date:** {result['timestamp']}",
        "",
        "## Budget",
        f"- Daily budget: **${result['budget']['daily_budget_usd']}**",
        f"- Monthly external spend cap: **${result['monthly_budget_cap_usd']}**",
        f"- Budget capped by guardrail: **{result['budget_capped']}**",
        f"- Target CPA: **${result['budget']['target_cpa_usd']}**",
        f"- Max CPT: **${result['budget']['max_cpt_usd']}**",
        "",
        "## Budget Allocation",
        f"- Apple Search Ads: **${result['allocation']['apple_search_ads']}/day**",
        f"- Google UAC: **${result['allocation']['google_uac']}/day**",
        "",
        "## Apple Search Ads",
        f"- Ad groups: {result['apple_ad_groups']}",
        f"- Total keywords: {result['apple_total_keywords']}",
        "",
        "## Google UAC",
        f"- Keyword themes: {result['google_themes']}",
        f"- Headlines: {result['google_headlines']}",
        "",
        "## Unmanaged Paid Channel Guardrails",
        *(
            [
                "- none",
            ]
            if not result.get("unmanaged_budget_guardrails")
            else [
                (
                    f"- {item['platform']}: blocked at $0/day "
                    f"(requested ${item['daily_budget_requested_usd']}/day, status {item['status']})"
                )
                for item in result["unmanaged_budget_guardrails"]
            ]
        ),
        "",
        "## Next Steps",
        "1. Review campaign configs in `marketing/data/paid_campaigns.json`",
        "2. Import Apple Search Ads campaign via ASA API or web console",
        "3. Set up Google UAC campaign in Google Ads console",
        "4. Monitor CPA and adjust bids after 7 days",
        "5. Pause underperforming keywords after 14 days",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Paid acquisition seed pipeline")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--daily-budget", type=float, default=None)
    parser.add_argument("--report-out", default=None)
    args = parser.parse_args()

    budget = None
    if args.daily_budget:
        budget = {**DEFAULT_BUDGET, "daily_budget_usd": args.daily_budget}

    result = run_acquisition(Path(args.repo_root).resolve(), budget)
    report = build_report(result)
    print(report)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
