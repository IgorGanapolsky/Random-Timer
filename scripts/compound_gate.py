#!/usr/bin/env python3
"""Compound Engineering lite gate — docs/solutions/ learning capture.

Inspired by:
  https://theaiengineer.substack.com/p/superpowers-vs-gsd-vs-compound-engineering
  https://github.com/EveryInc/compound-engineering-plugin
  https://every.to/guides/compound-engineering

Does NOT install the full Compound Engineering plugin (33 skills, parallel
reviewer farm). Validates the fourth loop step: Plan → Work → Review → Compound.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_SECTIONS = (
    "Problem",
    "What worked",
    "Prevention",
    "Evidence",
)
PLACEHOLDERS = (
    "[short problem name]",
    "YYYY-MM-DD",
    "What failed, for whom",
    "The fix or workflow that actually resolved it",
)
SOLUTIONS_DIR = "docs/solutions"


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def has_frontmatter(text: str) -> bool:
    if not text.startswith("---"):
        return False
    rest = text[3:]
    end = rest.find("\n---")
    return end >= 0


def assess_solution(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        return {
            "ok": False,
            "path": str(path),
            "missing_sections": list(REQUIRED_SECTIONS),
            "placeholder_hits": [],
            "has_frontmatter": False,
            "reason": "missing_or_empty",
        }
    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    missing = [name for name in REQUIRED_SECTIONS if name not in sections or not sections[name]]
    placeholders = [p for p in PLACEHOLDERS if p in text]
    fm = has_frontmatter(text)
    if not fm:
        missing.append("frontmatter")
    ok = not missing and not placeholders
    return {
        "ok": ok,
        "path": str(path),
        "missing_sections": missing,
        "placeholder_hits": placeholders,
        "has_frontmatter": fm,
        "section_keys": sorted(sections.keys()),
        "bytes": path.stat().st_size,
    }


def list_solutions(root: Path) -> list[Path]:
    solutions = root / SOLUTIONS_DIR
    if not solutions.is_dir():
        return []
    return sorted(
        p for p in solutions.glob("*.md") if p.name.lower() not in {"readme.md", "index.md"}
    )


def evaluate(
    root: Path,
    slug: str | None = None,
    require_any: bool = True,
) -> dict[str, Any]:
    blockers: list[str] = []
    solutions_root = root / SOLUTIONS_DIR
    template = root / "templates" / "compound" / "SOLUTION.md"
    if not template.is_file():
        blockers.append("missing_templates/compound/SOLUTION.md")

    files = list_solutions(root)
    assessments: list[dict[str, Any]] = []

    if slug:
        matches = [p for p in files if slug in p.stem]
        if not matches:
            blockers.append(f"missing_solution:{slug}")
            selected = None
        else:
            selected = matches[0]
            info = assess_solution(selected)
            assessments.append(info)
            if not info["ok"]:
                if info.get("missing_sections"):
                    blockers.append("incomplete_solution:" + ",".join(info["missing_sections"]))
                if info.get("placeholder_hits"):
                    blockers.append("solution_placeholders")
    else:
        selected = None
        if require_any and not files:
            blockers.append("missing_docs/solutions/*.md")
        for path in files:
            info = assess_solution(path)
            assessments.append(info)
            if not info["ok"]:
                blockers.append(f"invalid_solution:{path.name}")

    ready = len(blockers) == 0
    return {
        "source": "compound-engineering-lite",
        "article": "theaiengineer.substack.com/p/superpowers-vs-gsd-vs-compound-engineering",
        "upstream": "EveryInc/compound-engineering-plugin",
        "ready": ready,
        "claim_done_allowed": ready,
        "blockers": blockers,
        "solutions_dir": str(solutions_root),
        "solution_count": len(files),
        "selected": str(selected) if selected else None,
        "assessments": assessments,
        "next_step": "compound" if ready else "write_docs/solutions",
        "bridges": {
            "superpowers": "docs/SUPERPOWERS.md",
            "opengsd": "docs/GSD_OPENGSD.md",
            "spec_kit": "docs/SPEC_KIT.md",
            "bmad": "docs/BMAD.md",
            "compound": "docs/COMPOUND_ENGINEERING.md",
            "playerzero_roi": "docs/AGENT_COMPOUNDING_ROI.md",
        },
        "skipped": [
            "full_plugin_33_skills",
            "parallel_reviewer_farm_default",
            "ce-lfg_50_agent_pipeline",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compound Engineering lite gate")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--slug", default=None, help="Require a matching docs/solutions/<slug>*.md")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Do not require any solution docs (template-only check)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = evaluate(
        Path(args.repo_root).resolve(),
        slug=args.slug,
        require_any=not args.allow_empty,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ready={report['ready']} solutions={report['solution_count']} blockers={report['blockers']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
