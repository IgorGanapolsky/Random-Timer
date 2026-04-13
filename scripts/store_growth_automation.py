#!/usr/bin/env python3
"""Build persona-specific store-growth artifacts and SEO landing pages."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
DEFAULT_PERSONAS = REPO_ROOT / "marketing" / "store_growth" / "personas.json"
GENERATED_DIR = REPO_ROOT / "marketing" / "store_growth" / "generated"
SITE_AUDIENCES_DIR = REPO_ROOT / "marketing" / "site" / "audiences"
ATTRIBUTION_PATH = REPO_ROOT / "marketing" / "data" / "store_growth_attribution.json"
DEEP_LINK_BASE = "https://igorganapolsky.github.io/Random-Timer/download"

PLAY_CUSTOM_LISTING_LIMIT = 50
APPLE_CUSTOM_PRODUCT_PAGE_LIMIT = 70
PLAY_SHORT_DESCRIPTION_MAX = 80
PLAY_FULL_DESCRIPTION_MAX = 4000
APPLE_PROMOTIONAL_TEXT_MAX = 170
APPLE_KEYWORDS_MAX = 100


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _slug_url(slug: str) -> str:
    return f"https://igorganapolsky.github.io/Random-Timer/marketing/site/audiences/{slug}/"


def _download_url(platform: str, persona: dict[str, Any], source: str) -> str:
    params = {
        "platform": platform,
        "utm_source": source,
        "utm_medium": "organic",
        "utm_campaign": persona["utm"]["campaign"],
        "utm_content": persona["utm"]["content"],
    }
    return f"{DEEP_LINK_BASE}?{urlencode(params)}"


def validate_personas(payload: dict[str, Any]) -> list[str]:
    personas = payload.get("personas", [])
    errors: list[str] = []
    if not isinstance(personas, list) or not personas:
        return ["personas must be a non-empty list"]
    if len(personas) > PLAY_CUSTOM_LISTING_LIMIT:
        errors.append(f"Google Play custom listing count {len(personas)} exceeds {PLAY_CUSTOM_LISTING_LIMIT}")
    if len(personas) > APPLE_CUSTOM_PRODUCT_PAGE_LIMIT:
        errors.append(f"Apple Custom Product Page count {len(personas)} exceeds {APPLE_CUSTOM_PRODUCT_PAGE_LIMIT}")

    seen: set[str] = set()
    for persona in personas:
        slug = str(persona.get("slug") or "")
        if not slug:
            errors.append("persona missing slug")
            continue
        if slug in seen:
            errors.append(f"duplicate persona slug: {slug}")
        seen.add(slug)

        google = persona.get("google", {})
        apple = persona.get("apple", {})
        if len(str(google.get("short_description") or "")) > PLAY_SHORT_DESCRIPTION_MAX:
            errors.append(f"{slug} Google short_description exceeds {PLAY_SHORT_DESCRIPTION_MAX}")
        if len(str(google.get("full_description") or "")) > PLAY_FULL_DESCRIPTION_MAX:
            errors.append(f"{slug} Google full_description exceeds {PLAY_FULL_DESCRIPTION_MAX}")
        if len(str(apple.get("promotional_text") or "")) > APPLE_PROMOTIONAL_TEXT_MAX:
            errors.append(f"{slug} Apple promotional_text exceeds {APPLE_PROMOTIONAL_TEXT_MAX}")
        if len(str(apple.get("keywords") or "")) > APPLE_KEYWORDS_MAX:
            errors.append(f"{slug} Apple keywords exceeds {APPLE_KEYWORDS_MAX}")
        if not persona.get("primary_keywords"):
            errors.append(f"{slug} needs primary_keywords")
        if not persona.get("content", {}).get("article_topics"):
            errors.append(f"{slug} needs content.article_topics")
    return errors


def _google_listing(persona: dict[str, Any]) -> dict[str, Any]:
    google = persona["google"]
    return {
        "persona": persona["slug"],
        "custom_listing_name": google["custom_listing_name"],
        "language": "en-US",
        "short_description": google["short_description"],
        "full_description": google["full_description"],
        "targeting_note": google["targeting_note"],
        "landing_page": _slug_url(persona["slug"]),
        "android_download_url": _download_url("android", persona, "google_play_custom_listing"),
        "keywords": persona["primary_keywords"],
    }


def _apple_page(persona: dict[str, Any]) -> dict[str, Any]:
    apple = persona["apple"]
    return {
        "persona": persona["slug"],
        "custom_product_page_name": apple["custom_product_page_name"],
        "campaign_token": apple["campaign_token"],
        "language": "en-US",
        "promotional_text": apple["promotional_text"],
        "keywords": apple["keywords"],
        "screenshot_story": apple["screenshot_story"],
        "landing_page": _slug_url(persona["slug"]),
        "ios_download_url": _download_url("ios", persona, "apple_custom_product_page"),
    }


def _content_calendar(personas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, persona in enumerate(personas):
        for topic_index, topic in enumerate(persona["content"]["article_topics"]):
            rows.append(
                {
                    "slot": index + topic_index * len(personas),
                    "persona": persona["slug"],
                    "topic": topic,
                    "utm_campaign": persona["utm"]["campaign"],
                    "utm_content": persona["utm"]["content"],
                    "communities": persona["content"]["communities"],
                    "zernio_angles": persona["content"]["zernio_angles"],
                }
            )
    return rows


def build_plan(payload: dict[str, Any], generated_at: str) -> dict[str, Any]:
    personas = payload["personas"]
    google_listings = [_google_listing(persona) for persona in personas]
    apple_pages = [_apple_page(persona) for persona in personas]
    calendar = _content_calendar(personas)
    attribution = {
        "generated_at": generated_at,
        "north_star": payload["north_star"],
        "monthly_external_spend_cap_usd": payload["budget_policy"]["monthly_external_spend_cap_usd"],
        "tracking_rule": "Measure WQTU, paywall_viewed, paywall_purchase_success, and UTM source/page rows by persona campaign.",
        "personas": [
            {
                "slug": persona["slug"],
                "campaign": persona["utm"]["campaign"],
                "content": persona["utm"]["content"],
                "landing_page": _slug_url(persona["slug"]),
                "ios_download_url": _download_url("ios", persona, "audience_page"),
                "android_download_url": _download_url("android", persona, "audience_page"),
            }
            for persona in personas
        ],
    }
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "budget_policy": payload["budget_policy"],
        "references": payload["references"],
        "counts": {
            "personas": len(personas),
            "google_custom_store_listings": len(google_listings),
            "apple_custom_product_pages": len(apple_pages),
            "content_topics": len(calendar),
        },
        "google_custom_store_listings": google_listings,
        "apple_custom_product_pages": apple_pages,
        "content_calendar": calendar,
        "attribution": attribution,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_audience_page(persona: dict[str, Any]) -> str:
    title = f"Random Tactical Timer for {persona['display_name']}"
    keywords = ", ".join(persona["primary_keywords"])
    ios_url = _download_url("ios", persona, "audience_page")
    android_url = _download_url("android", persona, "audience_page")
    topics = "".join(f"<li>{html.escape(topic)}</li>" for topic in persona["content"]["article_topics"])
    communities = "".join(f"<li>{html.escape(item)}</li>" for item in persona["content"]["communities"])
    structured = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Random Tactical Timer",
        "applicationCategory": "HealthApplication",
        "operatingSystem": "iOS, Android",
        "audience": persona["audience"],
        "description": persona["positioning"],
        "url": _slug_url(persona["slug"]),
    }
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(persona['positioning'])}" />
  <meta name="keywords" content="{html.escape(keywords)}" />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <link rel="canonical" href="{html.escape(_slug_url(persona['slug']))}" />
  <link rel="stylesheet" href="../../styles.css" />
  <script type="application/ld+json">{json.dumps(structured, separators=(',', ':'))}</script>
</head>
<body>
  <main class="container">
    <a class="back" href="../index.html">Back to audiences</a>
    <h1>{html.escape(title)}</h1>
    <p>{html.escape(persona['positioning'])}</p>
    <p>{html.escape(persona['audience'])}</p>
    <p>
      <a href="{html.escape(ios_url)}">Download for iOS</a>
      <span> | </span>
      <a href="{html.escape(android_url)}">Download for Android</a>
    </p>
    <h2>Best-fit drills</h2>
    <ul>{topics}</ul>
    <h2>Outreach targets</h2>
    <ul>{communities}</ul>
  </main>
</body>
</html>
"""


