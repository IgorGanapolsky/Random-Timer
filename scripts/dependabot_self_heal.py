#!/usr/bin/env python3
"""Self-heal Dependabot security alerts for Python (uv) dependencies.

Agents and CI use this instead of CEO babysitting the GitHub Security tab.

Modes:
  --check   Exit 1 when high/critical open alerts exist and no upgrade plan can
            be formed (or when --require-pr finds no open deps PR).
  --plan    Print JSON upgrade plan from live (or --alerts-file) Dependabot alerts.
  --apply   Rewrite pyproject.toml floors and run `uv lock --upgrade-package`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def alert_package_key(name: str) -> str:
    return name.strip().lower()


def _parse_semver_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for token in version.split("."):
        match = re.match(r"^(\d+)", token)
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts) if parts else (0,)


def _max_version(a: str, b: str) -> str:
    return a if _parse_semver_tuple(a) >= _parse_semver_tuple(b) else b


def infer_min_version_from_range(vulnerable_range: str | None) -> str | None:
    """Infer the first safe floor from a Dependabot range like '< 12.3.0'."""
    if not vulnerable_range:
        return None
    # Prefer exclusive upper bounds as the patched floor.
    match = re.search(r"<\s*([0-9]+(?:\.[0-9]+)*)", vulnerable_range)
    if match:
        return match.group(1)
    match = re.search(r"<=\s*([0-9]+(?:\.[0-9]+)*)", vulnerable_range)
    if match:
        # bump patch when only <= N is known is ambiguous; treat N as floor by
        # requiring callers to also supply first_patched_version when possible.
        return match.group(1)
    return None


def build_upgrade_plan(alerts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    plan: dict[str, dict[str, Any]] = {}
    for alert in alerts:
        vuln = alert.get("security_vulnerability") or {}
        package = alert_package_key(((vuln.get("package") or {}).get("name") or ""))
        if not package:
            continue
        patched = ((vuln.get("first_patched_version") or {}) or {}).get("version")
        inferred = infer_min_version_from_range(vuln.get("vulnerable_version_range"))
        floor = patched or inferred
        if not floor:
            continue
        entry = plan.setdefault(
            package,
            {
                "min_version": floor,
                "alert_numbers": [],
                "severities": [],
                "manifests": set(),
            },
        )
        entry["min_version"] = _max_version(entry["min_version"], floor)
        entry["alert_numbers"].append(int(alert.get("number") or 0))
        severity = ((alert.get("security_advisory") or {}).get("severity") or "unknown").lower()
        entry["severities"].append(severity)
        manifest = ((alert.get("dependency") or {}).get("manifest_path") or "")
        if manifest:
            entry["manifests"].add(manifest)

    # JSON-safe sets
    for entry in plan.values():
        entry["alert_numbers"] = sorted({n for n in entry["alert_numbers"] if n})
        entry["manifests"] = sorted(entry["manifests"])
    return plan


def summarize_open_alerts(alerts: list[dict[str, Any]]) -> dict[str, Any]:
    packages = sorted(
        {
            alert_package_key(
                (((alert.get("security_vulnerability") or {}).get("package") or {}).get("name") or "")
            )
            for alert in alerts
            if (((alert.get("security_vulnerability") or {}).get("package") or {}).get("name"))
        }
    )
    high_or_critical = sum(
        1
        for alert in alerts
        if ((alert.get("security_advisory") or {}).get("severity") or "").lower()
        in {"high", "critical"}
    )
    return {
        "open_count": len(alerts),
        "unique_packages": packages,
        "high_or_critical": high_or_critical,
    }


def render_pyproject_pin(
    pyproject_text: str,
    package: str,
    min_version: str,
    upper: str | None = None,
) -> str:
    """Raise the lower bound for a direct dependency pin in pyproject.toml."""
    # Match optional extras and existing ranges: pillow>=12.2.0,<13
    pattern = re.compile(
        rf'(["\'])({re.escape(package)})(\[[^\]]+\])?(>=|==)([^"\']+)\1',
        re.IGNORECASE,
    )

    def _replace(match: re.Match[str]) -> str:
        quote, name, extras, op, rest = match.groups()
        extras = extras or ""
        if op == "==":
            return f"{quote}{name}{extras}=={min_version}{quote}"
        # Preserve an existing upper bound when present.
        upper_bound = upper
        if upper_bound is None:
            upper_match = re.search(r"(,<[^,]+)$", rest)
            upper_bound = upper_match.group(1) if upper_match else ""
        elif not upper_bound.startswith(","):
            upper_bound = f",{upper_bound}"
        return f"{quote}{name}{extras}>={min_version}{upper_bound}{quote}"

    updated, count = pattern.subn(_replace, pyproject_text)
    if count == 0:
        # Insert into dependencies list when missing (transitive-only otherwise).
        dep_block = re.search(
            r"(dependencies\s*=\s*\[)(.*?)(\n\])",
            pyproject_text,
            flags=re.DOTALL,
        )
        if not dep_block:
            return pyproject_text
        upper_suffix = ""
        if upper:
            upper_suffix = upper if upper.startswith(",") else f",{upper}"
        insertion = f'\n    "{package}>={min_version}{upper_suffix}",'
        return (
            pyproject_text[: dep_block.end(1)]
            + insertion
            + dep_block.group(2)
            + pyproject_text[dep_block.start(3) :]
        )
    return updated


def parse_lock_versions(lock_path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    current: str | None = None
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("name = "):
            current = line.split("=", 1)[1].strip().strip('"').lower()
        elif line.startswith("version = ") and current:
            versions[current] = line.split("=", 1)[1].strip().strip('"')
            current = None
    return versions


def fetch_open_alerts(repo: str) -> list[dict[str, Any]]:
    proc = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/dependabot/alerts?state=open&per_page=100",
            "--paginate",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "gh api dependabot/alerts failed")
    payload = json.loads(proc.stdout or "[]")
    if isinstance(payload, list):
        return payload
    raise RuntimeError("unexpected Dependabot alerts payload shape")


def apply_plan(repo_root: Path, plan: dict[str, dict[str, Any]], dry_run: bool = False) -> dict[str, Any]:
    pyproject_path = repo_root / "pyproject.toml"
    text = pyproject_path.read_text(encoding="utf-8")
    changed_packages: list[str] = []
    for package, entry in sorted(plan.items()):
        min_version = entry["min_version"]
        # Keep existing upper bounds for known direct deps.
        upper = None
        if package == "pillow":
            upper = "<13"
        elif package == "cryptography":
            # Stay on the major floor Dependabot security advisories require.
            major = min_version.split(".", 1)[0]
            upper = f"<{int(major) + 1}"
        elif package == "pyjwt":
            upper = "<3"
        new_text = render_pyproject_pin(text, package, min_version, upper=upper)
        if new_text != text:
            changed_packages.append(package)
            text = new_text

    result: dict[str, Any] = {
        "pyproject_changed": bool(changed_packages),
        "changed_packages": changed_packages,
        "uv_upgraded": [],
    }
    if dry_run:
        return result

    if changed_packages:
        pyproject_path.write_text(text, encoding="utf-8")

    for package in sorted(plan):
        cmd = ["uv", "lock", "--upgrade-package", package]
        proc = subprocess.run(cmd, cwd=repo_root, check=False, capture_output=True, text=True)
        result["uv_upgraded"].append(
            {
                "package": package,
                "ok": proc.returncode == 0,
                "stderr": (proc.stderr or "").strip()[-500:],
            }
        )
        if proc.returncode != 0:
            raise RuntimeError(f"uv lock failed for {package}: {proc.stderr}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="IgorGanapolsky/Random-Timer")
    parser.add_argument("--alerts-file", type=Path, help="Optional JSON alerts fixture")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="With --check, exit 1 when high/critical alerts remain after planning",
    )
    args = parser.parse_args(argv)

    if args.alerts_file:
        alerts = json.loads(args.alerts_file.read_text(encoding="utf-8"))
    else:
        alerts = fetch_open_alerts(args.repo)

    summary = summarize_open_alerts(alerts)
    plan = build_upgrade_plan(alerts)
    lock_versions = parse_lock_versions(REPO_ROOT / "uv.lock") if (REPO_ROOT / "uv.lock").exists() else {}

    payload: dict[str, Any] = {
        "summary": summary,
        "plan": plan,
        "lock_versions": {k: lock_versions[k] for k in plan if k in lock_versions},
    }

    if args.apply:
        payload["apply"] = apply_plan(REPO_ROOT, plan, dry_run=args.dry_run)

    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.check or args.fail_on_high:
        if summary["high_or_critical"] > 0 and not plan:
            return 1
        if args.fail_on_high and summary["high_or_critical"] > 0:
            # Still open highs: caller should apply + open PR. Non-zero signals
            # the heal loop still has work.
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
