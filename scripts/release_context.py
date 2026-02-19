#!/usr/bin/env python3
"""Build a precomputed iOS release context snapshot.

This script consolidates local listing readiness and optional App Store Connect
remote signals into one JSON artifact that downstream automation can reuse.

It intentionally avoids mutating store state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

IPHONE_LARGE_DIMENSIONS = {
    "1320x2868",
    "2868x1320",
    "1290x2796",
    "2796x1290",
    "1284x2778",
    "2778x1284",
    "1242x2688",
    "2688x1242",
}

IPAD_LARGE_DIMENSIONS = {
    "2064x2752",
    "2752x2064",
    "2048x2732",
    "2732x2048",
}

REQUIRED_IPAD_FILES = {"5_ipad_setup.png", "6_ipad_running.png", "7_ipad_stopped.png"}

REQUIRED_METADATA_FILES = {
    "description": "description.txt",
    "keywords": "keywords.txt",
    "support_url": "support_url.txt",
    "privacy_url": "privacy_url.txt",
}


class ContextError(RuntimeError):
    """Raised when snapshot generation cannot proceed."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_png_dimensions(path: Path) -> Tuple[int, int]:
    png_sig = b"\x89PNG\r\n\x1a\n"
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != png_sig:
        raise ContextError(f"not a PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_ios_version(repo_root: Path) -> str:
    pbxproj = repo_root / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"
    if not pbxproj.is_file():
        raise ContextError(f"Missing Xcode project file: {pbxproj}")

    text = pbxproj.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"MARKETING_VERSION\s*=\s*([0-9]+(?:\.[0-9]+){1,2})\s*;", text)
    if not match:
        raise ContextError("Could not detect MARKETING_VERSION in project.pbxproj")
    return match.group(1)


def _classify_dimension(size: str) -> str:
    if size in IPHONE_LARGE_DIMENSIONS:
        return "iphone_large"
    if size in IPAD_LARGE_DIMENSIONS:
        return "ipad_large"
    return "other"


def collect_screenshot_inventory(screenshots_dir: Path) -> Dict[str, Any]:
    files = sorted(screenshots_dir.glob("*.png")) if screenshots_dir.is_dir() else []

    iphone_count = 0
    ipad_count = 0
    other_count = 0
    records: List[Dict[str, Any]] = []
    hash_to_files: Dict[str, List[str]] = {}

    for path in files:
        width, height = _read_png_dimensions(path)
        size = f"{width}x{height}"
        cls = _classify_dimension(size)
        if cls == "iphone_large":
            iphone_count += 1
        elif cls == "ipad_large":
            ipad_count += 1
        else:
            other_count += 1

        digest = _sha256(path)
        hash_to_files.setdefault(digest, []).append(path.name)

        records.append(
            {
                "file": path.name,
                "size": size,
                "class": cls,
                "sha256": digest,
            }
        )

    duplicate_groups = [names for names in hash_to_files.values() if len(names) > 1]
    missing_required_ipad_files = sorted(
        [name for name in REQUIRED_IPAD_FILES if not (screenshots_dir / name).is_file()]
    )

    passes = {
        "total_minimum": len(files) >= 6,
        "iphone_large_minimum": iphone_count >= 3,
        "ipad_large_minimum": ipad_count >= 3,
        "required_ipad_files": len(missing_required_ipad_files) == 0,
        "no_duplicate_image_bytes": len(duplicate_groups) == 0,
    }

    return {
        "directory": str(screenshots_dir),
        "total": len(files),
        "iphone_large_count": iphone_count,
        "ipad_large_count": ipad_count,
        "other_count": other_count,
        "missing_required_ipad_files": missing_required_ipad_files,
        "duplicate_groups": duplicate_groups,
        "passes": passes,
        "files": records,
    }


