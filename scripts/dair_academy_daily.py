#!/usr/bin/env python3
"""Daily DAIR.AI Academy learn loop — scrape, rank, queue implementable steals.

Sources (free tier only):
  https://academy.dair.ai/papers
  https://academy.dair.ai/dashboard  (BrowserOS/Chrome session for auth surfaces)

Public papers HTML is enough for CI. Dashboard resources (e.g. AGENTS.md study)
are optional extras when --extra-json is provided.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PAPERS_URL = "https://academy.dair.ai/papers"
WEEK_RE = re.compile(r'href="(/papers/week/[^"]+)"')
PAPER_RE = re.compile(r'href="(/papers/[a-z0-9][a-z0-9\-]+)"')
SKIP_SLUG_PREFIXES = ("/papers/week/", "/papers/collections/", "/papers?/")

ROI_WEIGHTS: dict[str, int] = {
    "agents.md": 10,
    "claude.md": 8,
    "context file": 8,
    "coding agent": 7,
    "harness": 7,
    "procedural": 7,
    "paywall": 7,
    "revenue": 7,
    "wqtu": 8,
    "durable": 5,
    "design docs": 6,
    "spec": 4,
    "governance": 5,
    "cheat": 6,
    "eval": 4,
    "agent": 3,
    "memory": 3,
    "graph": 3,
    "store": 3,
    "long-horizon": 6,
    "multi-day": 5,
}

IMPLEMENT_HINTS: list[tuple[str, str, str]] = [
    (
        "agents.md|context file|claude.md",
        "agents-md-signal",
        "Keep human AGENTS.md/CLAUDE.md lean; never auto-generate bloated context files",
    ),
    (
        "procedural graph|procedural",
        "procedural-graphs",
        "Encode long-horizon work as an explicit procedure graph agents can query",
    ),
    (
        "design docs|ai-native",
        "design-docs-ssot",
        "Prefer design-doc SSOT regeneration over silent code drift",
    ),
    (
        "harness",
        "harness-evolution",
        "Evolve harness with the model; do not copy expert trajectories onto weaker planners",
    ),
    (
        "cheat|governance|swarm",
        "agent-governance",
        "Shared agent channels need sanctioning/validation against reward hacking",
    ),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


ALLOWED_HOSTS = frozenset({"academy.dair.ai"})


def fetch_html(url: str, timeout: float = 45.0) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"refusing fetch outside academy.dair.ai: {url!r}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "RandomTimer-DAIR-Daily/1.0 "
                "(+https://github.com/IgorGanapolsky/Random-Timer)"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — host allowlisted
        return resp.read().decode("utf-8", errors="replace")


def slug_to_title(slug_path: str) -> str:
    slug = slug_path.rstrip("/").rsplit("/", 1)[-1]
    base = re.sub(r"-20\d{2}-\d{2}-\d{2}.*$", "", slug)
    return base.replace("-", " ").strip().title() or slug


def extract_paper_hrefs(html: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in PAPER_RE.finditer(html):
        href = match.group(1)
        if any(href.startswith(prefix) for prefix in SKIP_SLUG_PREFIXES):
            continue
        if href in seen:
            continue
        if re.search(r"-20\d{2}-\d{2}-\d{2}-", href) or href.count("-") >= 2:
            seen.add(href)
            found.append(href)
    return found


def latest_week_url(papers_html: str) -> str | None:
    weeks = WEEK_RE.findall(papers_html)
    return urljoin(PAPERS_URL, weeks[0]) if weeks else None


def score_text(text: str) -> tuple[int, list[str]]:
    low = text.lower()
    score = 0
    hits: list[str] = []
    for needle, weight in ROI_WEIGHTS.items():
        if needle in low:
            score += weight
            hits.append(needle)
    return score, hits


def implement_hints_for(text: str) -> list[dict[str, str]]:
    low = text.lower()
    out: list[dict[str, str]] = []
    for pattern, layer, steal in IMPLEMENT_HINTS:
        if any(part.strip() in low for part in pattern.split("|")):
            out.append({"layer": layer, "steal": steal, "pattern": pattern})
    return out


def rank_papers(week_html: str, week_url: str) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for href in extract_paper_hrefs(week_html):
        title = slug_to_title(href)
        idx = week_html.find(href)
        window = week_html[max(0, idx - 80) : idx + 600] if idx >= 0 else title
        score, hits = score_text(f"{title} {window}")
        ranked.append(
            {
                "title": title,
                "url": urljoin(PAPERS_URL, href),
                "roi_score": score,
                "roi_hits": hits,
                "implement_hints": implement_hints_for(f"{title} {window}"),
                "week_url": week_url,
            }
        )
    ranked.sort(key=lambda row: (-int(row["roi_score"]), row["title"]))
    return ranked


def build_report(
    *,
    papers_html: str,
    week_html: str | None = None,
    extras: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    week_url = latest_week_url(papers_html) or PAPERS_URL
    body = week_html
    if body is None and week_url != PAPERS_URL:
        body = fetch_html(week_url)
    if body is None:
        body = papers_html
    papers = rank_papers(body, week_url)
    implement_queue = [
        paper
        for paper in papers
        if paper["implement_hints"] and paper["roi_score"] >= 8
    ][:5]
    for extra in extras or []:
        score, hits = score_text(f"{extra.get('title', '')} {extra.get('summary', '')}")
        item = {
            "title": extra.get("title") or "extra",
            "url": extra.get("url") or "",
            "roi_score": score,
            "roi_hits": hits,
            "implement_hints": implement_hints_for(
                f"{extra.get('title', '')} {extra.get('summary', '')}"
            ),
            "source": "dashboard_extra",
        }
        if item["implement_hints"] and score >= 8:
            implement_queue.insert(0, item)
    return {
        "framework": "dair-academy-daily",
        "scraped_at_utc": _utc_now(),
        "papers_url": PAPERS_URL,
        "week_url": week_url,
        "paper_count": len(papers),
        "papers": papers[:20],
        "implement_queue": implement_queue,
        "tier_note": "use free papers feed + free dashboard session; skip paid Academy unlocks",
        "north_star": "WQTU + after-tax revenue path; prefer agent-stack steals that cut rework",
    }


def write_artifact(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--artifact", type=Path, default=None)
    parser.add_argument("--papers-html", type=Path, default=None)
    parser.add_argument("--week-html", type=Path, default=None)
    parser.add_argument("--extra-json", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    artifact = args.artifact or (repo / "marketing" / "data" / "dair_daily_learn.json")

    papers_html = (
        args.papers_html.read_text(encoding="utf-8")
        if args.papers_html and args.papers_html.is_file()
        else fetch_html(PAPERS_URL)
    )
    week_html = None
    if args.week_html and args.week_html.is_file():
        week_html = args.week_html.read_text(encoding="utf-8")

    extras: list[dict[str, str]] = []
    if args.extra_json and args.extra_json.is_file():
        extras = json.loads(args.extra_json.read_text(encoding="utf-8"))

    report = build_report(papers_html=papers_html, week_html=week_html, extras=extras)
    write_artifact(report, artifact)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"READY papers={report['paper_count']} queue={len(report['implement_queue'])}")
        print(f"artifact={artifact}")
        for item in report["implement_queue"][:3]:
            print(f"  - [{item['roi_score']}] {item['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
