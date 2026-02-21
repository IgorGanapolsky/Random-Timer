#!/usr/bin/env python3
"""Inject live data from marketing/data/ JSON files into wiki dashboard template.

Reads the static wiki templates from wiki/, injects live metrics from
marketing/data/ JSON files into the Daily Metrics Dashboard. Git
operations (clone wiki repo, commit, push) are handled by the GitHub
Actions workflow YAML, not this script.

Designed to run daily via GitHub Actions.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if missing or invalid."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_jsonl(path: Path) -> list:
    """Load a JSONL file, returning empty list if missing."""
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _fmt(val: Any, suffix: str = "") -> str:
    """Format a value for display, returning '—' for None/0/empty."""
    if val is None or val == 0 or val == "":
        return "—"
    if isinstance(val, float):
        return f"{val:.1%}"
    return f"{val}{suffix}"


def _fmt_num(val: Any) -> str:
    if val is None or val == 0:
        return "—"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


def inject_dashboard_data(dashboard: str, data_dir: Path) -> str:
    """Replace placeholder sections in the dashboard with live data."""
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    dashboard = dashboard.replace("<!-- TIMESTAMP -->", now)

    # --- Downloads & Active Users ---
    dl = load_json(data_dir / "store_downloads.json")
    if dl:
        ios = dl.get("ios", {})
        android = dl.get("android", {})
        combined = dl.get("combined", {})
        users = dl.get("active_users", {})
        ios_30 = _fmt_num(ios.get("downloads_30d"))
        and_30 = _fmt_num(android.get("downloads_30d"))
        comb_30 = _fmt_num(combined.get("downloads_30d"))
        and_active = _fmt_num(android.get("active_installs"))
        downloads_block = (
            "| Metric | iOS | Android | Combined |\n"
            "|--------|:---:|:-------:|:--------:|\n"
            f"| Downloads (30d) | {ios_30} | {and_30} | {comb_30} |\n"
            f"| Active Installs | — | {and_active} | — |\n\n"
            "| Active Users | Count |\n"
            "|-------------|:-----:|\n"
            f"| DAU | {_fmt_num(users.get('dau'))} |\n"
            f"| WAU | {_fmt_num(users.get('wau'))} |\n"
            f"| MAU | {_fmt_num(users.get('mau'))} |"
        )
        dashboard = re.sub(
            r"<!-- DOWNLOADS_START -->.*?<!-- DOWNLOADS_END -->",
            f"<!-- DOWNLOADS_START -->\n{downloads_block}\n<!-- DOWNLOADS_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- Review Velocity ---
    rv = load_json(data_dir / "review_velocity.json")
    if rv:
        snapshots = rv.get("snapshots", [])
        latest = snapshots[-1] if snapshots else {}
        velocity = rv.get("latest_velocity", {})
        config = rv.get("review_prompt_config", {})

        reviews_block = (
            f"| Platform | Total Reviews | Avg Rating | 7-day Velocity |\n"
            f"|----------|:------------:|:----------:|:--------------:|\n"
            f"| iOS | {_fmt_num(latest.get('ios_total'))} | {_fmt_num(latest.get('ios_rating'))} "
            f"| {_fmt_num(velocity.get('ios_velocity'))} reviews/day |\n"
            f"| Android | {_fmt_num(latest.get('android_total'))} | {_fmt_num(latest.get('android_rating'))} "
            f"| {_fmt_num(velocity.get('android_velocity'))} reviews/day |\n\n"
            f"**Prompt Config:** Show after {config.get('completions_before_prompt', '—')} completions, "
            f"{config.get('min_days_between_prompts', '—')} days between prompts"
        )
        dashboard = re.sub(
            r"<!-- REVIEWS_START -->.*?<!-- REVIEWS_END -->",
            f"<!-- REVIEWS_START -->\n{reviews_block}\n<!-- REVIEWS_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- CRO Experiments ---
    cro = load_json(data_dir / "cro_experiments.json")
    if cro:
        # Support both {"experiments": [...]} and bare list formats
        experiments = cro.get("experiments", cro) if isinstance(cro, dict) else cro
        if not isinstance(experiments, list):
            experiments = []
        rows = []
        for exp in experiments:
            rows.append(
                f"| {exp.get('type', '—')} | {exp.get('platform', '—')} "
                f"| {exp.get('status', '—')} | {exp.get('duration_days', '—')} days |"
            )
        cro_block = (
            "| Experiment | Platform | Status | Duration |\n"
            "|-----------|----------|--------|----------|\n"
            + "\n".join(rows)
        )
        dashboard = re.sub(
            r"<!-- CRO_START -->.*?<!-- CRO_END -->",
            f"<!-- CRO_START -->\n{cro_block}\n<!-- CRO_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- Paid Campaigns ---
    pc = load_json(data_dir / "paid_campaigns.json")
    if pc:
        campaigns = pc.get("campaigns", [])
        alloc = pc.get("budget_allocation", {})
        campaign_rows = []
        total_kw = 0
        for c in campaigns:
            platform = c.get("platform", "—")
            alloc_val = alloc.get(platform, 0)
            budget = alloc_val.get("daily_budget_usd", 0) if isinstance(alloc_val, dict) else (alloc_val if isinstance(alloc_val, (int, float)) else 0)
            status = c.get("status", "draft")
            kw_count = sum(len(ag.get("keywords", [])) for ag in c.get("ad_groups", []))
            if not kw_count:
                kw_count = len(c.get("targeting", {}).get("keyword_themes", []))
            total_kw += kw_count
            campaign_rows.append(f"| {platform} | ${budget:.2f} | {status} | {kw_count} |")
        total_budget = sum(
            v.get("daily_budget_usd", 0) if isinstance(v, dict) else (v if isinstance(v, (int, float)) else 0)
            for v in alloc.values()
        )
        campaign_rows.append(f"| **Total** | **${total_budget:.2f}** | — | {total_kw} |")
        campaigns_block = (
            "| Platform | Daily Budget | Status | Keywords |\n"
            "|----------|:-----------:|--------|:--------:|\n"
            + "\n".join(campaign_rows)
        )
        dashboard = re.sub(
            r"<!-- CAMPAIGNS_START -->.*?<!-- CAMPAIGNS_END -->",
            f"<!-- CAMPAIGNS_START -->\n{campaigns_block}\n<!-- CAMPAIGNS_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- Content Pipeline ---
    posts = load_jsonl(data_dir / "posts.jsonl")
    if posts:
        latest_post = posts[-1]
        content_block = (
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Total Posts Published | {len(posts)} |\n"
            f"| Latest Post | {latest_post.get('title', '—')} |\n"
            f"| Published At | {latest_post.get('timestamp', '—')} |"
        )
        dashboard = re.sub(
            r"<!-- CONTENT_START -->.*?<!-- CONTENT_END -->",
            f"<!-- CONTENT_START -->\n{content_block}\n<!-- CONTENT_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- Referral Campaigns ---
    ref = load_json(data_dir / "referral_campaigns.json")
    if ref:
        reddit_count = len(ref.get("reddit_posts", []))
        ph_count = 1 if ref.get("product_hunt") else 0
        blog_count = len(ref.get("blog_outreach", []))
        reddit_status = ref["reddit_posts"][0].get("status", "draft") if ref.get("reddit_posts") else "—"
        ph_status = ref.get("product_hunt", {}).get("status", "—")
        blog_status = ref["blog_outreach"][0].get("status", "draft") if ref.get("blog_outreach") else "—"
        referral_block = (
            "| Channel | Items | Status |\n"
            "|---------|:-----:|--------|\n"
            f"| Reddit Posts | {reddit_count} | {reddit_status} |\n"
            f"| Product Hunt | {ph_count} | {ph_status} |\n"
            f"| Blog Outreach | {blog_count} | {blog_status} |"
        )
        dashboard = re.sub(
            r"<!-- REFERRAL_START -->.*?<!-- REFERRAL_END -->",
            f"<!-- REFERRAL_START -->\n{referral_block}\n<!-- REFERRAL_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- Attribution (from markdown report if available) ---
    report_path = data_dir / "attribution-report.md"
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        dashboard = re.sub(
            r"<!-- ATTRIBUTION_START -->.*?<!-- ATTRIBUTION_END -->",
            f"<!-- ATTRIBUTION_START -->\n{report}\n<!-- ATTRIBUTION_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- Funnel (from content_feedback.json) ---
    cf = load_json(data_dir / "content_feedback.json")
    if cf:
        funnel = cf.get("onboarding_funnel", {})
        fo = funnel.get("first_open", 0)
        fc = funnel.get("first_timer_configured", 0)
        ft = funnel.get("first_timer_completed", 0)
        oc_rate = funnel.get("open_to_configured_rate", 0)
        ot_rate = funnel.get("open_to_completed_rate", 0)
        funnel_block = (
            "| Step | Users | Conversion |\n"
            "|------|:-----:|:----------:|\n"
            f"| First Open | {_fmt_num(fo)} | — |\n"
            f"| First Timer Configured | {_fmt_num(fc)} | {_fmt(oc_rate)} of opens |\n"
            f"| First Timer Completed | {_fmt_num(ft)} | {_fmt(ot_rate)} of opens |"
        )
        dashboard = re.sub(
            r"<!-- FUNNEL_START -->.*?<!-- FUNNEL_END -->",
            f"<!-- FUNNEL_START -->\n{funnel_block}\n<!-- FUNNEL_END -->",
            dashboard,
            flags=re.DOTALL,
        )

    # --- ASO Keywords ---
    ios_kw_path = Path("native-ios/fastlane/metadata/en-US/keywords.txt")
    if ios_kw_path.exists():
        keywords = ios_kw_path.read_text(encoding="utf-8").strip()
    else:
        keywords = "—"

    rotation_hist = load_json(Path("marketing/keywords/rotation_history.json"))
    last_rotation = "—"
    performing = "—"
    replaced = "—"
    if rotation_hist and isinstance(rotation_hist, list) and rotation_hist:
        last = rotation_hist[-1]
        last_rotation = last.get("timestamp", "—")
        performing = str(last.get("performing_count", "—"))
        replaced = str(last.get("replaced_count", "—"))

    aso_block = (
        f"**iOS (current):** `{keywords}`\n\n"
        f"**Last rotation:** {last_rotation}\n"
        f"**Performing:** {performing} | **Replaced:** {replaced}"
    )
    dashboard = re.sub(
        r"<!-- ASO_START -->.*?<!-- ASO_END -->",
        f"<!-- ASO_START -->\n{aso_block}\n<!-- ASO_END -->",
        dashboard,
        flags=re.DOTALL,
    )

    return dashboard


def main() -> int:
    """Inject live data into wiki dashboard template.

    Git operations (clone wiki, push) are handled by the GitHub Actions
    workflow, not by this script, to avoid credential handling in Python.
    """
    repo_root = Path(os.getenv("GITHUB_WORKSPACE", ".")).resolve()
    wiki_dir = repo_root / "wiki"
    data_dir = repo_root / "marketing" / "data"

    if not wiki_dir.exists():
        print(f"[wiki-sync] Wiki directory not found: {wiki_dir}")
        return 1

    # Inject live data into dashboard
    dashboard_path = wiki_dir / "Daily-Metrics-Dashboard.md"
    if dashboard_path.exists():
        dashboard = dashboard_path.read_text(encoding="utf-8")
        updated = inject_dashboard_data(dashboard, data_dir)
        dashboard_path.write_text(updated, encoding="utf-8")
        print("[wiki-sync] Dashboard updated with live data")

    print(f"[wiki-sync] {len(list(wiki_dir.glob('*.md')))} wiki pages ready in {wiki_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
