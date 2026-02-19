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
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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


def build_post_copy(topic: str, recent_commits: List[str], inspiration_url: str = "") -> Tuple[str, str, str]:
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

    width = 1240
    height = 250
    node_w = 170
    node_h = 68
    x_gap = 26
    start_x = 28
    y = 84

    pos: Dict[str, Tuple[int, int]] = {}
    for idx, node in enumerate(nodes):
        x = start_x + idx * (node_w + x_gap)
        pos[node["id"]] = (x, y)

    lines: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        "<linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">",
        "<stop offset=\"0%\" stop-color=\"#0A1A2F\"/>",
        "<stop offset=\"100%\" stop-color=\"#13284A\"/>",
        "</linearGradient>",
        "<linearGradient id=\"node\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">",
        "<stop offset=\"0%\" stop-color=\"#F2F7FF\"/>",
        "<stop offset=\"100%\" stop-color=\"#DCEAFF\"/>",
        "</linearGradient>",
        "<marker id=\"arrow\" markerWidth=\"10\" markerHeight=\"7\" refX=\"9\" refY=\"3.5\" orient=\"auto\">",
        "<polygon points=\"0 0, 10 3.5, 0 7\" fill=\"#8EC5FF\"/>",
        "</marker>",
        "</defs>",
        "<rect x=\"0\" y=\"0\" width=\"1240\" height=\"250\" fill=\"url(#bg)\" rx=\"16\"/>",
        "<text x=\"28\" y=\"38\" font-family=\"-apple-system,BlinkMacSystemFont,Segoe UI,Arial\" font-size=\"24\" font-weight=\"700\" fill=\"#ffffff\">PaperBanana Tech Flow</text>",
        "<text x=\"28\" y=\"60\" font-family=\"-apple-system,BlinkMacSystemFont,Segoe UI,Arial\" font-size=\"13\" fill=\"#CFE5FF\">Daily content automation: from idea to publish to measurable feedback</text>",
    ]

    for src, dst in edges:
        sx, sy = pos[src]
        dx, dy = pos[dst]
        x1 = sx + node_w
        y1 = sy + node_h // 2
        x2 = dx
        y2 = dy + node_h // 2
        lines.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#8EC5FF" stroke-width="3" marker-end="url(#arrow)"/>'
        )

    for node in nodes:
        x, y = pos[node["id"]]
        label = html.escape(node["label"])
        lines.extend(
            [
                f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" rx="12" fill="url(#node)" stroke="#8EC5FF" stroke-width="2"/>',
                f'<text x="{x + node_w / 2}" y="{y + 40}" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial" font-size="16" font-weight="600" fill="#0E2746">{label}</text>',
            ]
        )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def render_paperbanana_mermaid(spec: Dict[str, Any], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    nodes = "\n".join(f'  {n["id"]}["{n["label"]}"]' for n in spec["nodes"])
    edges = "\n".join(f"  {s} --> {d}" for s, d in spec["edges"])
    content = "flowchart LR\n" + nodes + "\n" + edges + "\n"
    output_path.write_text(content, encoding="utf-8")


def add_utm(url: str, source: str, campaign: str, medium: str = "organic") -> str:
    sep = "&" if "?" in url else "?"
    return (
        f"{url}{sep}utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"
        "&utm_content=daily_blog"
    )


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
    blog_ios = add_utm(app_store_url, "github_pages", campaign)
    blog_android = add_utm(play_store_url, "github_pages", campaign)
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


def build_site(output_root: Path) -> Dict[str, Any]:
    site_root = output_root / "site"
    posts_src = output_root / "posts"
    diagrams_src = output_root / "diagrams"
    posts_out = site_root / "posts"
    diagrams_out = site_root / "diagrams"

    ensure_dir(site_root)
    ensure_dir(posts_out)
    ensure_dir(diagrams_out)

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
        post_html = textwrap.dedent(
            f"""
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>{html.escape(title)} | Random Tactical Timer Blog</title>
              <meta name="description" content="{html.escape(description)}" />
              <link rel="stylesheet" href="../styles.css" />
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
            }
        )

    style = textwrap.dedent(
        """
        :root {
          --bg: #071426;
          --surface: #102946;
          --text: #f4f8ff;
          --muted: #b6cbea;
          --accent: #5bd2ff;
        }
        body {
          margin: 0;
          font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
          background: radial-gradient(circle at 20% -20%, #173e67 0%, #071426 55%);
          color: var(--text);
          min-height: 100vh;
          line-height: 1.6;
        }
        .container { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
        h1 { line-height: 1.2; }
        a { color: var(--accent); text-decoration: none; }
        a:hover { text-decoration: underline; }
        .post-card {
          background: rgba(16, 41, 70, 0.82);
          border: 1px solid rgba(91, 210, 255, 0.26);
          border-radius: 14px;
          padding: 16px;
          margin: 14px 0;
        }
        .meta { color: var(--muted); font-size: 0.95rem; }
        .back { display: inline-block; margin-bottom: 18px; }
        img { max-width: 100%; border-radius: 10px; }
        """
    ).strip()
    (site_root / "styles.css").write_text(style + "\n", encoding="utf-8")

    listing = []
    for post in posts_data:
        listing.append(
            f"<article class=\"post-card\"><h2><a href=\"{post['url']}\">{html.escape(post['title'])}</a></h2>"
            f"<p class=\"meta\">{html.escape(post['date'])}</p>"
            f"<p>{html.escape(post['description'])}</p></article>"
        )

    index_html = textwrap.dedent(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>Random Tactical Timer Engineering Blog</title>
          <meta name="description" content="Daily engineering posts about AI-assisted app development, automation, testing, and release quality." />
          <link rel="stylesheet" href="styles.css" />
          {analytics_block}
        </head>
        <body>
          <main class="container">
            <h1>Random Tactical Timer Engineering Blog</h1>
            <p>Daily short posts on AI-assisted mobile engineering, release automation, and quality feedback loops.</p>
            {''.join(listing)}
          </main>
        </body>
        </html>
        """
    ).strip()
    (site_root / "index.html").write_text(index_html + "\n", encoding="utf-8")

    sitemap = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"]
    base_url = os.getenv("BLOG_BASE_URL", "https://igorganapolsky.github.io/Random-Timer/").rstrip("/")
    sitemap.append(f"  <url><loc>{base_url}/index.html</loc></url>")
    for post in posts_data:
        sitemap.append(f"  <url><loc>{base_url}/{post['url']}</loc></url>")
    sitemap.append("</urlset>")
    (site_root / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    return {"site_root": str(site_root), "post_count": len(posts_data), "base_url": base_url}


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
        }
    data = response.json()
    return {
        "channel": "devto",
        "status": "published",
        "id": data.get("id"),
        "url": data.get("url"),
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
    data = response.json()
    tweet_id = ((data.get("data") or {}).get("id"))
    return {
        "channel": "x",
        "status": "published",
        "id": tweet_id,
        "url": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else canonical_url,
    }


def publish_post(post: PostAsset, output_root: Path, dry_run: bool = False) -> List[Dict[str, Any]]:
    markdown = post.markdown_path.read_text(encoding="utf-8")
    base_url = os.getenv("BLOG_BASE_URL", "https://igorganapolsky.github.io/Random-Timer/").rstrip("/")
    canonical_url = f"{base_url}/posts/{post.slug}.html"

    short_text = (
        f"New build log: {post.title}. We share how AI + automation improved release quality and review outcomes."
    )

    if dry_run:
        results = [
            {"channel": "devto", "status": "dry_run", "url": canonical_url},
            {"channel": "linkedin", "status": "dry_run", "url": canonical_url},
            {"channel": "x", "status": "dry_run", "url": canonical_url},
        ]
    else:
        results = [
            _post_devto(markdown, post.title, post.tags, canonical_url),
            _post_linkedin(short_text, canonical_url),
            _post_x(short_text, canonical_url),
        ]

    pub_log = output_root / "data" / "publications.jsonl"
    for item in results:
        append_jsonl(
            pub_log,
            {
                "timestamp": iso_timestamp(),
                "slug": post.slug,
                **item,
            },
        )
    return results


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
                timeout=20,
            )
            if response.status_code < 300:
                data = response.json()
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
                timeout=20,
            )
            if response.status_code < 300:
                metrics = ((response.json().get("data") or {}).get("public_metrics") or {})
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

    summary_file = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if summary_file:
        with Path(summary_file).open("a", encoding="utf-8") as handle:
            handle.write(report_md)

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

    if args.topic:
        chosen_topic = args.topic
    elif first_post:
        chosen_topic = FIRST_POST_TOPIC
        inspiration_url = FIRST_POST_SOURCE
    else:
        chosen_topic = topic_for_day(DEFAULT_TOPICS, utc_now().date())

    commits = run_git_log(repo_root, since_days=args.since_days, max_commits=args.max_commits)
    title, description, body = build_post_copy(chosen_topic, commits, inspiration_url=inspiration_url)

    app_store_url = os.getenv(
        "APP_STORE_URL",
        "https://apps.apple.com/us/app/random-tactical-timer/id6742267714",
    )
    play_store_url = os.getenv(
        "PLAY_STORE_URL",
        "https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer",
    )
    ios_review_url = os.getenv(
        "IOS_REVIEW_URL",
        "https://apps.apple.com/us/app/random-tactical-timer/id6742267714?action=write-review",
    )
    android_review_url = os.getenv(
        "ANDROID_REVIEW_URL",
        "https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer&reviewId=0",
    )

    post = write_post(
        output_root=output_root,
        title=title,
        description=description,
        body=body,
        tags=list(DEFAULT_TAGS),
        app_store_url=app_store_url,
        play_store_url=play_store_url,
        ios_review_url=ios_review_url,
        android_review_url=android_review_url,
    )

    append_jsonl(
        output_root / "data" / "posts.jsonl",
        {
            "timestamp": post.created_at,
            "slug": post.slug,
            "title": post.title,
            "description": post.description,
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
    post = generate_post(args)
    site = build_site(output_root)
    publish_results = publish_post(post, output_root, dry_run=args.dry_run)
    engagement = collect_engagement(output_root, days=args.engagement_days)

    payload = {
        "status": "ok",
        "post": post.slug,
        "site": site,
        "publish": publish_results,
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

    p_daily = sub.add_parser("run-daily", help="Generate, build, publish, and collect")
    p_daily.add_argument("--topic", default="")
    p_daily.add_argument("--since-days", type=int, default=2)
    p_daily.add_argument("--max-commits", type=int, default=8)
    p_daily.add_argument("--engagement-days", type=int, default=14)
    p_daily.add_argument("--dry-run", action="store_true")

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

    if args.command == "run-daily":
        return run_daily(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
