#!/usr/bin/env python3
"""Audit the unified developer docs hub and capabilities catalog.

Inspired by Pi Network's developer documentation consolidation playbook:
https://minepi.com/blog/dev-capabilities-documentation/

Checks:
- hub + catalog exist in docs/ and marketing/site/ (Pages deploy root)
- catalog schema + journey steps
- relative markdown links in the hub resolve on disk
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


JOURNEY_IDS = ("get_started", "local_build", "integrate_capabilities", "store_launch")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _broken_md_links(hub: Path, repo_root: Path) -> list[str]:
    text = hub.read_text(encoding="utf-8")
    broken: list[str] = []
    for _label, target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0].strip()
        if not clean:
            continue
        candidate = (hub.parent / clean).resolve()
        if not candidate.exists():
            # also allow repo-root-relative paths written from docs/
            alt = (repo_root / clean).resolve()
            if not alt.exists():
                broken.append(target)
    return broken


def audit(repo_root: Path) -> dict[str, Any]:
    hub = repo_root / "docs" / "DEVELOPERS.md"
    caps_path = repo_root / "docs" / "developer_capabilities.json"
    site_hub = repo_root / "marketing" / "site" / "developers.md"
    site_caps = repo_root / "marketing" / "site" / "developer_capabilities.json"

    errors: list[str] = []
    for path in (hub, caps_path, site_hub, site_caps):
        if not path.is_file():
            errors.append(f"missing:{path.relative_to(repo_root)}")

    caps: dict[str, Any] = {}
    if caps_path.is_file():
        caps = _load_json(caps_path)
        if caps.get("brand") != "Random Tactical Timer":
            errors.append("catalog brand mismatch")
        caps_list = caps.get("capabilities") or []
        if len(caps_list) < 5:
            errors.append("catalog needs >=5 capabilities")
        journey = caps.get("developer_journey") or []
        ids = [step.get("id") for step in journey]
        if ids != list(JOURNEY_IDS):
            errors.append(f"journey ids mismatch: {ids}")
        for cap in caps_list:
            for key in ("id", "name", "status", "platforms", "summary", "evidence_paths"):
                if key not in cap:
                    errors.append(f"capability missing {key}: {cap.get('id')}")
            for evidence in cap.get("evidence_paths") or []:
                if not (repo_root / evidence).exists():
                    errors.append(f"missing evidence:{evidence}")

    if site_caps.is_file() and caps_path.is_file():
        if site_caps.read_text(encoding="utf-8") != caps_path.read_text(encoding="utf-8"):
            errors.append("site capabilities catalog out of sync with docs/")

    broken = _broken_md_links(hub, repo_root) if hub.is_file() else []
    for link in broken:
        errors.append(f"broken_link:{link}")

    return {
        "ok": not errors,
        "errors": errors,
        "broken_links": broken,
        "capability_count": len(caps.get("capabilities") or []),
        "hub": str(hub.relative_to(repo_root)) if hub.is_file() else None,
        "source_playbook": "https://minepi.com/blog/dev-capabilities-documentation/",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args(argv)
    report = audit(args.repo_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