def collect_metadata_fields(metadata_dir: Path) -> Dict[str, Any]:
    fields: Dict[str, Dict[str, Any]] = {}
    missing_required: List[str] = []

    for field_name, filename in REQUIRED_METADATA_FILES.items():
        path = metadata_dir / filename
        value = path.read_text(encoding="utf-8", errors="replace").strip() if path.is_file() else ""
        present = bool(value)
        if not present:
            missing_required.append(field_name)
        fields[field_name] = {
            "file": str(path),
            "present": present,
            "length": len(value),
            "value": value,
        }

    return {
        "directory": str(metadata_dir),
        "required_fields": fields,
        "missing_required_fields": missing_required,
        "passes": {
            "required_fields_non_empty": len(missing_required) == 0,
        },
    }


def collect_local_context(repo_root: Path, locale: str) -> Dict[str, Any]:
    screenshots_dir = repo_root / "native-ios" / "fastlane" / "screenshots" / locale
    metadata_dir = repo_root / "native-ios" / "fastlane" / "metadata" / locale

    screenshots = collect_screenshot_inventory(screenshots_dir)
    metadata = collect_metadata_fields(metadata_dir)

    local_ready = all(screenshots["passes"].values()) and all(metadata["passes"].values())

    return {
        "screenshots": screenshots,
        "metadata": metadata,
        "local_ready": local_ready,
    }


def has_asc_credentials(env: Dict[str, str]) -> bool:
    key_id = (env.get("APPSTORE_KEY_ID") or "").strip()
    issuer = (env.get("APPSTORE_ISSUER_ID") or "").strip()
    key_material = (env.get("APPSTORE_PRIVATE_KEY") or env.get("APPSTORE_PRIVATE_KEY_PATH") or "").strip()
    if not key_material and key_id:
        default_key = Path.home() / ".appstoreconnect" / "private_keys" / f"AuthKey_{key_id}.p8"
        key_material = str(default_key) if default_key.is_file() else ""
    return bool(key_id and issuer and key_material)


def _run_json_command(cmd: List[str], json_path: Path, cwd: Path, env: Dict[str, str]) -> Dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)

    payload: Optional[Dict[str, Any]] = None
    if json_path.is_file():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None

    return {
        "command": cmd,
        "exit_code": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-25:]),
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-25:]),
        "payload": payload,
        "status": "success" if proc.returncode == 0 else "failed",
    }


def _extract_build_processing_state(asc_ready_payload: Optional[Dict[str, Any]]) -> Optional[str]:
    if not asc_ready_payload:
        return None

    for check in asc_ready_payload.get("checks", []) or []:
        evidence = check.get("evidence") or {}
        state = evidence.get("processingState")
        if state:
            return str(state)

        # Backward-compatible fallback for legacy check naming.
        name = str(check.get("name") or "")
        if name.startswith("Build Attached"):
            details = str(check.get("details") or "")
            m = re.search(r"processingState=([A-Z_]+)", details)
            if m:
                return m.group(1)
    return None


def collect_remote_context(
    repo_root: Path,
    version: str,
    locale: str,
    include_remote: bool,
    review_limit: int,
    sla_hours: int,
    env: Dict[str, str],
) -> Dict[str, Any]:
    if not include_remote:
        return {
            "status": "skipped_no_remote",
            "asc_readiness": {"status": "skipped_no_remote"},
            "reviews_ops": {"status": "skipped_no_remote"},
        }

    if not has_asc_credentials(env):
        return {
            "status": "skipped_missing_credentials",
            "asc_readiness": {"status": "skipped_missing_credentials"},
            "reviews_ops": {"status": "skipped_missing_credentials"},
        }

    with tempfile.TemporaryDirectory(prefix="release-context-") as tmp:
        tmp_path = Path(tmp)
        asc_json = tmp_path / "asc-ready.json"
        reviews_json = tmp_path / "asc-reviews.json"

        asc_cmd = [
            sys.executable,
            str(repo_root / "scripts" / "asc_verify_ready.py"),
            "--version",
            version,
            "--locale",
            locale,
            "--json",
            str(asc_json),
        ]
        asc_result = _run_json_command(asc_cmd, asc_json, repo_root, env)

        reviews_cmd = [
            sys.executable,
            str(repo_root / "scripts" / "asc_reviews_ops.py"),
            "--bundle-id",
            "com.igorganapolsky.randomtimer",
            "--limit",
            str(review_limit),
            "--sla-hours",
            str(sla_hours),
            "--json-out",
            str(reviews_json),
        ]
        reviews_result = _run_json_command(reviews_cmd, reviews_json, repo_root, env)

        build_processing = _extract_build_processing_state(asc_result.get("payload"))

        status = "success" if asc_result["status"] == "success" and reviews_result["status"] == "success" else "partial_failure"
        return {
            "status": status,
            "build_processing_state": build_processing,
            "asc_readiness": asc_result,
            "reviews_ops": reviews_result,
        }