def write_audience_pages(personas: list[dict[str, Any]], site_dir: Path) -> list[Path]:
    site_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    cards: list[str] = []
    for persona in personas:
        page_dir = site_dir / persona["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        page_path = page_dir / "index.html"
        page_path.write_text(_render_audience_page(persona), encoding="utf-8")
        written.append(page_path)
        cards.append(
            "<article class=\"post-card\">"
            f"<h2><a href=\"{html.escape(persona['slug'])}/index.html\">{html.escape(persona['display_name'])}</a></h2>"
            f"<p>{html.escape(persona['positioning'])}</p>"
            "</article>"
        )

    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Random Tactical Timer Audience Pages</title>
  <meta name="description" content="Persona-specific pages for Random Tactical Timer training audiences." />
  <meta name="robots" content="index,follow,max-image-preview:large" />
  <link rel="canonical" href="https://igorganapolsky.github.io/Random-Timer/marketing/site/audiences/" />
  <link rel="stylesheet" href="../styles.css" />
</head>
<body>
  <main class="container">
    <a class="back" href="../index.html">Back to blog</a>
    <h1>Random Tactical Timer audience pages</h1>
    <p>Persona-specific pages and campaign links for store growth, attribution, and outreach.</p>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    index_path = site_dir / "index.html"
    index_path.write_text(index, encoding="utf-8")
    written.append(index_path)
    return written


def build(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    personas_path = args.personas.resolve()
    generated_dir = (repo_root / "marketing" / "store_growth" / "generated").resolve()
    site_dir = (repo_root / "marketing" / "site" / "audiences").resolve()
    attribution_path = (repo_root / "marketing" / "data" / "store_growth_attribution.json").resolve()

    payload = _load_json(personas_path)
    errors = validate_personas(payload)
    if errors:
        raise SystemExit("Invalid store growth personas: " + "; ".join(errors))

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    plan = build_plan(payload, generated_at)
    generated_dir.mkdir(parents=True, exist_ok=True)
    _write_json(generated_dir / "store_growth_plan.json", plan)
    _write_json(generated_dir / "google_custom_store_listings.json", plan["google_custom_store_listings"])
    _write_json(generated_dir / "apple_custom_product_pages.json", plan["apple_custom_product_pages"])
    _write_json(generated_dir / "persona_content_calendar.json", plan["content_calendar"])
    _write_json(attribution_path, plan["attribution"])
    written_pages = write_audience_pages(payload["personas"], site_dir)

    return {
        "status": "ok",
        "personas": len(payload["personas"]),
        "google_custom_store_listings": len(plan["google_custom_store_listings"]),
        "apple_custom_product_pages": len(plan["apple_custom_product_pages"]),
        "content_topics": len(plan["content_calendar"]),
        "audience_pages": len(written_pages),
        "generated_dir": str(generated_dir.relative_to(repo_root)),
        "attribution_path": str(attribution_path.relative_to(repo_root)),
    }


def topic(args: argparse.Namespace) -> dict[str, Any]:
    payload = _load_json(args.personas.resolve())
    errors = validate_personas(payload)
    if errors:
        raise SystemExit("Invalid store growth personas: " + "; ".join(errors))
    day = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone.utc).date()
    personas = payload["personas"]
    persona = personas[day.toordinal() % len(personas)]
    topics = persona["content"]["article_topics"]
    selected_topic = topics[(day.toordinal() // len(personas)) % len(topics)]
    result = {
        "status": "ok",
        "date": day.isoformat(),
        "persona": persona["slug"],
        "topic": selected_topic,
        "utm_campaign": persona["utm"]["campaign"],
        "utm_content": persona["utm"]["content"],
    }
    if args.github_output:
        path = Path(args.github_output)
        with path.open("a", encoding="utf-8") as handle:
            for key in ("persona", "topic", "utm_campaign", "utm_content"):
                handle.write(f"{key}={result[key]}\n")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Store growth automation")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--personas", type=Path, default=DEFAULT_PERSONAS)
    parser.add_argument("--json-stdout", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build", help="Validate personas and write generated growth artifacts")
    p_build.add_argument("--json-stdout", action="store_true")
    p_topic = sub.add_parser("topic", help="Select today's persona-specific article topic")
    p_topic.add_argument("--date", default="")
    p_topic.add_argument("--github-output", default="")
    p_topic.add_argument("--json-stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build(args) if args.command == "build" else topic(args)
    if args.json_stdout:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
