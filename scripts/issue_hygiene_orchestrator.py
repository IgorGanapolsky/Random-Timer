#!/usr/bin/env python3
"""Autonomous issue hygiene orchestrator.

Closes automation-generated GitHub issues that humans should never babysit:
  - release-watch issues for superseded / dual-live store versions
  - pr-state-machine incident issues whose linked PR is MERGED/CLOSED
  - known CI gate issues once voice regression contracts pass

Agents and CI run: python3 scripts/issue_hygiene_orchestrator.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WATCH_RE = re.compile(r"^Release watch:\s*v?(\d+\.\d+\.\d+)\s*$", re.I)
PR_INCIDENT_RE = re.compile(r"^PR Incident:\s*#(\d+)\b", re.I)
CI_GATE_RE = re.compile(r"CI base gates red", re.I)
STALE_IN_FLIGHT_DAYS = 14


@dataclass(frozen=True)
class Decision:
    action: str  # keep | close
    reason: str
    comment: str = ""


def parse_semver(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def parse_release_watch_version(title: str) -> str | None:
    match = RELEASE_WATCH_RE.match(title.strip())
    return match.group(1) if match else None


def parse_pr_incident_number(title: str) -> int | None:
    match = PR_INCIDENT_RE.match(title.strip())
    return int(match.group(1)) if match else None


def decide_release_watch(
    *,
    title: str,
    live_ios: str | None,
    live_play: str | None,
    created_at: str | None = None,
    now: datetime | None = None,
) -> Decision:
    version = parse_release_watch_version(title)
    if not version:
        return Decision("keep", "not_release_watch")

    live_candidates = [v for v in (live_ios, live_play) if v]
    if live_candidates:
        max_live = max(live_candidates, key=parse_semver)
        if parse_semver(version) < parse_semver(max_live):
            return Decision(
                "close",
                "superseded",
                f"Autonomous hygiene: v{version} superseded by live store version v{max_live}. Closing release-watch.",
            )

    if live_ios and live_play and live_ios == version and live_play == version:
        return Decision(
            "close",
            "both_live",
            f"Autonomous hygiene: v{version} is LIVE on iOS and Play. Closing release-watch.",
        )

    # Abandoned in-flight watches (newer than live but stuck for weeks).
    if live_candidates and parse_semver(version) > parse_semver(max(live_candidates, key=parse_semver)):
        if created_at:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            current = now or datetime.now(timezone.utc)
            age_days = (current - created).days
            if age_days >= STALE_IN_FLIGHT_DAYS:
                return Decision(
                    "close",
                    "stale_in_flight",
                    f"Autonomous hygiene: v{version} is newer than live but stale ({age_days}d) with no ship evidence. Closing abandoned release-watch.",
                )

    return Decision("keep", "in_flight")


def decide_pr_incident(*, title: str, pr_state: str | None) -> Decision:
    pr_number = parse_pr_incident_number(title)
    if pr_number is None:
        return Decision("keep", "not_pr_incident")
    state = (pr_state or "").upper()
    if state == "MERGED":
        return Decision(
            "close",
            "pr_merged",
            f"Autonomous hygiene: linked PR #{pr_number} is MERGED. Closing incident.",
        )
    if state == "CLOSED":
        return Decision(
            "close",
            "pr_closed",
            f"Autonomous hygiene: linked PR #{pr_number} is CLOSED. Closing incident.",
        )
    return Decision("keep", "pr_open")


def decide_ci_gate_issue(*, title: str, voice_contracts_passing: bool) -> Decision:
    if not CI_GATE_RE.search(title):
        return Decision("keep", "not_ci_gate")
    if voice_contracts_passing:
        return Decision(
            "close",
            "voice_contracts_green",
            "Autonomous hygiene: `test_voice_regression_contracts` passes on develop. Closing CI gate issue.",
        )
    return Decision("keep", "voice_contracts_red")


def _gh_json(args: list[str]) -> Any:
    proc = subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"gh {' '.join(args)} failed")
    return json.loads(proc.stdout or "null")


def fetch_live_ios_version(bundle_lookup_id: str = "6758355312") -> str | None:
    url = f"https://itunes.apple.com/lookup?id={bundle_lookup_id}&country=us"
    with urllib.request.urlopen(url, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    results = payload.get("results") or []
    if not results:
        return None
    version = results[0].get("version")
    return str(version) if version else None


def fetch_live_play_version(package: str = "com.iganapolsky.randomtimer") -> str | None:
    """Best-effort public Play version via existing verifier script stdout."""
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "verify_play_public_listing.py"),
            "--package",
            package,
            "--timeout",
            "45",
            "--poll-interval",
            "5",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    combined = f"{proc.stdout}\n{proc.stderr}"
    match = re.search(r"(?:displayed[_ ]version|versionName|version)[=:\s]+([0-9]+\.[0-9]+\.[0-9]+)", combined, re.I)
    if match:
        return match.group(1)
    # Fallback: if verifier exits 0 against expected, we don't know exact; leave unknown.
    return None


def voice_contracts_pass() -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "scripts/tests/test_voice_regression_contracts.py", "-q"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def plan_actions(
    issues: list[dict[str, Any]],
    *,
    live_ios: str | None,
    live_play: str | None,
    pr_states: dict[int, str],
    voice_ok: bool,
) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for issue in issues:
        number = int(issue["number"])
        title = issue.get("title") or ""
        labels = {str(label.get("name") if isinstance(label, dict) else label) for label in (issue.get("labels") or [])}

        decision: Decision | None = None
        if "release-watch" in labels or title.lower().startswith("release watch:"):
            decision = decide_release_watch(
                title=title,
                live_ios=live_ios,
                live_play=live_play,
                created_at=issue.get("createdAt"),
            )
        elif "pr-state-machine" in labels or title.lower().startswith("pr incident:"):
            pr_number = parse_pr_incident_number(title)
            decision = decide_pr_incident(
                title=title,
                pr_state=pr_states.get(pr_number) if pr_number else None,
            )
        elif CI_GATE_RE.search(title):
            decision = decide_ci_gate_issue(title=title, voice_contracts_passing=voice_ok)

        if decision is None:
            continue
        planned.append(
            {
                "number": number,
                "title": title,
                "decision": asdict(decision),
            }
        )
    return planned


def apply_plan(plan: list[dict[str, Any]], *, dry_run: bool) -> dict[str, Any]:
    closed: list[int] = []
    kept: list[int] = []
    for item in plan:
        number = int(item["number"])
        decision = item["decision"]
        if decision["action"] != "close":
            kept.append(number)
            continue
        if dry_run:
            closed.append(number)
            continue
        comment = decision.get("comment") or f"Autonomous hygiene: {decision.get('reason')}"
        subprocess.run(
            ["gh", "issue", "comment", str(number), "--body", comment],
            check=False,
            capture_output=True,
            text=True,
        )
        proc = subprocess.run(
            ["gh", "issue", "close", str(number), "--reason", "completed"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            closed.append(number)
        else:
            kept.append(number)
    return {"closed": closed, "kept": kept}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="IgorGanapolsky/Random-Timer")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-play", action="store_true")
    parser.add_argument("--live-ios", default="")
    parser.add_argument("--live-play", default="")
    args = parser.parse_args(argv)

    issues = _gh_json(
        [
            "issue",
            "list",
            "--repo",
            args.repo,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title,labels,createdAt",
        ]
    )

    live_ios = args.live_ios or fetch_live_ios_version()
    live_play = args.live_play or (None if args.skip_play else fetch_live_play_version())

    pr_states: dict[int, str] = {}
    for issue in issues:
        pr_number = parse_pr_incident_number(issue.get("title") or "")
        if pr_number is None:
            continue
        try:
            pr = _gh_json(
                [
                    "pr",
                    "view",
                    str(pr_number),
                    "--repo",
                    args.repo,
                    "--json",
                    "state",
                ]
            )
            pr_states[pr_number] = str(pr.get("state") or "")
        except RuntimeError:
            pr_states[pr_number] = "MISSING"

    voice_ok = voice_contracts_pass()
    plan = plan_actions(
        issues,
        live_ios=live_ios,
        live_play=live_play,
        pr_states=pr_states,
        voice_ok=voice_ok,
    )

    result: dict[str, Any] = {
        "live_ios": live_ios,
        "live_play": live_play,
        "voice_contracts_passing": voice_ok,
        "open_issues_scanned": len(issues),
        "plan": plan,
        "close_count": sum(1 for item in plan if item["decision"]["action"] == "close"),
        "keep_count": sum(1 for item in plan if item["decision"]["action"] == "keep"),
    }

    if args.apply or args.dry_run:
        result["apply"] = apply_plan(plan, dry_run=args.dry_run and not args.apply)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
