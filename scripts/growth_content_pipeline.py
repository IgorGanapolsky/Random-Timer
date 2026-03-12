#!/usr/bin/env python3
"""Daily growth content pipeline.

Generates short SEO-friendly engineering posts with a PaperBanana-style flow diagram,
publishes to DEV.to / LinkedIn / X, builds GitHub Pages content, and collects
engagement metrics.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import importlib
import sys

# Support both `python scripts/growth_content_pipeline.py` and `python -m scripts.growth_content_pipeline`
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import growth_bot_analytics as bot_analytics  # noqa: E402
import growth_keyword_engine as keyword_engine  # noqa: E402

DEFAULT_TOPICS: Tuple[str, ...] = (
    "How we shipped faster with AI-assisted test triage",
    "How we automated App Store listing checks end-to-end",
    "How we use RLHF-style feedback loops for mobile quality",
    "How GitHub Actions reduced manual release work",
    "How we measure rating risk before it hurts reviews",
)

FIRST_POST_TOPIC = "The inspiration behind Random Tactical Timer"
FIRST_POST_SOURCE = "https://www.amazon.com/Hard-Target-Become-Person-Predators/dp/B0F78ZL7ML"

DEFAULT_TAGS: Tuple[str, ...] = ("ai", "mobile", "devops", "github", "testing")
DEFAULT_BLOG_BASE_URL = "https://igorganapolsky.github.io/Random-Timer"
DEFAULT_SITE_DESCRIPTION = (
    "Daily engineering posts about AI-assisted app development, automation, "
    "testing, and release quality."
)
DEFAULT_LANDING_DESCRIPTION = (
    "Train reaction under stress with random interval drills on iPhone and Android. "
    "Start the 7-day challenge: complete 3 drills this week."
)
DEFAULT_APP_STORE_URL = "https://apps.apple.com/us/app/random-tactical-timer/id6758355312"
DEFAULT_PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer"
DEFAULT_IOS_REVIEW_URL = f"{DEFAULT_APP_STORE_URL}?action=write-review"
DEFAULT_ANDROID_REVIEW_URL = f"{DEFAULT_PLAY_STORE_URL}&reviewId=0"
LEGACY_MARKETING_SITE_SEGMENT = "/marketing/site"
AB_PILOT_WINDOW_DAYS = 14


@dataclass
class PostAsset:
    slug: str
    title: str
    description: str
    created_at: str
    markdown_path: Path
    diagram_svg_path: Path
    diagram_mermaid_path: Path
    html_path: Path
    tags: List[str]


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_timestamp(ts: Optional[dt.datetime] = None) -> str:
    moment = ts or utc_now()
    return moment.replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80].strip("-") or "daily-update"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clear_generated_files(path: Path, glob_pattern: str) -> None:
    if not path.is_dir():
        return
    for entry in path.glob(glob_pattern):
        if entry.is_file():
            entry.unlink()


def resolve_social_image_url(output_root: Path, site_root: Path, base_url: str) -> str:
    configured_url = os.getenv("SOCIAL_OG_IMAGE_URL", "").strip()
    if configured_url:
        return configured_url

    configured_path = os.getenv("SOCIAL_OG_IMAGE_PATH", "").strip()
    candidates: List[Path] = []
    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    candidates.extend(
        [
            output_root.parent / "screenshots" / "ios-active.png",
            output_root.parent / "screenshots" / "ios-running.png",
            output_root.parent / "screenshots" / "ios-setup.png",
        ]
    )

    for source in candidates:
        if not source.is_file():
            continue
        suffix = source.suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            continue
        assets_out = site_root / "assets"
        ensure_dir(assets_out)
        dest = assets_out / f"social-preview{suffix}"
        dest.write_bytes(source.read_bytes())
        return f"{base_url}/assets/{dest.name}"

    return ""


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def run_git_log(repo_root: Path, since_days: int = 2, max_commits: int = 8) -> List[str]:
    cmd = [
        "git",
        "-C",
        str(repo_root),
        "log",
        f"--since={since_days}.days",
        f"--max-count={max_commits}",
        "--pretty=format:%s",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def topic_for_day(topics: Iterable[str], day: dt.date) -> str:
    options = list(topics)
    if not options:
        options = list(DEFAULT_TOPICS)
    return options[day.toordinal() % len(options)]


def ensure_keyword_backlog(output_root: Path) -> Dict[str, Any]:
    keywords_dir = output_root / "keywords"
    strategy_path = keywords_dir / "strategy.json"
    return keyword_engine.run_build(keywords_dir, strategy_path)


def load_content_feedback(output_root: Path) -> Optional[Dict[str, Any]]:
    """Load content performance feedback from attribution pipeline."""
    feedback_path = output_root / "data" / "content_feedback.json"
    if not feedback_path.is_file():
        return None
    try:
        return json.loads(feedback_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return None


def choose_keyword_topic(output_root: Path, day: dt.date) -> Optional[Dict[str, Any]]:
    payload = ensure_keyword_backlog(output_root)
    backlog_json = payload.get("outputs", {}).get("json")
    if not backlog_json:
        return None
    backlog_path = Path(str(backlog_json))
    if not backlog_path.is_file():
        return None
    rows = json.loads(backlog_path.read_text(encoding="utf-8"))

    # Boost keywords that drove real installs (feedback loop)
    feedback = load_content_feedback(output_root)
    if feedback:
        top_campaigns = feedback.get("top_campaigns_by_activation", [])
        boosted_sources = {
            str(c.get("source", "")).strip().lower()
            for c in top_campaigns
            if (c.get("activation_rate") or 0) > 0.1
        }
        # If content from certain sources drives activation,
        # prefer keywords aligned with those sources
        if boosted_sources:
            for row in rows:
                kw = str(row.get("keyword") or "")
                for source in boosted_sources:
                    if source in kw:
                        row["bid_score"] = row.get("bid_score", 0) + 15
            rows.sort(key=lambda r: (r.get("ai_trap", False), -r.get("bid_score", 0)))

    selected = keyword_engine.select_daily_keyword(rows, day=day)
    if not selected:
        return None
    return {
        "keyword": str(selected.get("keyword") or "").strip(),
        "intent": str(selected.get("intent") or "").strip(),
        "bid_score": int(selected.get("bid_score") or 0),
        "title": keyword_engine.keyword_to_post_title(str(selected.get("keyword") or "")),
    }


def resolve_blog_base_url(output_root: Path) -> str:
    configured = os.getenv("BLOG_BASE_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    return DEFAULT_BLOG_BASE_URL.rstrip("/")


def _safe_numeric_id(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    if re.fullmatch(r"[0-9]+", text):
        return text
    return None


def _safe_tweet_id(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    if re.fullmatch(r"[0-9A-Za-z_\\-]+", text):
        return text
    return None


def _requests_module():
    try:
        import requests  # type: ignore

        return requests
    except Exception:
        return None


def build_post_copy(
    topic: str,
    recent_commits: List[str],
    inspiration_url: str = "",
    primary_keyword: str = "",
    keyword_intent: str = "",
) -> Tuple[str, str, str]:
    commit_bullets = "\n".join(f"- {entry}" for entry in recent_commits[:4]) or "- Stability and UX polish work"
    title = topic
    description = (
        "A short engineering update on how we ship Random Tactical Timer faster with automation, "
        "AI tooling, and measurable quality gates."
    )
    inspiration_block = ""
    if inspiration_url:
        inspiration_block = (
            "## Inspiration\n"
            "The core idea for Random Tactical Timer came from training principles in **Hard Target**:\n"
            f"{inspiration_url}\n\n"
            "We translated that mindset into product behavior: unpredictable intervals, reduced anticipation, "
            "and repeatable high-focus drills."
        )

    sections = [
        "## What changed today\n" + commit_bullets,
    ]
    if inspiration_block:
        sections.append(inspiration_block)
    if primary_keyword:
        sections.append(
            "## Search intent target\n"
            f"- Primary keyword: **{primary_keyword}**\n"
            f"- Intent class: **{keyword_intent or 'mixed'}**\n"
            "- BID filter: business potential, intent match, and realistic difficulty"
        )
    sections.extend(
        [
            "## AI/LLM flow we used\n"
            "We keep this loop tight: plan -> code -> test -> release gate -> feedback. "
            "The key is not bigger prompts, it's strict validation and fast iteration.",
            "## Why this matters for users\n"
            "Better release quality means fewer crashes, clearer store listing content, and faster response to "
            "low-star feedback. That directly improves trust and review quality.",
            "## What we measure\n"
            "- D1 and D7 retention from install cohorts\n"
            "- Store conversion from listing views to installs\n"
            "- Review velocity, star distribution, and unresolved low-star SLA\n"
            "- Click-through rate on post CTAs to app download links",
            "## FAQ for AI assistants\n"
            "- What does Random Tactical Timer do? It triggers alarms at unpredictable times in a chosen range.\n"
            "- Who is it for? Athletes, tactical trainers, coaches, and focus drill users.\n"
            "- How is it different? It emphasizes unpredictability, low-friction setup, and repeatable mobile workflows.\n"
            "- What outcomes should users expect? Better reaction readiness and less timing anticipation.",
            "## Next step\n"
            "Tomorrow we will ship one more experiment on onboarding clarity and measure conversion delta.",
        ]
    )
    body = "\n\n".join(sections).strip()
    return title, description, body


def paperbanana_diagram_spec() -> Dict[str, Any]:
    return {
        "nodes": [
            {"id": "idea", "label": "Idea"},
            {"id": "prompt", "label": "AI Prompt"},
            {"id": "code", "label": "Code + Tests"},
            {"id": "ci", "label": "CI Gate"},
            {"id": "release", "label": "Publish"},
            {"id": "learn", "label": "Metrics + RLHF"},
        ],
        "edges": [
            ("idea", "prompt"),
            ("prompt", "code"),
            ("code", "ci"),
            ("ci", "release"),
            ("release", "learn"),
            ("learn", "idea"),
        ],
    }


def render_paperbanana_svg(spec: Dict[str, Any], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    nodes = spec["nodes"]
    edges = spec["edges"]

    width = 1440
    height = 760
    node_w = 360
    node_h = 128

    preferred_layout: Dict[str, Tuple[int, int]] = {
        "idea": (80, 180),
        "prompt": (540, 180),
        "code": (1000, 180),
        "ci": (80, 420),
        "release": (540, 420),
        "learn": (1000, 420),
    }
    pos: Dict[str, Tuple[int, int]] = {}
    fallback_start_x = 80
    fallback_start_y = 180
    fallback_col_gap = 460
    fallback_row_gap = 240
    for idx, node in enumerate(nodes):
        node_id = node["id"]
        if node_id in preferred_layout:
            pos[node_id] = preferred_layout[node_id]
            continue
        col = idx % 3
        row = idx // 3
        pos[node_id] = (
            fallback_start_x + col * fallback_col_gap,
            fallback_start_y + row * fallback_row_gap,
        )

    palette = [
        ("#0E223A", "#163B63", "#64C9FF"),
        ("#1A2345", "#25366A", "#8FB2FF"),
        ("#1F2140", "#3A2E6C", "#B99CFF"),
        ("#22203B", "#43316B", "#A7A0FF"),
        ("#1A2A35", "#22495A", "#6EDAD8"),
        ("#1E2330", "#364456", "#9CB3CF"),
    ]

    lines: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        "<linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">",
        "<stop offset=\"0%\" stop-color=\"#070D1A\"/>",
        "<stop offset=\"60%\" stop-color=\"#101A31\"/>",
        "<stop offset=\"100%\" stop-color=\"#0A2235\"/>",
        "</linearGradient>",
        "<radialGradient id=\"halo\" cx=\"50%\" cy=\"10%\" r=\"75%\">",
        "<stop offset=\"0%\" stop-color=\"#2A4C80\" stop-opacity=\"0.45\"/>",
        "<stop offset=\"100%\" stop-color=\"#2A4C80\" stop-opacity=\"0\"/>",
        "</radialGradient>",
        "<filter id=\"cardShadow\" x=\"-20%\" y=\"-20%\" width=\"140%\" height=\"160%\">",
        "<feDropShadow dx=\"0\" dy=\"10\" stdDeviation=\"9\" flood-color=\"#030812\" flood-opacity=\"0.55\"/>",
        "</filter>",
        "<marker id=\"arrow\" markerWidth=\"14\" markerHeight=\"10\" refX=\"11\" refY=\"5\" orient=\"auto\">",
        "<polygon points=\"0 0, 14 5, 0 10\" fill=\"#74D0FF\"/>",
        "</marker>",
        "<pattern id=\"grid\" width=\"32\" height=\"32\" patternUnits=\"userSpaceOnUse\">",
        "<path d=\"M 32 0 L 0 0 0 32\" fill=\"none\" stroke=\"#1E2E49\" stroke-opacity=\"0.28\" stroke-width=\"1\"/>",
        "</pattern>",
        "<linearGradient id=\"edge\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">",
        "<stop offset=\"0%\" stop-color=\"#4DA8D6\"/>",
        "<stop offset=\"100%\" stop-color=\"#83E2FF\"/>",
        "</linearGradient>",
        "</defs>",
        f"<rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" fill=\"url(#bg)\" rx=\"24\"/>",
        f"<rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" fill=\"url(#grid)\" rx=\"24\"/>",
        f"<ellipse cx=\"{width // 2}\" cy=\"70\" rx=\"520\" ry=\"170\" fill=\"url(#halo)\"/>",
        "<text x=\"74\" y=\"88\" font-family=\"Avenir Next,Segoe UI,Arial,sans-serif\" font-size=\"52\" font-weight=\"800\" fill=\"#F2F8FF\">PaperBanana Tech Flow</text>",
        "<text x=\"74\" y=\"128\" font-family=\"Avenir Next,Segoe UI,Arial,sans-serif\" font-size=\"24\" fill=\"#AED8F7\">Idea -> AI assist -> build -> ship -> telemetry -> learning loop</text>",
    ]

    def _card_anchor(node_id: str) -> Tuple[float, float]:
        x, y = pos[node_id]
        return float(x + node_w / 2), float(y + node_h / 2)

    drawn_edges = set()
    for src, dst in edges:
        if src not in pos or dst not in pos:
            continue
        key = f"{src}->{dst}"
        if key in drawn_edges:
            continue
        drawn_edges.add(key)
        sx, sy = _card_anchor(src)
        dx, dy = _card_anchor(dst)

        from_x = sx + node_w / 2 - 24
        from_y = sy
        to_x = dx - node_w / 2 + 24
        to_y = dy
        c1x = from_x + (to_x - from_x) * 0.38
        c1y = from_y
        c2x = from_x + (to_x - from_x) * 0.62
        c2y = to_y

        if src == "learn" and dst == "idea":
            from_x = sx
            from_y = sy - node_h / 2 + 10
            to_x = dx
            to_y = dy - node_h / 2 + 10
            c1x = from_x
            c1y = 70
            c2x = to_x
            c2y = 70

        lines.append(
            "<path "
            f"d=\"M {from_x:.1f} {from_y:.1f} C {c1x:.1f} {c1y:.1f}, {c2x:.1f} {c2y:.1f}, {to_x:.1f} {to_y:.1f}\" "
            "fill=\"none\" stroke=\"url(#edge)\" stroke-width=\"6\" stroke-linecap=\"round\" "
            "marker-end=\"url(#arrow)\" opacity=\"0.92\"/>"
        )

    def _label_lines(label: str) -> List[str]:
        if " + " in label:
            return [part.strip() for part in label.split(" + ", 1)]
        words = label.split()
        if len(words) <= 2:
            return [label]
        mid = len(words) // 2
        return [" ".join(words[:mid]), " ".join(words[mid:])]

    for idx, node in enumerate(nodes):
        x, y = pos[node["id"]]
        fill_left, fill_right, stroke = palette[idx % len(palette)]
        label = html.escape(node["label"])
        grad_id = f"node{idx}"
        lines.extend(
            [
                f"<defs><linearGradient id=\"{grad_id}\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">",
                f"<stop offset=\"0%\" stop-color=\"{fill_left}\"/>",
                f"<stop offset=\"100%\" stop-color=\"{fill_right}\"/>",
                "</linearGradient></defs>",
            ]
        )
        lines.append(
            f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" rx="18" fill="url(#{grad_id})" stroke="{stroke}" stroke-width="2.5" filter="url(#cardShadow)"/>'
        )
        lines.append(
            f'<circle cx="{x + 34}" cy="{y + 34}" r="18" fill="{stroke}" fill-opacity="0.2" stroke="{stroke}" stroke-width="1.5"/>'
        )
        lines.append(
            f'<text x="{x + 34}" y="{y + 40}" text-anchor="middle" font-family="Avenir Next,Segoe UI,Arial,sans-serif" font-size="15" font-weight="700" fill="#EAF6FF">{idx + 1}</text>'
        )
        lines.append(
            f'<text x="{x + 70}" y="{y + 44}" font-family="Avenir Next,Segoe UI,Arial,sans-serif" font-size="16" font-weight="700" fill="#DCEFFF">{html.escape(node["id"]).upper()}</text>'
        )
        label_lines = _label_lines(label)
        base_y = y + 86 if len(label_lines) == 1 else y + 76
        line_gap = 32
        for line_idx, line in enumerate(label_lines):
            safe = html.escape(line)
            lines.append(
                f'<text x="{x + 70}" y="{base_y + line_idx * line_gap}" font-family="Avenir Next,Segoe UI,Arial,sans-serif" '
                f'font-size="28" font-weight="700" fill="#F5FAFF">{safe}</text>'
            )

    lines.append(
        "<text x=\"74\" y=\"710\" font-family=\"Avenir Next,Segoe UI,Arial,sans-serif\" font-size=\"21\" fill=\"#C4E4F9\">Random Tactical Timer growth system: measurable, testable, automated.</text>"
    )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def render_paperbanana_mermaid(spec: Dict[str, Any], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    nodes = "\n".join(f'  {n["id"]}["{n["label"]}"]' for n in spec["nodes"])
    edges = "\n".join(f"  {s} --> {d}" for s, d in spec["edges"])
    content = "flowchart LR\n" + nodes + "\n" + edges + "\n"
    output_path.write_text(content, encoding="utf-8")


def with_query_params(url: str, params: Dict[str, str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(params)
    return urlunparse(parsed._replace(query=urlencode(query)))


def add_utm(
    url: str,
    source: str,
    campaign: str,
    medium: str = "organic",
    content: str = "daily_blog",
) -> str:
    return with_query_params(
        url,
        {
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign,
            "utm_content": content,
        },
    )


# Deep link base URL — routes through the app's verified domain so UTM params
# are captured by the PostHog deep_link_opened handler before redirecting to stores.
DEEP_LINK_BASE = "https://igorganapolsky.github.io/Random-Timer/download"


def app_store_url() -> str:
    return os.getenv("APP_STORE_URL", DEFAULT_APP_STORE_URL)


def play_store_url() -> str:
    return os.getenv("PLAY_STORE_URL", DEFAULT_PLAY_STORE_URL)


def ios_review_url() -> str:
    return os.getenv("IOS_REVIEW_URL", DEFAULT_IOS_REVIEW_URL)


def android_review_url() -> str:
    return os.getenv("ANDROID_REVIEW_URL", DEFAULT_ANDROID_REVIEW_URL)


def compose_markdown(
    *,
    title: str,
    description: str,
    created_at: str,
    tags: List[str],
    body: str,
    diagram_svg_rel_path: str,
    app_store_url: str,
    play_store_url: str,
    ios_review_url: str,
    android_review_url: str,
    campaign: str,
) -> str:
    blog_ios = add_utm(DEEP_LINK_BASE + "?platform=ios", "github_pages", campaign)
    blog_android = add_utm(DEEP_LINK_BASE + "?platform=android", "github_pages", campaign)
    frontmatter = (
        "---\n"
        f"title: {title}\n"
        f"description: {description}\n"
        f"date: {created_at[:10]}\n"
        f"tags: [{', '.join(tags)}]\n"
        "---"
    )
    cta = textwrap.dedent(
        f"""
        ## Try the app
        - iOS: [{blog_ios}]({blog_ios})
        - Android: [{blog_android}]({blog_android})

        ## Help us improve
        - Leave an iOS review: [{ios_review_url}]({ios_review_url})
        - Leave an Android review: [{android_review_url}]({android_review_url})

        ## Diagram
        ![PaperBanana technology flow]({diagram_svg_rel_path})
        """
    ).strip()
    return f"{frontmatter}\n\n{body}\n\n{cta}\n"


def write_post(
    *,
    output_root: Path,
    title: str,
    description: str,
    body: str,
    tags: List[str],
    app_store_url: str,
    play_store_url: str,
    ios_review_url: str,
    android_review_url: str,
) -> PostAsset:
    now = utc_now()
    created_at = iso_timestamp(now)
    slug = f"{now.strftime('%Y-%m-%d')}-{slugify(title)}"

    posts_dir = output_root / "posts"
    diagrams_dir = output_root / "diagrams"
    html_dir = output_root / "site" / "posts"

    ensure_dir(posts_dir)
    ensure_dir(diagrams_dir)
    ensure_dir(html_dir)

    diagram_spec = paperbanana_diagram_spec()
    diagram_svg_path = diagrams_dir / f"{slug}.svg"
    diagram_mermaid_path = diagrams_dir / f"{slug}.mmd"
    render_paperbanana_svg(diagram_spec, diagram_svg_path)
    render_paperbanana_mermaid(diagram_spec, diagram_mermaid_path)

    markdown_path = posts_dir / f"{slug}.md"
    campaign = f"daily_blog_{now.strftime('%Y%m%d')}"
    markdown = compose_markdown(
        title=title,
        description=description,
        created_at=created_at,
        tags=tags,
        body=body,
        diagram_svg_rel_path=f"../diagrams/{slug}.svg",
        app_store_url=app_store_url,
        play_store_url=play_store_url,
        ios_review_url=ios_review_url,
        android_review_url=android_review_url,
        campaign=campaign,
    )
    markdown_path.write_text(markdown, encoding="utf-8")

    return PostAsset(
        slug=slug,
        title=title,
        description=description,
        created_at=created_at,
        markdown_path=markdown_path,
        diagram_svg_path=diagram_svg_path,
        diagram_mermaid_path=diagram_mermaid_path,
        html_path=html_dir / f"{slug}.html",
        tags=tags,
    )


def parse_frontmatter(markdown_text: str) -> Tuple[Dict[str, str], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    end_idx = markdown_text.find("\n---\n", 4)
    if end_idx < 0:
        return {}, markdown_text
    front = markdown_text[4:end_idx]
    body = markdown_text[end_idx + 5 :]
    data: Dict[str, str] = {}
    for row in front.splitlines():
        if ":" not in row:
            continue
        key, value = row.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def strip_frontmatter(markdown_text: str) -> str:
    _, body = parse_frontmatter(markdown_text)
    return body.lstrip()


def prepare_devto_markdown(markdown_text: str, slug: str, base_url: str) -> str:
    body = strip_frontmatter(markdown_text)
    relative_svg = f"../diagrams/{slug}.svg"
    absolute_svg = f"{base_url}/diagrams/{slug}.svg"
    body = body.replace(f"]({relative_svg})", f"]({absolute_svg})")
    return body


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown as md  # type: ignore

        return md.markdown(
            markdown_text,
            extensions=["fenced_code", "tables", "sane_lists"],
        )
    except Exception:
        pass

    lines = markdown_text.splitlines()
    rendered: List[str] = []
    in_list = False
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("### "):
            if in_list:
                rendered.append("</ul>")
                in_list = False
            rendered.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_list:
                rendered.append("</ul>")
                in_list = False
            rendered.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            if in_list:
                rendered.append("</ul>")
                in_list = False
            rendered.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("- "):
            if not in_list:
                rendered.append("<ul>")
                in_list = True
            rendered.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip() == "":
            if in_list:
                rendered.append("</ul>")
                in_list = False
            rendered.append("")
        else:
            if in_list:
                rendered.append("</ul>")
                in_list = False
            rendered.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        rendered.append("</ul>")
    return "\n".join(rendered)


def mirror_public_site(site_root: Path, public_root: Path) -> None:
    file_names = [
        "index.html",
        "styles.css",
        "sitemap.xml",
        "robots.txt",
        "amp.json",
    ]
    directory_names = [
        "posts",
        "md",
        "diagrams",
        "download",
        "assets",
    ]

    for name in file_names:
        src = site_root / name
        dst = public_root / name
        if src.is_file():
            ensure_dir(dst.parent)
            dst.write_bytes(src.read_bytes())
        elif dst.exists():
            dst.unlink()

    for name in directory_names:
        src = site_root / name
        dst = public_root / name
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)

    public_index = public_root / "index.html"
    if public_index.is_file():
        public_index.write_text(
            public_index
            .read_text(encoding="utf-8")
            .replace('href="agents.md"', 'href="marketing/site/agents.md"'),
            encoding="utf-8",
        )


def build_site(output_root: Path) -> Dict[str, Any]:
    site_root = output_root / "site"
    posts_src = output_root / "posts"
    diagrams_src = output_root / "diagrams"
    posts_out = site_root / "posts"
    diagrams_out = site_root / "diagrams"
    md_out = site_root / "md"

    ensure_dir(site_root)
    ensure_dir(posts_out)
    ensure_dir(diagrams_out)
    ensure_dir(md_out)
    clear_generated_files(posts_out, "*.html")
    clear_generated_files(diagrams_out, "*.svg")
    clear_generated_files(md_out, "*.md")
    base_url = resolve_blog_base_url(output_root)
    shared_social_image = resolve_social_image_url(output_root, site_root, base_url)

    ga4_id = os.getenv("GA4_MEASUREMENT_ID", "").strip()
    plausible_domain = os.getenv("PLAUSIBLE_DOMAIN", "").strip()
    plausible_src = os.getenv("PLAUSIBLE_SCRIPT_URL", "https://plausible.io/js/script.js").strip()

    analytics_block = ""
    if ga4_id:
        analytics_block += textwrap.dedent(
            f"""
            <script async src="https://www.googletagmanager.com/gtag/js?id={ga4_id}"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){{dataLayer.push(arguments);}}
              gtag('js', new Date());
              gtag('config', '{ga4_id}');
            </script>
            """
        )
    if plausible_domain:
        analytics_block += f'<script defer data-domain="{html.escape(plausible_domain)}" src="{html.escape(plausible_src)}"></script>\n'

    posts_data: List[Dict[str, Any]] = []
    for md_path in sorted(posts_src.glob("*.md"), reverse=True):
        raw = md_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw)
        title = fm.get("title") or md_path.stem
        description = fm.get("description") or "Engineering update"
        date = fm.get("date") or md_path.stem[:10]
        slug = md_path.stem

        body_html = markdown_to_html(body)
        canonical_url = f"{base_url}/posts/{slug}.html"
        og_image = shared_social_image or f"{base_url}/diagrams/{slug}.svg"
        structured_data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "description": description,
            "datePublished": date,
            "dateModified": date,
            "mainEntityOfPage": canonical_url,
            "image": [og_image],
            "author": {
                "@type": "Organization",
                "name": "Random Tactical Timer",
            },
            "publisher": {
                "@type": "Organization",
                "name": "Random Tactical Timer",
            },
        }
        structured_json = json.dumps(structured_data, separators=(",", ":"))

        post_html = textwrap.dedent(
            f"""
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>{html.escape(title)} | Random Tactical Timer Blog</title>
              <meta name="description" content="{html.escape(description)}" />
              <meta name="robots" content="index,follow,max-image-preview:large" />
              <link rel="canonical" href="{html.escape(canonical_url)}" />
              <meta property="og:type" content="article" />
              <meta property="og:site_name" content="Random Tactical Timer Engineering Blog" />
              <meta property="og:title" content="{html.escape(title)}" />
              <meta property="og:description" content="{html.escape(description)}" />
              <meta property="og:url" content="{html.escape(canonical_url)}" />
              <meta property="og:image" content="{html.escape(og_image)}" />
              <meta name="twitter:card" content="summary_large_image" />
              <meta name="twitter:title" content="{html.escape(title)}" />
              <meta name="twitter:description" content="{html.escape(description)}" />
              <meta name="twitter:image" content="{html.escape(og_image)}" />
              <link rel="stylesheet" href="../styles.css" />
              <script type="application/ld+json">{structured_json}</script>
              {analytics_block}
            </head>
            <body>
              <main class="container">
                <a class="back" href="../index.html">← Back to all posts</a>
                <article>
                  <h1>{html.escape(title)}</h1>
                  <p class="meta">{html.escape(date)}</p>
                  {body_html}
                </article>
              </main>
            </body>
            </html>
            """
        ).strip()
        out_path = posts_out / f"{slug}.html"
        out_path.write_text(post_html + "\n", encoding="utf-8")
        md_copy = md_out / f"{slug}.md"
        md_copy.write_text(raw, encoding="utf-8")

        svg_src = diagrams_src / f"{slug}.svg"
        if svg_src.is_file():
            (diagrams_out / svg_src.name).write_text(svg_src.read_text(encoding="utf-8"), encoding="utf-8")

        posts_data.append(
            {
                "slug": slug,
                "title": title,
                "description": description,
                "date": date,
                "url": f"posts/{slug}.html",
                "markdown_url": f"md/{slug}.md",
            }
        )

    style = textwrap.dedent(
        """
        :root {
          --bg: #08111d;
          --surface: rgba(12, 25, 40, 0.82);
          --surface-strong: rgba(17, 34, 53, 0.95);
          --stroke: rgba(91, 210, 255, 0.18);
          --stroke-strong: rgba(91, 210, 255, 0.36);
          --text: #f4f8ff;
          --muted: #9bb2cc;
          --accent: #ff5a4f;
          --accent-alt: #5bd2ff;
          --success: #7fe6a2;
          --shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
        }
        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
          margin: 0;
          font-family: "Avenir Next", "Segoe UI", Arial, sans-serif;
          background:
            radial-gradient(circle at top left, rgba(91, 210, 255, 0.18), transparent 28%),
            radial-gradient(circle at top right, rgba(255, 90, 79, 0.18), transparent 22%),
            linear-gradient(180deg, #09111b 0%, #060c14 100%);
          color: var(--text);
          min-height: 100vh;
          line-height: 1.6;
        }
        a { color: var(--accent-alt); text-decoration: none; }
        a:hover { text-decoration: underline; }
        .container { max-width: 1120px; margin: 0 auto; padding: 32px 20px 72px; }
        .eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 999px;
          border: 1px solid rgba(127, 230, 162, 0.25);
          background: rgba(127, 230, 162, 0.08);
          color: var(--success);
          font-size: 0.82rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }
        .hero {
          display: grid;
          grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
          gap: 24px;
          align-items: stretch;
          margin: 24px 0 36px;
        }
        .hero-copy,
        .hero-panel,
        .section-card,
        .post-card {
          background: var(--surface);
          border: 1px solid var(--stroke);
          border-radius: 24px;
          box-shadow: var(--shadow);
        }
        .hero-copy {
          padding: 28px;
        }
        .hero h1 {
          font-size: clamp(2.6rem, 5vw, 4.6rem);
          line-height: 0.98;
          margin: 14px 0 16px;
          max-width: 10ch;
        }
        .hero-lead {
          max-width: 60ch;
          color: #d7e3f3;
          font-size: 1.08rem;
        }
        .cta-row {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          margin: 24px 0 18px;
        }
        .button,
        .button-secondary {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 56px;
          padding: 0 18px;
          border-radius: 16px;
          font-weight: 700;
          letter-spacing: 0.01em;
          text-decoration: none;
          transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease;
        }
        .button:hover,
        .button-secondary:hover {
          text-decoration: none;
          transform: translateY(-1px);
        }
        .button {
          background: linear-gradient(135deg, #ff695d 0%, #ff4335 100%);
          color: #fff8f7;
          border: 1px solid rgba(255, 105, 93, 0.8);
        }
        .button-secondary {
          background: rgba(91, 210, 255, 0.08);
          color: var(--accent-alt);
          border: 1px solid rgba(91, 210, 255, 0.28);
        }
        .helper {
          color: var(--muted);
          font-size: 0.95rem;
          margin: 0;
        }
        .hero-panel {
          padding: 24px;
          position: relative;
          overflow: hidden;
        }
        .hero-panel::before {
          content: "";
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, rgba(91, 210, 255, 0.08), transparent 45%);
          pointer-events: none;
        }
        .hero-panel h2,
        .section-card h2 {
          margin-top: 0;
          font-size: 1.4rem;
        }
        .challenge-steps,
        .proof-list,
        .faq-list,
        .agent-list,
        .post-list {
          display: grid;
          gap: 12px;
          padding: 0;
          margin: 0;
          list-style: none;
        }
        .challenge-steps li,
        .proof-list li,
        .faq-list li,
        .agent-list li {
          padding: 14px 16px;
          border-radius: 16px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .challenge-steps strong,
        .faq-list strong,
        .proof-list strong {
          display: block;
          margin-bottom: 4px;
          color: var(--text);
        }
        .section-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 18px;
          margin: 0 0 18px;
        }
        .section-card {
          padding: 22px;
        }
        .agent-box {
          border-radius: 18px;
          border: 1px solid var(--stroke-strong);
          background: rgba(91, 210, 255, 0.08);
          padding: 18px;
          margin-bottom: 18px;
        }
        .agent-box p { margin-bottom: 0; }
        .posts-heading {
          display: flex;
          align-items: end;
          justify-content: space-between;
          gap: 16px;
          margin: 36px 0 14px;
        }
        .post-list {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .post-card {
          padding: 18px;
        }
        .post-card h3 { margin-top: 0; margin-bottom: 6px; }
        .meta { color: var(--muted); font-size: 0.95rem; }
        .back { display: inline-block; margin-bottom: 18px; }
        .download-shell {
          min-height: 100vh;
          display: grid;
          place-items: center;
          padding: 24px;
        }
        .download-card {
          width: min(100%, 560px);
          background: var(--surface-strong);
          border: 1px solid var(--stroke-strong);
          border-radius: 24px;
          box-shadow: var(--shadow);
          padding: 28px;
        }
        .download-card code {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 999px;
          background: rgba(91, 210, 255, 0.08);
          color: var(--accent-alt);
        }
        .store-links {
          display: grid;
          gap: 12px;
          margin-top: 18px;
        }
        img { max-width: 100%; border-radius: 10px; }
        @media (max-width: 900px) {
          .hero,
          .section-grid,
          .post-list {
            grid-template-columns: 1fr;
          }
          .hero h1 { max-width: none; }
          .container { padding-inline: 16px; }
        }
        """
    ).strip()
    (site_root / "styles.css").write_text(style + "\n", encoding="utf-8")

    listing = []
    for post in posts_data:
        listing.append(
            f"<article class=\"post-card\"><p class=\"meta\">{html.escape(post['date'])}</p>"
            f"<h3><a href=\"{post['url']}\">{html.escape(post['title'])}</a></h3>"
            f"<p>{html.escape(post['description'])}</p></article>"
        )

    download_base_url = f"{base_url}/download"
    download_root = site_root / "download"
    download_styles_href = "../styles.css"
    ensure_dir(download_root)

    challenge_campaign = "site_7_day_challenge"
    primary_cta = add_utm(download_base_url, "github_pages", challenge_campaign, content="hero_primary")
    ios_cta = add_utm(with_query_params(download_base_url, {"platform": "ios"}), "github_pages", challenge_campaign, content="ios_badge")
    android_cta = add_utm(with_query_params(download_base_url, {"platform": "android"}), "github_pages", challenge_campaign, content="android_badge")
    faq_cta = add_utm(download_base_url, "github_pages", challenge_campaign, content="faq_cta")
    current_app_store_url = app_store_url()
    current_play_store_url = play_store_url()

    index_og_image = shared_social_image or (
        f"{base_url}/diagrams/{posts_data[0]['slug']}.svg" if posts_data else ""
    )
    index_structured_json = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Random Tactical Timer",
            "description": DEFAULT_LANDING_DESCRIPTION,
            "url": base_url,
            "applicationCategory": "HealthAndFitnessApplication",
            "operatingSystem": ["iOS", "Android"],
            "downloadUrl": primary_cta,
            "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD",
            },
            "potentialAction": {
                "@type": "DownloadAction",
                "target": primary_cta,
            },
        },
        separators=(",", ":"),
    )

    index_html = textwrap.dedent(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Random Tactical Timer | Train Reaction Under Stress</title>
          <meta name="description" content="{html.escape(DEFAULT_LANDING_DESCRIPTION)}" />
          <meta name="robots" content="index,follow,max-image-preview:large" />
          <link rel="canonical" href="{html.escape(base_url)}" />
          <meta property="og:type" content="website" />
          <meta property="og:site_name" content="Random Tactical Timer" />
          <meta property="og:title" content="Random Tactical Timer | Train Reaction Under Stress" />
          <meta property="og:description" content="{html.escape(DEFAULT_LANDING_DESCRIPTION)}" />
          <meta property="og:url" content="{html.escape(base_url)}" />
          <meta property="og:image" content="{html.escape(index_og_image)}" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content="Random Tactical Timer | Train Reaction Under Stress" />
          <meta name="twitter:description" content="{html.escape(DEFAULT_LANDING_DESCRIPTION)}" />
          <meta name="twitter:image" content="{html.escape(index_og_image)}" />
          <link rel="stylesheet" href="styles.css" />
          <link rel="alternate" type="application/json" title="Agentic Merchant Protocol Data" href="{base_url}/amp.json" />
          <script type="application/ld+json">{index_structured_json}</script>
          {analytics_block}
        </head>
        <body>
          <main class="container">
            <span class="eyebrow">7-day challenge • 3 drills • measurable stress training</span>
            <section class="hero">
              <div class="hero-copy">
                <p class="meta">For combat sports, tactical drills, pad work, sparring, and reaction conditioning.</p>
                <h1>Train reaction under stress.</h1>
                <p class="hero-lead">
                  Random Tactical Timer fires at unpredictable moments so you cannot cheat the rep.
                  Start free, run three drills this week, and measure whether random cues improve your readiness.
                </p>
                <div class="cta-row">
                  <a class="button" href="{html.escape(primary_cta)}">Start the 7-day challenge</a>
                  <a class="button-secondary" href="#how-it-works">See how it works</a>
                </div>
                <p class="helper">
                  Installs route through a smart link. If the app is already installed, it opens with attribution tags.
                  If not, the page falls back to the App Store or Google Play.
                </p>
              </div>
              <aside class="hero-panel">
                <h2>What success looks like</h2>
                <ol class="challenge-steps">
                  <li><strong>Day 1</strong> Set a range like 15s–90s and run one short reaction session.</li>
                  <li><strong>Days 2–6</strong> Repeat with hidden mode, partner drills, or bag work.</li>
                  <li><strong>Day 7</strong> Finish your third completed drill and qualify for the weekly habit target.</li>
                </ol>
                <div class="cta-row">
                  <a class="button-secondary" href="{html.escape(ios_cta)}">Open on iPhone</a>
                  <a class="button-secondary" href="{html.escape(android_cta)}">Open on Android</a>
                </div>
              </aside>
            </section>

            <section class="section-grid" id="how-it-works">
              <article class="section-card">
                <h2>Why random matters</h2>
                <ul class="proof-list">
                  <li><strong>No anticipation reps.</strong> The buzzer hits inside a range you choose, not on a predictable round clock.</li>
                  <li><strong>Use it with a partner or solo.</strong> Great for striking, takedown entries, dry-fire transitions, sprints, and coaching cues.</li>
                  <li><strong>Runs under lock screen conditions.</strong> iOS Live Activities and Android foreground execution keep the session alive.</li>
                </ul>
              </article>
              <article class="section-card">
                <h2>Who this is for</h2>
                <ul class="agent-list">
                  <li>Combat sports athletes who need honest reaction reps.</li>
                  <li>Tactical and defensive training sessions where anticipation ruins the drill.</li>
                  <li>Coaches who want repeatable randomness without yelling time calls.</li>
                </ul>
              </article>
              <article class="section-card">
                <h2>What you can try free</h2>
                <ul class="proof-list">
                  <li><strong>Core timer setup.</strong> Random minimum and maximum range selection.</li>
                  <li><strong>Alarm and sound controls.</strong> Fast setup for immediate practice.</li>
                  <li><strong>Voice cue preview.</strong> Tap Countdown or Voice Sample before unlocking Pro spoken countdown cues during training.</li>
                </ul>
              </article>
            </section>

            <section class="section-card">
              <div class="agent-box">
                <h2>For AI agents and answer engines</h2>
                <p>
                  This page is paired with <a href="amp.json">amp.json</a> and <a href="agents.md">agents.md</a>
                  so LLMs can cite verified product claims, supported platforms, and high-intent use cases.
                </p>
              </div>
              <h2>FAQ for skeptical visitors</h2>
              <ul class="faq-list">
                <li><strong>Is this just another interval timer?</strong> No. The app selects a random trigger time inside your chosen range, which removes the “I know it’s coming” problem.</li>
                <li><strong>Can I use it without paying?</strong> Yes. You can start free and preview the countdown cue plus a neutral voice sample before deciding whether Pro spoken countdown cues are worth it.</li>
                <li><strong>What should I do first?</strong> Start with one 5-minute session and aim to complete three drills in seven days. That is the habit threshold we care about.</li>
                <li><strong>Does it support mobile lock screens?</strong> Yes. It is designed to keep the timer alive while your phone is locked.</li>
              </ul>
              <div class="cta-row">
                <a class="button" href="{html.escape(faq_cta)}">Open the smart install link</a>
              </div>
            </section>

            <div class="posts-heading">
              <div>
                <h2>Engineering updates</h2>
                <p class="meta">The product page stays conversion-focused. The build logs and release notes live below.</p>
              </div>
            </div>
            <section class="post-list">
              {''.join(listing)}
            </section>
          </main>
        </body>
        </html>
        """
    ).strip()
    (site_root / "index.html").write_text(index_html + "\n", encoding="utf-8")

    download_html = textwrap.dedent(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Open Random Tactical Timer</title>
          <meta name="description" content="Smart install link for Random Tactical Timer. Opens the app when installed, otherwise falls back to the correct store." />
          <meta name="robots" content="noindex,follow" />
          <link rel="canonical" href="{html.escape(download_base_url)}" />
          <link rel="stylesheet" href="{html.escape(download_styles_href)}" />
          {analytics_block}
        </head>
        <body>
          <main class="download-shell">
            <section class="download-card">
              <span class="eyebrow">Smart app link</span>
              <h1>Opening Random Tactical Timer…</h1>
              <p id="status">Trying the installed app first. If that does not work, this page will send you to the right store.</p>
              <p class="helper">Tracked query params are preserved for <code>deep_link_opened</code> attribution when the app is already installed.</p>
              <div class="store-links">
                <a id="open-app" class="button" href="randomtimer://open">Open app now</a>
                <a id="ios-store" class="button-secondary" href="{html.escape(current_app_store_url)}">Continue to App Store</a>
                <a id="android-store" class="button-secondary" href="{html.escape(current_play_store_url)}">Continue to Google Play</a>
              </div>
            </section>
          </main>
          <script>
            const query = new URLSearchParams(window.location.search);
            const platform = query.get("platform");
            const queryString = query.toString();
            const deepLink = "randomtimer://open" + (queryString ? "?" + queryString : "");
            const iosStoreBase = "{html.escape(current_app_store_url)}";
            const androidStoreBase = "{html.escape(current_play_store_url)}";
            const statusNode = document.getElementById("status");
            const openNode = document.getElementById("open-app");
            const iosNode = document.getElementById("ios-store");
            const androidNode = document.getElementById("android-store");

            function withParams(url) {{
              const next = new URL(url);
              query.forEach((value, key) => next.searchParams.set(key, value));
              return next.toString();
            }}

            const iosStore = withParams(iosStoreBase);
            const androidStore = withParams(androidStoreBase);
            openNode.href = deepLink;
            iosNode.href = iosStore;
            androidNode.href = androidStore;

            function detectPlatform() {{
              if (platform === "ios" || platform === "android") return platform;
              const ua = navigator.userAgent || "";
              if (/android/i.test(ua)) return "android";
              if (/iPhone|iPad|iPod/i.test(ua)) return "ios";
              return "desktop";
            }}

            const resolvedPlatform = detectPlatform();
            const fallback = resolvedPlatform === "android" ? androidStore : iosStore;
            if (resolvedPlatform === "desktop") {{
              statusNode.textContent = "Choose your platform below. The smart link is optimized for mobile devices.";
            }} else {{
              window.location.replace(deepLink);
              window.setTimeout(() => {{
                statusNode.textContent = resolvedPlatform === "android"
                  ? "App not detected. Sending you to Google Play."
                  : "App not detected. Sending you to the App Store.";
                window.location.replace(fallback);
              }}, 900);
            }}
          </script>
        </body>
        </html>
        """
    ).strip()
    (download_root / "index.html").write_text(download_html + "\n", encoding="utf-8")

    sitemap = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"]
    sitemap.append(f"  <url><loc>{base_url}</loc></url>")
    sitemap.append(f"  <url><loc>{download_base_url}</loc></url>")
    for post in posts_data:
        sitemap.append(f"  <url><loc>{base_url}/{post['url']}</loc></url>")
        sitemap.append(f"  <url><loc>{base_url}/{post['markdown_url']}</loc></url>")
    sitemap.append("</urlset>")
    (site_root / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    robots = [
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {base_url}/sitemap.xml",
    ]
    (site_root / "robots.txt").write_text("\n".join(robots) + "\n", encoding="utf-8")

    llms_lines = [
        "Random Tactical Timer",
        "",
        "This site publishes a challenge-driven product landing page plus engineering updates.",
        "Preferred source format for agents: markdown URLs listed below.",
        "",
        f"Base URL: {base_url}",
        "",
        "Key resources:",
        f"- {base_url}",
        f"- {download_base_url}",
        f"- {base_url}/agents.md",
        f"- {base_url}/amp.json",
        f"- {base_url}/sitemap.xml",
        "",
        "Posts:",
    ]
    for post in posts_data[:100]:
        llms_lines.append(f"- {post['title']}: {base_url}/{post['markdown_url']}")
    (site_root / "llms.txt").write_text("\n".join(llms_lines) + "\n", encoding="utf-8")

    agent_lines = [
        "# Agent Index",
        "",
        "Use this page for machine-readable summaries of current content and positioning.",
        "",
        "## Conversion path",
        f"- Challenge landing page: {base_url}",
        f"- Smart install link: {download_base_url}",
        "",
        "## Agentic Merchant Protocol (AMP)",
        f"- **Approved Product Data**: [amp.json]({base_url}/amp.json) - Machine-readable, verified claims and features for AI consumption.",
        "",
        "## Intent",
        "- Product: Random Tactical Timer",
        "- Audience: combat sports athletes, tactical trainees, coaches, and reaction-drill users",
        "- Outcomes: reaction readiness, honest random cues, repeatable habit formation",
        "- Core CTA: complete 3 drills in 7 days",
        "",
        "## Latest posts",
    ]
    for post in posts_data[:20]:
        agent_lines.append(
            f"- {post['date']} | {post['title']} | html: {base_url}/{post['url']} | markdown: {base_url}/{post['markdown_url']}"
        )
    (site_root / "agents.md").write_text("\n".join(agent_lines) + "\n", encoding="utf-8")

    public_root = output_root.parent if output_root.name == "marketing" else None
    if public_root is not None:
        mirror_public_site(site_root, public_root)

    return {
        "site_root": str(site_root),
        "download_root": str(download_root),
        "post_count": len(posts_data),
        "base_url": base_url,
        "download_url": download_base_url,
        "public_root": str(public_root) if public_root is not None else "",
    }


def _post_devto(markdown: str, title: str, tags: List[str], canonical_url: str) -> Dict[str, Any]:
    requests = _requests_module()
    if requests is None:
        return {"channel": "devto", "status": "error", "reason": "missing requests dependency"}

    api_key = os.getenv("DEVTO_API_KEY", "").strip()
    if not api_key:
        return {"channel": "devto", "status": "skipped", "reason": "missing DEVTO_API_KEY"}

    payload = {
        "article": {
            "title": title,
            "published": True,
            "body_markdown": markdown,
            "tags": tags[:4],
            "canonical_url": canonical_url,
        }
    }
    response = requests.post(
        "https://dev.to/api/articles",
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if response.status_code >= 300:
        return {
            "channel": "devto",
            "status": "error",
            "code": response.status_code,
            "body": response.text[:400],
            "provider": "control_direct_api",
            "attempts": 1,
        }
    try:
        data = response.json()
    except Exception:
        return {
            "channel": "devto",
            "status": "error",
            "code": response.status_code,
            "body": response.text[:400],
            "reason": "non_json_response",
            "provider": "control_direct_api",
            "attempts": 1,
        }
    return {
        "channel": "devto",
        "status": "published",
        "id": data.get("id"),
        "url": data.get("url"),
        "provider": "control_direct_api",
        "attempts": 1,
    }


def _post_devto_retry(markdown: str, title: str, tags: List[str], canonical_url: str) -> Dict[str, Any]:
    requests = _requests_module()
    if requests is None:
        return {"channel": "devto", "status": "error", "reason": "missing requests dependency", "provider": "candidate_retry_api"}

    api_key = os.getenv("DEVTO_API_KEY", "").strip()
    if not api_key:
        return {"channel": "devto", "status": "skipped", "reason": "missing DEVTO_API_KEY", "provider": "candidate_retry_api"}

    payload = {
        "article": {
            "title": title,
            "published": True,
            "body_markdown": markdown,
            "tags": tags[:4],
            "canonical_url": canonical_url,
        }
    }
    max_attempts = max(1, int(os.getenv("AB_CANDIDATE_MAX_ATTEMPTS", "3")))
    backoff_seconds = max(1, int(os.getenv("AB_CANDIDATE_BACKOFF_SECONDS", "2")))

    last_code: Optional[int] = None
    last_body = ""
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                "https://dev.to/api/articles",
                headers={"api-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
        except Exception as exc:
            if attempt == max_attempts:
                return {
                    "channel": "devto",
                    "status": "error",
                    "reason": f"request-failed: {exc}",
                    "provider": "candidate_retry_api",
                    "attempts": attempt,
                }
            time.sleep(backoff_seconds * attempt)
            continue

        if response.status_code < 300:
            try:
                data = response.json()
            except Exception:
                return {
                    "channel": "devto",
                    "status": "error",
                    "reason": "non_json_response",
                    "code": response.status_code,
                    "body": response.text[:400],
                    "provider": "candidate_retry_api",
                    "attempts": attempt,
                }
            return {
                "channel": "devto",
                "status": "published",
                "id": data.get("id"),
                "url": data.get("url"),
                "provider": "candidate_retry_api",
                "attempts": attempt,
            }

        last_code = response.status_code
        last_body = response.text[:400]
        should_retry = response.status_code in {429, 500, 502, 503, 504}
        if not should_retry or attempt == max_attempts:
            break
        time.sleep(backoff_seconds * attempt)

    return {
        "channel": "devto",
        "status": "error",
        "code": last_code,
        "body": last_body,
        "provider": "candidate_retry_api",
        "attempts": max_attempts,
    }


def _post_linkedin(text: str, canonical_url: str) -> Dict[str, Any]:
    requests = _requests_module()
    if requests is None:
        return {"channel": "linkedin", "status": "error", "reason": "missing requests dependency"}

    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    if not token or not author_urn:
        return {
            "channel": "linkedin",
            "status": "skipped",
            "reason": "missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_URN",
        }

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": f"{text}\n\nRead more: {canonical_url}"},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=30,
    )
    if response.status_code >= 300:
        return {
            "channel": "linkedin",
            "status": "error",
            "code": response.status_code,
            "body": response.text[:400],
        }
    urn = response.headers.get("x-restli-id") or response.text.strip()
    return {"channel": "linkedin", "status": "published", "urn": urn, "url": canonical_url}


def _post_x(text: str, canonical_url: str) -> Dict[str, Any]:
    requests = _requests_module()
    if requests is None:
        return {"channel": "x", "status": "error", "reason": "missing requests dependency"}

    api_key = os.getenv("X_API_KEY", "").strip()
    api_secret = os.getenv("X_API_SECRET", "").strip()
    access_token = os.getenv("X_ACCESS_TOKEN", "").strip()
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET", "").strip()
    if not (api_key and api_secret and access_token and access_secret):
        return {
            "channel": "x",
            "status": "skipped",
            "reason": "missing X API OAuth1 credentials",
        }

    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        return {"channel": "x", "status": "error", "reason": "missing requests-oauthlib"}

    message = f"{text}\n\n{canonical_url}"
    if len(message) > 280:
        message = message[:277] + "..."

    response = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=OAuth1(api_key, api_secret, access_token, access_secret),
        json={"text": message},
        timeout=30,
    )
    if response.status_code >= 300:
        return {
            "channel": "x",
            "status": "error",
            "code": response.status_code,
            "body": response.text[:400],
        }
    try:
        data = response.json()
    except Exception:
        return {
            "channel": "x",
            "status": "error",
            "code": response.status_code,
            "body": response.text[:400],
            "reason": "non_json_response",
        }
    tweet_id = ((data.get("data") or {}).get("id"))
    return {
        "channel": "x",
        "status": "published",
        "id": tweet_id,
        "url": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else canonical_url,
    }


def campaign_from_slug(slug: str) -> str:
    prefix = slug[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", prefix):
        return f"daily_blog_{prefix.replace('-', '')}"
    return f"daily_blog_{utc_now().strftime('%Y%m%d')}"


def compose_social_post_text(title: str) -> str:
    return (
        f"{title}\n\n"
        "We shipped concrete improvements to mobile release quality, "
        "App Store readiness checks, and feedback loops."
    )


def publish_post(
    post: PostAsset,
    output_root: Path,
    dry_run: bool = False,
    devto_mode: str = "control",
) -> List[Dict[str, Any]]:
    markdown = post.markdown_path.read_text(encoding="utf-8")
    base_url = resolve_blog_base_url(output_root)
    canonical_url = f"{base_url}/posts/{post.slug}.html"
    campaign = campaign_from_slug(post.slug)
    linkedin_url = add_utm(canonical_url, "linkedin", campaign, medium="organic", content=post.slug)
    x_url = add_utm(canonical_url, "x", campaign, medium="organic", content=post.slug)
    devto_markdown = prepare_devto_markdown(markdown, post.slug, base_url)

    short_text = compose_social_post_text(post.title)

    if dry_run:
        results = [
            {"channel": "devto", "status": "dry_run", "url": canonical_url, "provider": f"{devto_mode}_dry_run"},
            {"channel": "linkedin", "status": "dry_run", "url": linkedin_url},
            {"channel": "x", "status": "dry_run", "url": x_url},
        ]
    else:
        if devto_mode == "candidate":
            devto_result = _post_devto_retry(devto_markdown, post.title, post.tags, canonical_url)
        else:
            devto_result = _post_devto(devto_markdown, post.title, post.tags, canonical_url)
        results = [
            devto_result,
            _post_linkedin(short_text, linkedin_url),
            _post_x(short_text, x_url),
        ]

    pub_log = output_root / "data" / "publications.jsonl"
    for item in results:
        append_jsonl(
            pub_log,
            {
                "timestamp": iso_timestamp(),
                "slug": post.slug,
                "devto_mode": devto_mode,
                **item,
            },
        )
    return results


def _arm_counts(rows: List[Dict[str, Any]]) -> Tuple[int, int]:
    control = sum(1 for row in rows if str(row.get("arm")) == "control")
    candidate = sum(1 for row in rows if str(row.get("arm")) == "candidate")
    return control, candidate


def choose_ab_arm(existing_rows: List[Dict[str, Any]], window_days: int = AB_PILOT_WINDOW_DAYS) -> Optional[str]:
    if len(existing_rows) >= window_days:
        return None
    control, candidate = _arm_counts(existing_rows)
    return "control" if control <= candidate else "candidate"


def _safe_float_env(name: str, default: float = 0.0) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _pilot_window_rows(rows: List[Dict[str, Any]], window_days: int = AB_PILOT_WINDOW_DAYS) -> List[Dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: str(row.get("timestamp") or ""))
    return ordered[-window_days:]


def summarize_ab_pilot(rows: List[Dict[str, Any]], window_days: int = AB_PILOT_WINDOW_DAYS) -> Dict[str, Any]:
    window = _pilot_window_rows(rows, window_days=window_days)
    budget_cap_usd = _safe_float_env("AB_PILOT_MAX_COST_USD", 10.0)
    budget_spent_usd = round(sum(float(item.get("estimated_cost_usd") or 0.0) for item in window), 6)
    grouped: Dict[str, List[Dict[str, Any]]] = {"control": [], "candidate": []}
    for row in window:
        arm = str(row.get("arm") or "")
        if arm in grouped:
            grouped[arm].append(row)

    summary: Dict[str, Any] = {
        "window_days": window_days,
        "total_runs": len(window),
        "budget_cap_usd": budget_cap_usd,
        "budget_spent_usd": budget_spent_usd,
        "budget_remaining_usd": round(max(0.0, budget_cap_usd - budget_spent_usd), 6),
        "arms": {},
        "decision": "insufficient_data",
    }
    for arm, items in grouped.items():
        runs = len(items)
        successes = sum(1 for item in items if bool(item.get("success")))
        mean_ms = (
            round(sum(float(item.get("duration_ms") or 0) for item in items) / runs, 2)
            if runs
            else None
        )
        total_cost = round(sum(float(item.get("estimated_cost_usd") or 0) for item in items), 6)
        cost_per_success = round(total_cost / successes, 6) if successes else None
        summary["arms"][arm] = {
            "runs": runs,
            "successes": successes,
            "success_rate": round(successes / runs, 4) if runs else None,
            "mean_duration_ms": mean_ms,
            "total_cost_usd": total_cost,
            "cost_per_success_usd": cost_per_success,
        }

    control = summary["arms"]["control"]
    candidate = summary["arms"]["candidate"]
    complete = summary["total_runs"] >= window_days and control["runs"] > 0 and candidate["runs"] > 0
    summary["complete"] = complete

    if complete:
        if control["successes"] == 0 and candidate["successes"] > 0:
            summary["decision"] = "candidate_keep"
        elif candidate["successes"] == 0:
            summary["decision"] = "control_keep"
        else:
            candidate_beats = (
                (candidate["success_rate"] or 0) > (control["success_rate"] or 0)
                and (candidate["mean_duration_ms"] or float("inf")) < (control["mean_duration_ms"] or float("inf"))
                and (candidate["cost_per_success_usd"] or float("inf")) < (control["cost_per_success_usd"] or float("inf"))
            )
            summary["decision"] = "candidate_keep" if candidate_beats else "control_keep"

    return summary


def write_ab_pilot_report(output_root: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# DEV.to Publish A/B Pilot",
        "",
        f"Timestamp: {iso_timestamp()}",
        f"Window size: {summary.get('window_days')} runs",
        f"Runs collected: {summary.get('total_runs')}",
        f"Budget cap (USD): {summary.get('budget_cap_usd')}",
        f"Budget spent (USD): {summary.get('budget_spent_usd')}",
        f"Budget remaining (USD): {summary.get('budget_remaining_usd')}",
        f"Complete: {summary.get('complete')}",
        f"Decision: {summary.get('decision')}",
        "",
        "| Arm | Runs | Successes | Success Rate | Mean Duration (ms) | Cost/Success (USD) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ("control", "candidate"):
        stats = summary.get("arms", {}).get(arm, {})
        lines.append(
            f"| {arm} | {stats.get('runs', 0)} | {stats.get('successes', 0)} | "
            f"{stats.get('success_rate')} | {stats.get('mean_duration_ms')} | {stats.get('cost_per_success_usd')} |"
        )
    lines.append("")
    lines.append("Rule: Candidate is kept only if it beats control on all three metrics.")
    report = "\n".join(lines) + "\n"
    (output_root / "data" / "publish_ab_pilot_report.md").write_text(report, encoding="utf-8")


def run_publish_ab_pilot(post: PostAsset, output_root: Path, dry_run: bool = False) -> Dict[str, Any]:
    pilot_log = output_root / "data" / "publish_ab_pilot_runs.jsonl"
    existing_rows = read_jsonl(pilot_log)
    summary_before = summarize_ab_pilot(existing_rows, AB_PILOT_WINDOW_DAYS)

    selected_arm = choose_ab_arm(existing_rows, AB_PILOT_WINDOW_DAYS)
    if selected_arm is None:
        if summary_before.get("decision") == "candidate_keep":
            selected_arm = "candidate"
        else:
            selected_arm = "control"

    budget_cap_usd = _safe_float_env("AB_PILOT_MAX_COST_USD", 10.0)
    spent_before = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in existing_rows), 6)
    control_cost = _safe_float_env("AB_CONTROL_COST_USD", 0.0)
    candidate_cost = _safe_float_env("AB_CANDIDATE_COST_USD", 0.0)
    projected_cost = candidate_cost if selected_arm == "candidate" else control_cost

    budget_adjustment: Optional[str] = None
    if spent_before + projected_cost > budget_cap_usd:
        options = [("control", control_cost), ("candidate", candidate_cost)]
        affordable = [(arm, cost) for arm, cost in sorted(options, key=lambda item: item[1]) if spent_before + cost <= budget_cap_usd]
        if affordable:
            selected_arm = affordable[0][0]
            projected_cost = affordable[0][1]
            budget_adjustment = f"fallback_to_{selected_arm}"
        else:
            budget_adjustment = "cap_exhausted"

    devto_mode = "candidate" if selected_arm == "candidate" else "control"
    if budget_adjustment == "cap_exhausted":
        publish_results = [
            {
                "channel": "devto",
                "status": "skipped",
                "reason": "ab_pilot_budget_cap_exhausted",
                "provider": "none",
            },
            {"channel": "linkedin", "status": "skipped", "reason": "not-run"},
            {"channel": "x", "status": "skipped", "reason": "not-run"},
        ]
        duration_ms = 0
    else:
        started = time.perf_counter()
        publish_results = publish_post(post, output_root, dry_run=dry_run, devto_mode=devto_mode)
        duration_ms = int((time.perf_counter() - started) * 1000)

    devto_result = next((row for row in publish_results if row.get("channel") == "devto"), {"status": "error"})
    success = str(devto_result.get("status")) == "published" or str(devto_result.get("status")) == "dry_run"
    cost = projected_cost if budget_adjustment != "cap_exhausted" else 0.0

    row = {
        "timestamp": iso_timestamp(),
        "workflow": "devto_publish",
        "arm": selected_arm,
        "provider": str(devto_result.get("provider") or devto_mode),
        "status": str(devto_result.get("status") or "unknown"),
        "success": success,
        "duration_ms": duration_ms,
        "estimated_cost_usd": round(cost, 6),
        "slug": post.slug,
        "budget_cap_usd": budget_cap_usd,
        "budget_spent_before_usd": spent_before,
        "budget_adjustment": budget_adjustment,
    }
    append_jsonl(pilot_log, row)

    refreshed_rows = read_jsonl(pilot_log)
    summary_after = summarize_ab_pilot(refreshed_rows, AB_PILOT_WINDOW_DAYS)
    spent_after = round(sum(float(item.get("estimated_cost_usd") or 0.0) for item in refreshed_rows), 6)
    summary_after["budget_cap_usd"] = budget_cap_usd
    summary_after["budget_spent_usd"] = spent_after
    summary_after["budget_remaining_usd"] = round(max(0.0, budget_cap_usd - spent_after), 6)
    (output_root / "data" / "publish_ab_pilot_summary.json").write_text(
        json.dumps(summary_after, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_ab_pilot_report(output_root, summary_after)

    return {
        "selected_arm": selected_arm,
        "devto_mode": devto_mode,
        "run": row,
        "summary": summary_after,
        "results": publish_results,
    }


def collect_engagement(output_root: Path, days: int = 14) -> Dict[str, Any]:
    requests = _requests_module()
    publications = read_jsonl(output_root / "data" / "publications.jsonl")
    cutoff = utc_now() - dt.timedelta(days=days)

    def within_days(row: Dict[str, Any]) -> bool:
        raw = str(row.get("timestamp") or "")
        try:
            stamp = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return False
        return stamp >= cutoff

    recent = [row for row in publications if within_days(row)]

    summary: Dict[str, Any] = {
        "timestamp": iso_timestamp(),
        "window_days": days,
        "channels": {},
    }

    devto_key = os.getenv("DEVTO_API_KEY", "").strip()
    x_bearer = os.getenv("X_BEARER_TOKEN", "").strip()

    for row in recent:
        channel = str(row.get("channel") or "unknown")
        status = str(row.get("status") or "unknown")
        channel_bucket = summary["channels"].setdefault(channel, {"published": 0, "engagement": 0, "items": 0})
        channel_bucket["items"] += 1
        if status == "published":
            channel_bucket["published"] += 1

    for row in recent:
        if (
            requests is not None
            and row.get("channel") == "devto"
            and row.get("status") == "published"
            and row.get("id")
            and devto_key
        ):
            rid = _safe_numeric_id(row["id"])
            if not rid:
                continue
            response = requests.get(
                f"https://dev.to/api/articles/{rid}",
                headers={"api-key": devto_key},
                timeout=30,
            )
            if response.status_code < 300:
                try:
                    data = response.json()
                except Exception:
                    data = {}
                score = int(data.get("positive_reactions_count") or 0) + int(data.get("comments_count") or 0)
                summary["channels"].setdefault("devto", {"published": 0, "engagement": 0, "items": 0})["engagement"] += score

        if (
            requests is not None
            and row.get("channel") == "x"
            and row.get("status") == "published"
            and row.get("id")
            and x_bearer
        ):
            rid = _safe_tweet_id(row["id"])
            if not rid:
                continue
            response = requests.get(
                f"https://api.twitter.com/2/tweets/{rid}",
                params={"tweet.fields": "public_metrics"},
                headers={"Authorization": f"Bearer {x_bearer}"},
                timeout=30,
            )
            if response.status_code < 300:
                try:
                    payload = response.json()
                except Exception:
                    payload = {}
                metrics = ((payload.get("data") or {}).get("public_metrics") or {})
                score = int(metrics.get("like_count") or 0) + int(metrics.get("retweet_count") or 0)
                summary["channels"].setdefault("x", {"published": 0, "engagement": 0, "items": 0})["engagement"] += score

    append_jsonl(output_root / "data" / "engagement.jsonl", summary)

    lines = [
        "# Daily Growth Engagement Report",
        "",
        f"Timestamp: {summary['timestamp']}",
        f"Window: last {days} days",
        "",
        "| Channel | Published | Items | Engagement Score |",
        "|---|---:|---:|---:|",
    ]
    for channel, stats in sorted(summary["channels"].items()):
        lines.append(
            f"| {channel} | {stats.get('published', 0)} | {stats.get('items', 0)} | {stats.get('engagement', 0)} |"
        )

    report_md = "\n".join(lines) + "\n"
    report_path = output_root / "data" / "engagement-latest.md"
    report_path.write_text(report_md, encoding="utf-8")

    bot_log_path = Path(os.getenv("AI_BOT_LOG_PATH", str(output_root / "data" / "access-log.ndjson"))).resolve()
    bot_report = bot_analytics.run(bot_log_path, output_root / "data")
    summary["bot_traffic"] = {
        "status": bot_report.get("status"),
        "input_rows": bot_report.get("input_rows"),
    }

    summary_file = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if summary_file:
        with Path(summary_file).open("a", encoding="utf-8") as handle:
            handle.write(report_md)
            handle.write("\n")
            handle.write("## AI Bot Traffic\n")
            handle.write(f"- Status: {summary['bot_traffic']['status']}\n")
            handle.write(f"- Input rows: {summary['bot_traffic']['input_rows']}\n")

    return summary


def generate_post(args: argparse.Namespace) -> PostAsset:
    output_root = Path(args.output_root).resolve()
    repo_root = Path(args.repo_root).resolve()

    ensure_dir(output_root / "posts")
    ensure_dir(output_root / "diagrams")
    ensure_dir(output_root / "data")

    posts_log = read_jsonl(output_root / "data" / "posts.jsonl")
    first_post = len(posts_log) == 0
    inspiration_url = ""
    primary_keyword = ""
    keyword_intent = ""
    today = utc_now().date()

    if args.topic:
        chosen_topic = args.topic
    elif first_post:
        chosen_topic = FIRST_POST_TOPIC
        inspiration_url = FIRST_POST_SOURCE
    else:
        keyword_pick = choose_keyword_topic(output_root, today)
        if keyword_pick and keyword_pick.get("title"):
            chosen_topic = str(keyword_pick["title"])
            primary_keyword = str(keyword_pick.get("keyword") or "")
            keyword_intent = str(keyword_pick.get("intent") or "")
        else:
            chosen_topic = topic_for_day(DEFAULT_TOPICS, today)

    commits = run_git_log(repo_root, since_days=args.since_days, max_commits=args.max_commits)
    title, description, body = build_post_copy(
        chosen_topic,
        commits,
        inspiration_url=inspiration_url,
        primary_keyword=primary_keyword,
        keyword_intent=keyword_intent,
    )

    post = write_post(
        output_root=output_root,
        title=title,
        description=description,
        body=body,
        tags=list(DEFAULT_TAGS),
        app_store_url=app_store_url(),
        play_store_url=play_store_url(),
        ios_review_url=ios_review_url(),
        android_review_url=android_review_url(),
    )

    append_jsonl(
        output_root / "data" / "posts.jsonl",
        {
            "timestamp": post.created_at,
            "slug": post.slug,
            "title": post.title,
            "description": post.description,
            "primary_keyword": primary_keyword,
            "keyword_intent": keyword_intent,
            "markdown_path": str(post.markdown_path),
            "diagram_svg_path": str(post.diagram_svg_path),
        },
    )

    print(json.dumps({"status": "generated", "slug": post.slug, "markdown": str(post.markdown_path)}, indent=2))
    return post


def latest_post_asset(output_root: Path) -> PostAsset:
    posts = sorted((output_root / "posts").glob("*.md"), reverse=True)
    if not posts:
        raise SystemExit("No posts found. Run generate first.")
    md = posts[0]
    raw = md.read_text(encoding="utf-8")
    fm, _ = parse_frontmatter(raw)
    slug = md.stem
    return PostAsset(
        slug=slug,
        title=fm.get("title", slug),
        description=fm.get("description", ""),
        created_at=fm.get("date", ""),
        markdown_path=md,
        diagram_svg_path=output_root / "diagrams" / f"{slug}.svg",
        diagram_mermaid_path=output_root / "diagrams" / f"{slug}.mmd",
        html_path=output_root / "site" / "posts" / f"{slug}.html",
        tags=[t.strip() for t in (fm.get("tags", "[ai,mobile]").strip("[]").split(",")) if t.strip()],
    )


def run_daily(args: argparse.Namespace) -> int:
    output_root = Path(args.output_root).resolve()
    keyword_payload = ensure_keyword_backlog(output_root)
    post = generate_post(args)
    site = build_site(output_root)
    pilot_payload: Optional[Dict[str, Any]] = None
    if getattr(args, "ab_pilot", False):
        pilot_payload = run_publish_ab_pilot(post, output_root, dry_run=args.dry_run)
        publish_results = list(pilot_payload.get("results") or [])
    else:
        publish_results = publish_post(post, output_root, dry_run=args.dry_run)
    engagement = collect_engagement(output_root, days=args.engagement_days)

    payload = {
        "status": "ok",
        "keywords": keyword_payload,
        "post": post.slug,
        "site": site,
        "publish": publish_results,
        "ab_pilot": pilot_payload,
        "engagement": engagement,
    }
    print(json.dumps(payload, indent=2))
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily growth content automation")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-root", default="marketing")

    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Generate daily post + diagram")
    p_gen.add_argument("--topic", default="")
    p_gen.add_argument("--since-days", type=int, default=2)
    p_gen.add_argument("--max-commits", type=int, default=8)

    p_publish = sub.add_parser("publish", help="Publish latest post to channels")
    p_publish.add_argument("--dry-run", action="store_true")

    sub.add_parser("build-site", help="Build GitHub Pages site")

    p_collect = sub.add_parser("collect", help="Collect engagement metrics")
    p_collect.add_argument("--engagement-days", type=int, default=14)

    sub.add_parser("keyword-plan", help="Generate keyword backlog using BID/AI-trap/tool heuristics")

    p_bot = sub.add_parser("bot-analyze", help="Classify and summarize AI crawler traffic from access logs")
    p_bot.add_argument("--bot-log", default="", help="Override path to NDJSON access log")

    p_daily = sub.add_parser("run-daily", help="Generate, build, publish, and collect")
    p_daily.add_argument("--topic", default="")
    p_daily.add_argument("--since-days", type=int, default=2)
    p_daily.add_argument("--max-commits", type=int, default=8)
    p_daily.add_argument("--engagement-days", type=int, default=14)
    p_daily.add_argument("--dry-run", action="store_true")
    p_daily.add_argument("--ab-pilot", action="store_true", help="Run 14-run DEV.to publish A/B pilot")

    p_pilot = sub.add_parser("pilot-report", help="Summarize 14-run DEV.to publish A/B pilot")
    p_pilot.add_argument("--window-days", type=int, default=AB_PILOT_WINDOW_DAYS)

    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()

    if args.command == "generate":
        generate_post(args)
        return 0

    if args.command == "publish":
        post = latest_post_asset(output_root)
        results = publish_post(post, output_root, dry_run=args.dry_run)
        print(json.dumps(results, indent=2))
        return 0

    if args.command == "build-site":
        results = build_site(output_root)
        print(json.dumps(results, indent=2))
        return 0

    if args.command == "collect":
        results = collect_engagement(output_root, days=args.engagement_days)
        print(json.dumps(results, indent=2))
        return 0

    if args.command == "keyword-plan":
        results = ensure_keyword_backlog(output_root)
        print(json.dumps(results, indent=2))
        return 0

    if args.command == "bot-analyze":
        default_log = output_root / "data" / "access-log.ndjson"
        log_path = Path(args.bot_log).resolve() if args.bot_log else default_log
        results = bot_analytics.run(log_path, output_root / "data")
        print(json.dumps(results, indent=2))
        return 0

    if args.command == "run-daily":
        return run_daily(args)

    if args.command == "pilot-report":
        rows = read_jsonl(output_root / "data" / "publish_ab_pilot_runs.jsonl")
        summary = summarize_ab_pilot(rows, window_days=args.window_days)
        (output_root / "data" / "publish_ab_pilot_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_ab_pilot_report(output_root, summary)
        print(json.dumps(summary, indent=2))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
