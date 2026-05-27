#!/usr/bin/env python3
"""Single evidence bundle for release, store, billing, and revenue-proxy verification.

Outputs marketing/data/operational_verification_bundle.json with per-check:
check_id, tier, status, metric_field_id, ground_truth, semantics, command, evidence.

See docs/OPERATIONAL_RELIABILITY.md and .claude/skills/store-verify-ci.md.

Exit codes:
  0 — no blocking failures
  1 — one or more blocking checks failed
  2 — configuration error
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.repo_dotenv import load_repo_dotenv
from scripts.verify_public_store_versions import (
    read_android_version,
    read_github_latest_release_version,
    read_ios_version,
    verify_app_store_public_version,
    verify_play_public_version,
)

BUNDLE_ID = "operational_verification_bundle_v1"
OUTPUT_PATH = REPO_ROOT / "marketing" / "data" / "operational_verification_bundle.json"
RELIABILITY_DOC = "docs/OPERATIONAL_RELIABILITY.md"
BUSINESS_GOAL_USD_PER_DAY = 100.0


@dataclass
class CheckResult:
    check_id: str
    tier: str
    status: str  # pass | fail | skip | advisory_fail | unverified
    metric_field_id: str
    ground_truth: bool
    semantics: str
    command: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_age_hours(generated_at: str, *, max_age_hours: float) -> tuple[bool, float]:
    if not generated_at:
        return True, float("inf")
    try:
        ts = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError:
        return True, float("inf")
    age = datetime.now(timezone.utc) - ts
    hours = age.total_seconds() / 3600.0
    return hours > max_age_hours, hours


def summarize_checks(checks: list[CheckResult]) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "skip": 0, "advisory_fail": 0, "unverified": 0}
    for item in checks:
        key = item.status if item.status in counts else "unverified"
        counts[key] = counts.get(key, 0) + 1
    blocking_fail = sum(1 for c in checks if c.status == "fail")
    return {
        **counts,
        "total": len(checks),
        "blocking_failures": blocking_fail,
        "verifiable_pass": counts["pass"],
    }


def _run_command(cmd: list[str], *, cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _has_play_credentials() -> bool:
    if (os.environ.get("GOOGLE_PLAY_JSON_KEY") or "").strip():
        return True
    path = (os.environ.get("GOOGLE_PLAY_JSON_KEY_PATH") or "").strip()
    if path and Path(path).is_file():
        return True
    return Path("/tmp/play-service-account.json").is_file()


def _has_asc_credentials() -> bool:
    key = (os.environ.get("APPSTORE_PRIVATE_KEY") or "").strip()
    path = (os.environ.get("APPSTORE_PRIVATE_KEY_PATH") or "").strip()
    return bool(key or (path and Path(path).is_file())) and bool(
        (os.environ.get("APPSTORE_KEY_ID") or "").strip()
        and (os.environ.get("APPSTORE_ISSUER_ID") or "").strip()
    )


def _has_posthog_credentials() -> bool:
    api_key = (
        (os.environ.get("POSTHOG_PERSONAL_API_KEY") or "").strip()
        or (os.environ.get("POSTHOG_API_KEY") or "").strip()
    )
    project_id = (os.environ.get("POSTHOG_PROJECT_ID") or "").strip()
    return bool(api_key and project_id)


def check_github_latest_release() -> CheckResult:
    cmd = ["gh", "release", "view", "--json", "tagName,publishedAt,url"]
    code, out, err = _run_command(cmd)
    evidence: dict[str, Any] = {"exit_code": code, "stderr": err[:500] if err else ""}
    if code != 0:
        return CheckResult(
            "github_latest_release",
            "repo",
            "fail",
            "github_release_tag_semver_v1",
            False,
            "Latest GitHub Release tag (not store ground truth).",
            " ".join(cmd),
            evidence,
        )
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        return CheckResult(
            "github_latest_release",
            "repo",
            "fail",
            "github_release_tag_semver_v1",
            False,
            "Latest GitHub Release tag (not store ground truth).",
            " ".join(cmd),
            {**evidence, "parse_error": True},
        )
    tag = str(payload.get("tagName") or "")
    version = tag.lstrip("v")
    evidence.update(payload)
    return CheckResult(
        "github_latest_release",
        "repo",
        "pass",
        "github_release_tag_semver_v1",
        False,
        "Latest GitHub Release tag (not store ground truth).",
        " ".join(cmd),
        evidence,
    )


def check_repo_marketing_versions() -> CheckResult:
    try:
        ios_v = read_ios_version(REPO_ROOT)
        android_v = read_android_version(REPO_ROOT)
        gh_v = read_github_latest_release_version(REPO_ROOT)
    except RuntimeError as exc:
        return CheckResult(
            "repo_marketing_version_sync",
            "repo",
            "fail",
            "repo_native_marketing_version_semver_v1",
            False,
            "versionName / MARKETING_VERSION in repo sources (not store).",
            "read_ios_version + read_android_version + gh release",
            {"error": str(exc)},
        )
    synced = ios_v == android_v == gh_v
    return CheckResult(
        "repo_marketing_version_sync",
        "repo",
        "pass" if synced else "fail",
        "repo_native_marketing_version_semver_v1",
        False,
        "versionName / MARKETING_VERSION must match latest GitHub release tag.",
        "read_ios_version + read_android_version + gh release",
        {"ios": ios_v, "android": android_v, "github_release": gh_v, "synced": synced},
    )


def check_native_release_last_run(expected_version: str) -> CheckResult:
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow=native-release.yml",
        "--limit",
        "5",
        "--json",
        "databaseId,conclusion,status,headBranch,createdAt,url",
    ]
    code, out, err = _run_command(cmd)
    evidence: dict[str, Any] = {"exit_code": code, "stderr": err[:300] if err else ""}
    if code != 0:
        return CheckResult(
            "native_release_last_success",
            "tier0",
            "unverified",
            "github_actions_native_release_last_success_v1",
            False,
            "Most recent native-release.yml workflow on release/v* branch.",
            " ".join(cmd),
            evidence,
        )
    runs = json.loads(out)
    success_on_release = [
        r
        for r in runs
        if r.get("conclusion") == "success"
        and str(r.get("headBranch", "")).startswith("release/v")
    ]
    evidence["runs"] = runs
    if not success_on_release:
        return CheckResult(
            "native_release_last_success",
            "tier0",
            "fail",
            "github_actions_native_release_last_success_v1",
            False,
            "Most recent native-release.yml workflow on release/v* branch.",
            " ".join(cmd),
            evidence,
        )
    latest = success_on_release[0]
    branch_version = str(latest.get("headBranch", "")).replace("release/v", "")
    matches = branch_version == expected_version
    return CheckResult(
        "native_release_last_success",
        "tier0",
        "pass" if matches else "advisory_fail",
        "github_actions_native_release_last_success_v1",
        False,
        "Green native-release on release/vX.Y.Z (upload/review gate; not public storefront).",
        " ".join(cmd),
        {
            "latest_success": latest,
            "expected_version": expected_version,
            "branch_version": branch_version,
            "matches_expected": matches,
        },
    )


def check_public_store_tier2(expected_version: str, *, timeout: int) -> list[CheckResult]:
    checks: list[CheckResult] = []
    ios = verify_app_store_public_version("6758355312", expected_version)
    play = verify_play_public_version("com.iganapolsky.randomtimer", expected_version)
    for item in (ios, play):
        status = "pass" if item.passed else "advisory_fail"
        metric = (
            "itunes_lookup_public_version_field_v1"
            if item.platform == "ios"
            else "play_store_html_141_string_proxy_v1"
        )
        checks.append(
            CheckResult(
                f"public_store_{item.platform}",
                "tier2",
                status,
                metric,
                False,
                (
                    "iTunes lookup version field (US) — not ASC ground truth."
                    if item.platform == "ios"
                    else "Play listing HTML proxy — not Play Console track truth."
                ),
                f"verify_public_store (timeout={timeout}s advisory)",
                {
                    "url": item.url,
                    "expected_version": item.expected_version,
                    "observed_version": item.observed_version,
                    "details": item.details,
                    "propagation_note": "Lag hours–24h+ after tier0 ship; does not invalidate release.",
                },
            )
        )
    return checks


def check_play_iap_catalog() -> CheckResult:
    if not _has_play_credentials():
        return CheckResult(
            "play_iap_catalog",
            "tier0",
            "skip",
            "google_play_monetization_required_subscriptions_v1",
            False,
            "Play Monetization API: elite_tactical annual+monthly ACTIVE; pro_base ACTIVE.",
            "python3 scripts/play_verify_iap_products.py",
            {"reason": "missing GOOGLE_PLAY_JSON_KEY or GOOGLE_PLAY_JSON_KEY_PATH"},
        )
    cmd = [sys.executable, str(SCRIPTS / "play_verify_iap_products.py")]
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=env,
    )
    evidence: dict[str, Any] = {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
    }
    try:
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
        if lines:
            evidence["report"] = json.loads(lines[-1])
    except json.JSONDecodeError:
        pass
    return CheckResult(
        "play_iap_catalog",
        "tier0",
        "pass" if proc.returncode == 0 else "fail",
        "google_play_monetization_required_subscriptions_v1",
        True,
        "Play Monetization API subscription/OTP catalog (ground truth for Play billing).",
        " ".join(cmd),
        evidence,
    )


def check_asc_version_state(version: str) -> CheckResult:
    if not _has_asc_credentials():
        return CheckResult(
            "asc_app_store_version_state",
            "tier1",
            "skip",
            "asc_app_store_version_app_store_state_v1",
            True,
            "App Store Connect appStoreState for target marketing version.",
            f"PYTHONPATH=. python3 scripts/asc/asc_watch_status.py --version {version}",
            {"reason": "missing APPSTORE_KEY_ID / ISSUER_ID / PRIVATE_KEY"},
        )
    cmd = [
        sys.executable,
        str(SCRIPTS / "asc" / "asc_watch_status.py"),
        "--bundle-id",
        "com.igorganapolsky.randomtimer",
        "--version",
        version,
        "--max-polls",
        "1",
        "--print-json",
    ]
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=env,
    )
    evidence = {"exit_code": proc.returncode, "stdout": proc.stdout[-1500:], "stderr": proc.stderr[-300:]}
    state = ""
    try:
        for line in proc.stdout.splitlines():
            if line.strip().startswith("{"):
                payload = json.loads(line)
                state = str(payload.get("state") or "")
                evidence["asc"] = payload
                break
    except json.JSONDecodeError:
        pass
    live_states = {"READY_FOR_SALE", "PENDING_DEVELOPER_RELEASE", "PROCESSING_FOR_APP_STORE"}
    in_review = {"WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_APPLE_RELEASE"}
    prepare = {"PREPARE_FOR_SUBMISSION"}
    if state in live_states:
        st = "pass"
    elif state in in_review:
        st = "advisory_fail"
    elif state in prepare:
        st = "advisory_fail"
    elif proc.returncode != 0 or not state:
        st = "fail" if proc.returncode != 0 else "unverified"
    else:
        st = "advisory_fail"
    return CheckResult(
        "asc_app_store_version_state",
        "tier1",
        st,
        "asc_app_store_version_app_store_state_v1",
        True,
        "App Store Connect appStoreState (authoritative for iOS review; not iTunes lookup).",
        " ".join(cmd),
        {**evidence, "state": state},
    )


def check_posthog_paywall_revenue(*, window_days: int = 30) -> CheckResult:
    if not _has_posthog_credentials():
        return CheckResult(
            "posthog_paywall_purchase_success",
            "analytics",
            "skip",
            "posthog_hogql_count_events_paywall_purchase_success",
            False,
            "In-app telemetry; not App Store / Play ledger proceeds.",
            "POSTHOG execute-sql or paywall_conversion_report.py",
            {"reason": "missing POSTHOG_PERSONAL_API_KEY/POSTHOG_API_KEY or POSTHOG_PROJECT_ID"},
        )
    from scripts.store_downloads_snapshot import posthog_query

    errors: list[str] = []
    api_key = (os.environ.get("POSTHOG_PERSONAL_API_KEY") or os.environ.get("POSTHOG_API_KEY") or "").strip()
    project_id = (os.environ.get("POSTHOG_PROJECT_ID") or "").strip()
    query = f"""
        SELECT
          count() AS events,
          count(DISTINCT person_id) AS persons
        FROM events
        WHERE event = 'paywall_purchase_success'
          AND timestamp > now() - interval {window_days} day
    """
    result = posthog_query(query, api_key, project_id, errors)
    events = 0
    persons = 0
    if result and result.get("results") and result["results"][0]:
        row = result["results"][0]
        events = int(row[0] or 0)
        persons = int(row[1] or 0) if len(row) > 1 else 0
    status = "pass" if events > 0 else "fail"
    return CheckResult(
        "posthog_paywall_purchase_success",
        "analytics",
        status,
        "posthog_hogql_count_events_paywall_purchase_success",
        False,
        f"paywall_purchase_success count trailing {window_days}d — revenue proxy only.",
        "posthog_query (HogQL)",
        {
            "events_30d": events,
            "distinct_persons_30d": persons,
            "query_errors": errors,
            "window_days": window_days,
        },
    )


def check_artifact_staleness() -> list[CheckResult]:
    artifacts = [
        ("executive_metrics.json", REPO_ROOT / "marketing/data/executive_metrics.json", 24.0),
        ("paywall_conversion_report.json", REPO_ROOT / "marketing/data/paywall_conversion_report.json", 24.0),
        ("north_star.json", REPO_ROOT / "marketing/data/north_star.json", 24.0),
    ]
    out: list[CheckResult] = []
    for name, path, max_h in artifacts:
        if not path.is_file():
            out.append(
                CheckResult(
                    f"artifact_fresh_{name}",
                    "repo",
                    "unverified",
                    f"committed_snapshot_{name}_generated_at_v1",
                    False,
                    "Committed marketing snapshot freshness (not live unless refreshed in-session).",
                    f"read {path.relative_to(REPO_ROOT)}",
                    {"missing": True},
                )
            )
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        generated_at = str(payload.get("generated_at") or "")
        stale, age_h = snapshot_age_hours(generated_at, max_age_hours=max_h)
        out.append(
            CheckResult(
                f"artifact_fresh_{name}",
                "repo",
                "advisory_fail" if stale else "pass",
                f"committed_snapshot_{name}_generated_at_v1",
                False,
                f"Snapshot must be <= {max_h}h old for session-truth claims.",
                f"read {path.relative_to(REPO_ROOT)}",
                {"generated_at": generated_at, "age_hours": round(age_h, 2), "stale": stale},
            )
        )
    return out


def build_revenue_goal_section() -> dict[str, Any]:
    exec_path = REPO_ROOT / "marketing/data/executive_metrics.json"
    goal: dict[str, Any] = {
        "target_usd_per_day_after_tax": BUSINESS_GOAL_USD_PER_DAY,
        "metric_bundle_id": "executive_revenue_goal_v1",
        "status": "unverified",
        "posthog_paywall_revenue_avg_usd_per_day": None,
        "posthog_usd_gap_per_day_vs_target": None,
        "events_paywall_purchase_success_30d": None,
        "store_ledger_revenue_usd_30d": None,
        "store_ledger_metric_id": "not_wired_in_executive_snapshot",
        "note": "Use live posthog check in bundle checks[] for session truth; JSON may be stale.",
    }
    if exec_path.is_file():
        try:
            data = json.loads(exec_path.read_text(encoding="utf-8"))
            rg = data.get("revenue_goal") or {}
            goal.update(
                {
                    "status": rg.get("status", "unverified"),
                    "posthog_paywall_revenue_avg_usd_per_day": rg.get(
                        "posthog_paywall_revenue_avg_usd_per_day"
                    ),
                    "posthog_usd_gap_per_day_vs_target": rg.get("posthog_usd_gap_per_day_vs_target"),
                    "events_paywall_purchase_success_30d": rg.get(
                        "events_paywall_purchase_success_30d"
                    ),
                    "snapshot_generated_at": data.get("generated_at"),
                }
            )
            stale, age_h = snapshot_age_hours(str(data.get("generated_at") or ""), max_age_hours=24.0)
            goal["snapshot_stale"] = stale
            goal["snapshot_age_hours"] = round(age_h, 2)
        except json.JSONDecodeError:
            goal["parse_error"] = True
    return goal


def run_all_checks(
    repo_root: Path,
    *,
    expected_version: str,
    public_timeout: int,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(check_github_latest_release())
    checks.append(check_repo_marketing_versions())
    checks.append(check_native_release_last_run(expected_version))
    checks.extend(check_public_store_tier2(expected_version, timeout=public_timeout))
    checks.append(check_play_iap_catalog())
    checks.append(check_asc_version_state(expected_version))
    checks.append(check_posthog_paywall_revenue())
    checks.extend(check_artifact_staleness())
    return checks


def build_bundle(repo_root: Path, checks: list[CheckResult] | None = None) -> dict[str, Any]:
    if checks is None:
        try:
            expected = read_github_latest_release_version(repo_root)
        except RuntimeError:
            expected = ""
        checks = run_all_checks(repo_root, expected_version=expected, public_timeout=10)
    summary = summarize_checks(checks)
    return {
        "generated_at": utc_now_iso(),
        "bundle_id": BUNDLE_ID,
        "reliability_contract_doc": RELIABILITY_DOC,
        "definitions": {
            "ground_truth": "Vendor API or ledger field documented in semantics; false = proxy.",
            "tier0": "Upload/track verify — blocks release when credentials present.",
            "tier1": "ASC review state — authoritative for iOS pipeline.",
            "tier2": "Public storefront HTML/lookup — advisory propagation lag.",
            "blocking_fail": "status=fail counts toward exit code 1.",
            "revenue_goal": f"Business target ${BUSINESS_GOAL_USD_PER_DAY:.0f}/day after-tax vs PostHog proxy.",
        },
        "summary": summary,
        "revenue_goal": build_revenue_goal_section(),
        "checks": [c.to_dict() for c in checks],
    }


def print_human_report(payload: dict[str, Any]) -> None:
    print()
    print("== Operational Verification Bundle ==")
    print(f"bundle_id: {payload['bundle_id']}")
    print(f"generated_at: {payload['generated_at']}")
    s = payload["summary"]
    print(
        f"checks: pass={s['pass']} fail={s['fail']} advisory_fail={s['advisory_fail']} "
        f"skip={s['skip']} unverified={s['unverified']} blocking_failures={s['blocking_failures']}"
    )
    rg = payload.get("revenue_goal") or {}
    print(
        f"revenue_goal: target=${rg.get('target_usd_per_day_after_tax')} "
        f"proxy_avg_day={rg.get('posthog_paywall_revenue_avg_usd_per_day')} "
        f"gap_day={rg.get('posthog_usd_gap_per_day_vs_target')} "
        f"(snapshot_stale={rg.get('snapshot_stale')})"
    )
    for item in payload["checks"]:
        marker = item["status"].upper()
        print(f"  [{marker}] {item['check_id']} (tier={item['tier']}, ground_truth={item['ground_truth']})")
        if item["status"] in {"fail", "advisory_fail", "skip", "unverified"}:
            ev = item.get("evidence") or {}
            brief = {k: ev[k] for k in list(ev)[:6]}
            print(f"         evidence: {json.dumps(brief, default=str)[:200]}")
    print("=====================================")
    print(f"JSON: {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--expected-version", default="", help="Override expected semver (default: latest GitHub release)")
    parser.add_argument(
        "--public-timeout",
        type=int,
        default=10,
        help="Single-poll public store check (tier2 advisory; default 10s)",
    )
    parser.add_argument("--json-out", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--no-write", action="store_true", help="Print only; do not write JSON file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    load_repo_dotenv(repo_root)

    try:
        expected = args.expected_version.strip() or read_github_latest_release_version(repo_root)
    except RuntimeError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    checks = run_all_checks(
        repo_root,
        expected_version=expected,
        public_timeout=args.public_timeout,
    )
    payload = build_bundle(repo_root, checks)
    print_human_report(payload)

    if not args.no_write:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    blocking = payload["summary"]["blocking_failures"]
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
