#!/usr/bin/env python3
"""Unified Release Readiness Gate — single autonomous check before any release.

Combines ALL pre-release validation into one command:
  1. Store metadata completeness (Android + iOS)
  2. Version parity check
  3. PostHog WQTU health (warns if degraded)
  4. App Store Connect API readiness (if credentials available)
  5. Google Play API readiness (if credentials available)
  6. Privacy policy existence
  7. Screenshot inventory

Usage:
  python scripts/release_readiness_gate.py --platform both
  python scripts/release_readiness_gate.py --platform android --json

Exit codes: 0=ready, 1=not ready, 2=config error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


class Gate:
    def __init__(self, repo_root: Path, platform: str):
        self.repo = repo_root
        self.platform = platform
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: dict[str, dict] = {}

    def _record(self, name: str, passed: bool, detail: str = ""):
        self.checks[name] = {"passed": passed, "detail": detail}
        if not passed:
            self.errors.append(f"{name}: {detail}")

    def _warn(self, name: str, detail: str):
        self.checks[name] = {"passed": True, "detail": f"WARNING: {detail}"}
        self.warnings.append(f"{name}: {detail}")

    # ── Metadata checks ──────────────────────────────────────────────────

    def check_privacy_policy(self):
        pp = self.repo / "PRIVACY_POLICY.md"
        self._record("privacy_policy", pp.exists() and pp.stat().st_size > 0,
                      "PRIVACY_POLICY.md missing or empty" if not (pp.exists() and pp.stat().st_size > 0) else "present")

    def check_android_metadata(self):
        if self.platform not in ("android", "both"):
            return
        meta = self.repo / "native-android" / "fastlane" / "metadata" / "android" / "en-US"
        for f in ["title.txt", "short_description.txt", "full_description.txt"]:
            fp = meta / f
            if not fp.exists() or fp.stat().st_size == 0:
                self._record(f"android_{f}", False, f"missing or empty: {f}")
            else:
                self._record(f"android_{f}", True, "ok")

        # Screenshots
        shots_dir = meta / "images" / "phoneScreenshots"
        if shots_dir.exists():
            count = len(list(shots_dir.glob("*.png")))
            self._record("android_screenshots", count >= 3, f"{count} screenshots (need >= 3)")
        else:
            self._record("android_screenshots", False, "phoneScreenshots dir missing")

        # Title length
        title_file = meta / "title.txt"
        if title_file.exists():
            tlen = len(title_file.read_text(encoding="utf-8").strip())
            if tlen > 30:
                self._record("android_title_length", False, f"{tlen} chars (max 30)")

        # Short description length
        sd_file = meta / "short_description.txt"
        if sd_file.exists():
            sdlen = len(sd_file.read_text(encoding="utf-8").strip())
            if sdlen > 80:
                self._record("android_short_desc_length", False, f"{sdlen} chars (max 80)")

    def check_ios_metadata(self):
        if self.platform not in ("ios", "both"):
            return
        meta = self.repo / "native-ios" / "fastlane" / "metadata" / "en-US"
        for f in ["name.txt", "subtitle.txt", "description.txt", "keywords.txt", "release_notes.txt"]:
            fp = meta / f
            if not fp.exists() or fp.stat().st_size == 0:
                self._record(f"ios_{f}", False, f"missing or empty: {f}")
            else:
                self._record(f"ios_{f}", True, "ok")

        # Privacy URL
        pu = meta / "privacy_url.txt"
        if pu.exists():
            url = pu.read_text(encoding="utf-8").strip()
            self._record("ios_privacy_url", url.startswith("https://"),
                          f"must start with https:// (got: {url[:50]})" if not url.startswith("https://") else "ok")
        else:
            self._record("ios_privacy_url", False, "privacy_url.txt missing")

        # Keywords length
        kw = meta / "keywords.txt"
        if kw.exists():
            kwlen = len(kw.read_text(encoding="utf-8").strip())
            if kwlen > 100:
                self._record("ios_keywords_length", False, f"{kwlen} chars (max 100)")

    # ── Version checks ───────────────────────────────────────────────────

    def check_version_parity(self):
        android_version = ""
        ios_version = ""

        # Android version
        gradle = self.repo / "native-android" / "app" / "build.gradle.kts"
        if gradle.exists():
            text = gradle.read_text(encoding="utf-8")
            m = re.search(r'versionName\s*=\s*"([^"]+)"', text)
            if m:
                android_version = m.group(1)

        # iOS version
        pbx = self.repo / "native-ios" / "RandomTimer.xcodeproj" / "project.pbxproj"
        if pbx.exists():
            text = pbx.read_text(encoding="utf-8")
            m = re.search(r"MARKETING_VERSION = ([0-9.]+);", text)
            if m:
                ios_version = m.group(1)

        if android_version and ios_version:
            if android_version != ios_version:
                self._warn("version_parity", f"Android {android_version} != iOS {ios_version}")
            else:
                self.checks["version_parity"] = {"passed": True, "detail": f"v{android_version}"}
        else:
            self.checks["version_parity"] = {
                "passed": True,
                "detail": f"android={android_version or '?'} ios={ios_version or '?'}",
            }

    # ── PostHog WQTU health ──────────────────────────────────────────────

    def check_wqtu_health(self):
        wqtu_file = self.repo / "marketing" / "data" / "wqtu_health.json"
        if not wqtu_file.exists():
            # Try to generate it
            try:
                subprocess.run(
                    [sys.executable, str(self.repo / "scripts" / "wqtu_dashboard.py"),
                     "--repo-root", str(self.repo)],
                    capture_output=True, timeout=60,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        if wqtu_file.exists():
            try:
                data = json.loads(wqtu_file.read_text(encoding="utf-8"))
                wqtu = data.get("nsm", {}).get("wqtu", 0)
                status = data.get("status", "unknown")
                if status == "alert":
                    self._warn("wqtu_health", f"WQTU={wqtu} (below threshold)")
                else:
                    self.checks["wqtu_health"] = {"passed": True, "detail": f"WQTU={wqtu} status={status}"}
            except (json.JSONDecodeError, OSError):
                self._warn("wqtu_health", "could not parse wqtu_health.json")
        else:
            self._warn("wqtu_health", "no WQTU data available (PostHog credentials missing?)")

    # ── Store API access ─────────────────────────────────────────────────

    def check_store_api_access(self):
        check_script = self.repo / "scripts" / "check_store_access.py"
        if not check_script.exists():
            self.checks["store_api"] = {"passed": True, "detail": "check_store_access.py not found, skipped"}
            return

        if self.platform in ("android", "both"):
            gp_key = os.getenv("GOOGLE_PLAY_JSON_KEY", "")
            if gp_key:
                try:
                    r = subprocess.run(
                        [sys.executable, str(check_script), "--platform", "android"],
                        capture_output=True, text=True, timeout=30,
                    )
                    self._record("google_play_api", r.returncode == 0,
                                  r.stdout.strip()[-200:] if r.returncode == 0 else r.stderr.strip()[-200:])
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    self._warn("google_play_api", str(e))
            else:
                self.checks["google_play_api"] = {"passed": True, "detail": "no credentials, skipped"}

        if self.platform in ("ios", "both"):
            asc_key = os.getenv("APPSTORE_KEY_ID", "")
            if asc_key:
                try:
                    r = subprocess.run(
                        [sys.executable, str(check_script), "--platform", "ios"],
                        capture_output=True, text=True, timeout=30,
                    )
                    self._record("appstore_api", r.returncode == 0,
                                  r.stdout.strip()[-200:] if r.returncode == 0 else r.stderr.strip()[-200:])
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    self._warn("appstore_api", str(e))
            else:
                self.checks["appstore_api"] = {"passed": True, "detail": "no credentials, skipped"}

    # ── Run all ──────────────────────────────────────────────────────────

    def run_all(self) -> dict:
        self.check_privacy_policy()
        self.check_android_metadata()
        self.check_ios_metadata()
        self.check_version_parity()
        self.check_wqtu_health()
        self.check_store_api_access()

        passed = len(self.errors) == 0
        return {
            "ready": passed,
            "platform": self.platform,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
        }

    def print_report(self, result: dict):
        print("=" * 60)
        print("  RELEASE READINESS GATE")
        print("=" * 60)
        print(f"  Platform: {self.platform}")
        print()

        for name, check in result["checks"].items():
            icon = "✅" if check["passed"] else "❌"
            print(f"  {icon} {name}: {check['detail']}")

        if result["warnings"]:
            print()
            print("  ⚠️  Warnings:")
            for w in result["warnings"]:
                print(f"     {w}")

        if result["errors"]:
            print()
            print("  ❌ Blocking errors:")
            for e in result["errors"]:
                print(f"     {e}")

        print()
        if result["ready"]:
            print("  ✅ RELEASE READY")
        else:
            print("  ❌ NOT READY — fix errors above")
        print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Release Readiness Gate")
    parser.add_argument("--platform", choices=["android", "ios", "both"], default="both")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="JSON output only")
    parser.add_argument("--json-out", help="Write JSON result to file")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    gate = Gate(repo, args.platform)
    result = gate.run_all()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        gate.print_report(result)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