def build_summary(local_ctx: Dict[str, Any], remote_ctx: Dict[str, Any]) -> Dict[str, Any]:
    local_ready = bool(local_ctx.get("local_ready"))

    remote_status = str(remote_ctx.get("status") or "unknown")
    remote_ready = remote_status == "success"

    review_payload = ((remote_ctx.get("reviews_ops") or {}).get("payload") or {})
    sla_breach_count = int(review_payload.get("slaBreachCount") or 0)

    blockers: List[str] = []
    if not local_ready:
        blockers.append("local_listing_requirements_failed")
    if remote_status == "partial_failure":
        blockers.append("remote_checks_failed")
    if remote_status == "skipped_missing_credentials":
        blockers.append("remote_checks_skipped_missing_credentials")
    if sla_breach_count > 0:
        blockers.append("review_sla_breaches_present")

    return {
        "local_ready": local_ready,
        "remote_status": remote_status,
        "remote_ready": remote_ready,
        "build_processing_state": remote_ctx.get("build_processing_state"),
        "sla_breach_count": sla_breach_count,
        "blockers": blockers,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate consolidated release context JSON.")
    parser.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--version", help="iOS marketing version (auto-detected if omitted)")
    parser.add_argument("--locale", default="en-US", help="Store locale (default: en-US)")
    parser.add_argument("--json-out", required=True, help="Output JSON path")
    parser.add_argument("--no-remote", action="store_true", help="Skip remote ASC checks")
    parser.add_argument("--review-limit", type=int, default=200, help="Reviews scan limit for SLA report")
    parser.add_argument("--sla-hours", type=int, default=24, help="SLA threshold in hours")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    version = args.version or detect_ios_version(repo_root)

    local_ctx = collect_local_context(repo_root, args.locale)
    remote_ctx = collect_remote_context(
        repo_root=repo_root,
        version=version,
        locale=args.locale,
        include_remote=not args.no_remote,
        review_limit=args.review_limit,
        sla_hours=args.sla_hours,
        env=os.environ.copy(),
    )

    summary = build_summary(local_ctx, remote_ctx)

    snapshot = {
        "generated_at": _now_iso(),
        "repo_root": str(repo_root),
        "bundle_id": "com.igorganapolsky.randomtimer",
        "version": version,
        "locale": args.locale,
        "local": local_ctx,
        "remote": remote_ctx,
        "summary": summary,
    }

    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")

    print("══ Release Context Snapshot ═══════════════════════")
    print(f"Output:            {out_path}")
    print(f"Version:           {version}")
    print(f"Local ready:       {summary['local_ready']}")
    print(f"Remote status:     {summary['remote_status']}")
    print(f"Build processing:  {summary['build_processing_state']}")
    print(f"SLA breaches:      {summary['sla_breach_count']}")
    print(f"Blockers:          {', '.join(summary['blockers']) if summary['blockers'] else 'none'}")
    print("═══════════════════════════════════════════════════")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
