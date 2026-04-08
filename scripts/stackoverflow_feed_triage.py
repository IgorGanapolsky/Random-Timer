#!/usr/bin/env python3
"""Read-only Stack Overflow tag feed fetcher for human triage.

Uses public Atom feeds (no API key). Does NOT post answers, vote, or comment.

Feed format: https://stackoverflow.com/feeds/tag?tagnames=TAG1+TAG2&sort=newest

Pair with docs/STACK_OVERFLOW_PLAYBOOK.md — automation is for discovery only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

ATOM_NS = "{http://www.w3.org/2005/Atom}"
USER_AGENT = "RandomTimerTriage/1.0 (+https://github.com/IgorGanapolsky/Random-Timer; human review only)"


def feed_url_for_tags(tags: List[str], sort: str = "newest") -> str:
    joined = "+".join(quote_plus(t.strip()) for t in tags if t.strip())
    if not joined:
        raise ValueError("at least one non-empty tag required")
    return f"https://stackoverflow.com/feeds/tag?tagnames={joined}&sort={sort}"


def parse_atom_entries(xml_bytes: bytes, limit: int) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    out: List[Dict[str, Any]] = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        if len(out) >= limit:
            break
        title_el = entry.find(f"{ATOM_NS}title")
        title = (title_el.text or "").strip() if title_el is not None else ""
        href = ""
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.get("rel") == "alternate":
                href = link.get("href") or ""
                break
        qid_el = entry.find(f"{ATOM_NS}id")
        qid = (qid_el.text or "").strip() if qid_el is not None else ""
        pub_el = entry.find(f"{ATOM_NS}published")
        published = (pub_el.text or "").strip() if pub_el is not None else ""
        out.append(
            {
                "title": title,
                "url": href,
                "id": qid,
                "published": published,
            }
        )
    return out


def fetch_entries(tags: List[str], *, limit: int = 15, sort: str = "newest", timeout: int = 30) -> List[Dict[str, Any]]:
    url = feed_url_for_tags(tags, sort=sort)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return parse_atom_entries(raw, limit)


def _parse_tag_group_lines(text: str) -> List[str]:
    """Return display lines (comma in line = AND tags in SO feed)."""
    out: List[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        out.append(line)
    return out


def write_subscribe_markdown(tag_groups_file: Path, out_path: Path, sort: str = "newest") -> None:
    """Markdown list of Atom feed URLs for Feedly / Inoreader / etc. (same groups as hourly digest)."""
    text = tag_groups_file.read_text(encoding="utf-8")
    groups = _parse_tag_group_lines(text)
    lines = [
        "# Stack Overflow — subscribe in your RSS reader",
        "",
        "Paste each **Feed URL** into Feedly, Inoreader, Outlook, NetNewsWire, etc. "
        "Stack Overflow updates these Atom feeds when new questions appear (no GitHub required).",
        "",
        "_Tag groups mirror `marketing/data/stackoverflow_digest_tag_groups.txt` (same as the hourly Actions digest)._",
        "",
    ]
    for display in groups:
        tags = [t.strip() for t in display.split(",") if t.strip()]
        if not tags:
            continue
        url = feed_url_for_tags(tags, sort=sort)
        lines.append(f"## `{display}`")
        lines.append("")
        lines.append(f"- **Feed URL:** `{url}`")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "## Hourly snapshot (copy/paste question links)\n\n"
        "GitHub Actions also builds a markdown digest every hour: "
        "repo **Actions** → **Stack Overflow hourly triage digest** → artifact **stackoverflow-hourly-digest**."
    )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch SO tag feed for human triage (read-only)")
    parser.add_argument(
        "--write-subscribe-markdown",
        metavar="OUT.md",
        help="Write RSS/Atom subscription list from --tag-groups-file (no fetch)",
    )
    parser.add_argument(
        "--tag-groups-file",
        type=Path,
        default=Path("marketing/data/stackoverflow_digest_tag_groups.txt"),
        help="Used with --write-subscribe-markdown",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tags, e.g. swiftui,storekit (required unless --write-subscribe-markdown)",
    )
    parser.add_argument("--limit", type=int, default=15, help="Max questions to print")
    parser.add_argument("--sort", default="newest", help="Feed sort (e.g. newest, active, votes)")
    parser.add_argument("--json", action="store_true", help="Print JSON lines instead of markdown")
    args = parser.parse_args()

    if args.write_subscribe_markdown:
        out = Path(args.write_subscribe_markdown)
        tg = args.tag_groups_file if args.tag_groups_file.is_absolute() else Path.cwd() / args.tag_groups_file
        try:
            write_subscribe_markdown(tg.resolve(), out, sort=args.sort)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(str(out.resolve()))
        return 0

    if not args.tags.strip():
        parser.error("provide --tags or --write-subscribe-markdown")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    try:
        rows = fetch_entries(tags, limit=args.limit, sort=args.sort)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
        return 0
    print(f"# Stack Overflow — {', '.join(tags)} (last {len(rows)})\n")
    for row in rows:
        print(f"- [{row['title']}]({row['url']})")
        if row.get("published"):
            print(f"  - *{row['published']}*")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
