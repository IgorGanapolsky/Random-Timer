#!/usr/bin/env python3
"""Fleet assets — Dagster-style catalog, freshness, and checks (OSS patterns, no Dagster+).

Inspired by https://docs.dagster.io/ — assets, deps/lineage, asset checks, freshness.
Materializations are JSON files under marketing/data/; this CLI observes and checks them.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CATALOG = Path("marketing/data/fleet_asset_catalog.json")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_asset_json(root: Path, rel: str) -> dict[str, Any] | None:
    p = root / rel
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def run_check(
    name: str,
    asset: dict[str, Any],
    payload: dict[str, Any] | None,
    *,
    now: datetime,
) -> dict[str, Any]:
    if payload is None:
        return {
            "asset": asset["key"],
            "check": name,
            "passed": False,
            "detail": f"missing file: {asset.get('path')}",
        }

    if name == "file_exists":
        return {"asset": asset["key"], "check": name, "passed": True, "detail": "ok"}

    if name == "has_generated_at":
        ts = _parse_ts(payload.get("generated_at"))
        return {
            "asset": asset["key"],
            "check": name,
            "passed": ts is not None,
            "detail": "generated_at present" if ts else "generated_at missing/invalid",
        }

    if name == "required_keys":
        required = list(asset.get("required_keys") or [])
        missing = [k for k in required if k not in payload]
        return {
            "asset": asset["key"],
            "check": name,
            "passed": not missing,
            "detail": "ok" if not missing else f"missing keys: {missing}",
        }

    if name == "fresh_within_days":
        days = float(asset.get("freshness_days") or 7)
        ts = _parse_ts(payload.get("generated_at"))
        if ts is None:
            return {
                "asset": asset["key"],
                "check": name,
                "passed": False,
                "detail": "no generated_at",
            }
        age_days = (now - ts).total_seconds() / 86400.0
        ok = age_days <= days
        return {
            "asset": asset["key"],
            "check": name,
            "passed": ok,
            "detail": f"age_days={age_days:.1f} limit={days}",
        }

    if name == "proxy_labels_present":
        # Operational reliability: proxy metrics must be labeled when present.
        metric_id = payload.get("review_count_metric_id")
        defs = payload.get("definitions") or {}
        has_label = bool(metric_id) or bool(defs)
        # Pass if either labeled or asset doesn't claim review counts.
        claims_reviews = "reviews" in json.dumps(payload).lower() and "review_count" in json.dumps(
            payload
        ).lower()
        if not claims_reviews:
            return {
                "asset": asset["key"],
                "check": name,
                "passed": True,
                "detail": "no review-count claim",
            }
        return {
            "asset": asset["key"],
            "check": name,
            "passed": has_label,
            "detail": "labeled" if has_label else "review counts without metric_id/definitions",
        }

    return {
        "asset": asset["key"],
        "check": name,
        "passed": False,
        "detail": f"unknown check: {name}",
    }


def cmd_catalog(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else _repo_root()
    catalog_path = Path(args.catalog) if args.catalog else root / DEFAULT_CATALOG
    catalog = load_catalog(catalog_path)
    out = {
        "source": "fleet_assets",
        "inspired_by": "https://docs.dagster.io/",
        "catalog": str(catalog_path),
        "assets": catalog.get("assets", []),
    }
    print(json.dumps(out, indent=2 if not args.compact else None))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else _repo_root()
    catalog_path = Path(args.catalog) if args.catalog else root / DEFAULT_CATALOG
    catalog = load_catalog(catalog_path)
    now = datetime.now(timezone.utc)
    results: list[dict[str, Any]] = []
    for asset in catalog.get("assets", []):
        payload = load_asset_json(root, asset["path"])
        checks = list(asset.get("checks") or ["file_exists", "has_generated_at"])
        for check_name in checks:
            results.append(run_check(check_name, asset, payload, now=now))
    passed = all(r["passed"] for r in results)
    out = {
        "source": "fleet_assets",
        "passed": passed,
        "checked_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": results,
    }
    print(json.dumps(out, indent=2 if not args.compact else None))
    return 0 if passed else 1


def cmd_lineage(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else _repo_root()
    catalog_path = Path(args.catalog) if args.catalog else root / DEFAULT_CATALOG
    catalog = load_catalog(catalog_path)
    edges = []
    for asset in catalog.get("assets", []):
        for dep in asset.get("deps") or []:
            edges.append({"from": dep, "to": asset["key"]})
    out = {"source": "fleet_assets", "edges": edges, "nodes": [a["key"] for a in catalog["assets"]]}
    print(json.dumps(out, indent=2 if not args.compact else None))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Observe assets (Dagster-style observation — not a materialization)."""
    root = Path(args.root) if args.root else _repo_root()
    catalog_path = Path(args.catalog) if args.catalog else root / DEFAULT_CATALOG
    catalog = load_catalog(catalog_path)
    now = datetime.now(timezone.utc)
    rows = []
    for asset in catalog.get("assets", []):
        payload = load_asset_json(root, asset["path"])
        ts = _parse_ts((payload or {}).get("generated_at")) if payload else None
        age = None if ts is None else round((now - ts).total_seconds() / 86400.0, 2)
        rows.append(
            {
                "key": asset["key"],
                "path": asset["path"],
                "exists": payload is not None,
                "generated_at": (payload or {}).get("generated_at"),
                "age_days": age,
                "deps": asset.get("deps") or [],
            }
        )
    out = {"source": "fleet_assets", "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "assets": rows}
    print(json.dumps(out, indent=2 if not args.compact else None))
    return 0


def _add_common_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--root", default=None, help="Repo root (default: parent of scripts/)")
    p.add_argument("--catalog", default=None, help="Catalog JSON path")
    p.add_argument("--compact", action="store_true")
    p.add_argument("--json", action="store_true", help="JSON output (default)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cat = sub.add_parser("catalog", help="Print asset catalog")
    _add_common_flags(p_cat)
    p_cat.set_defaults(func=cmd_catalog)

    p_check = sub.add_parser("check", help="Run asset checks")
    _add_common_flags(p_check)
    p_check.set_defaults(func=cmd_check)

    p_lin = sub.add_parser("lineage", help="Print dep edges")
    _add_common_flags(p_lin)
    p_lin.set_defaults(func=cmd_lineage)

    p_st = sub.add_parser("status", help="Observe asset freshness (non-materializing)")
    _add_common_flags(p_st)
    p_st.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
