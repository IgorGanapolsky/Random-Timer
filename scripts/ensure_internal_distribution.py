#!/usr/bin/env python3
"""Ensure internal TestFlight/Firebase builds are actually visible to testers."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
_ASC_DIR = str(Path(__file__).resolve().parent / "asc")
for _p in (_SCRIPTS_DIR, _ASC_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from asc_client import ASCClient, AscClientError
from pem_env import load_google_play_service_account_dict
from repo_dotenv import load_repo_dotenv

load_repo_dotenv(Path(__file__).resolve().parent.parent)

IOS_BUNDLE_ID = "com.igorganapolsky.randomtimer"
FIREBASE_SCOPE = ("https://www.googleapis.com/auth/cloud-platform",)


def _csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _error(details: str) -> dict[str, Any]:
    return {"passed": False, "status": "ERROR", "details": details}


class TestFlightInternalDistributor:
    def __init__(self, bundle_id: str = IOS_BUNDLE_ID, client: ASCClient | None = None):
        self.bundle_id = bundle_id
        self.client = client or ASCClient.from_env()

    def _get_app_id(self) -> str:
        apps = self.client.get("/apps", params={"filter[bundleId]": self.bundle_id}).get("data", [])
        if not apps:
            raise RuntimeError(f"No App Store Connect app found for bundle id '{self.bundle_id}'")
        return apps[0]["id"]

    def _groups_for_app(self, app_id: str) -> dict[str, dict[str, Any]]:
        groups = self.client.get_all(f"/apps/{app_id}/betaGroups", params={"limit": "200"})
        return {group["attributes"]["name"]: group for group in groups}

    def _latest_build_for_version(self, app_id: str, marketing_version: str) -> dict[str, Any]:
        payload = self.client.get(
            "/builds",
            params={
                "filter[app]": app_id,
                "include": "preReleaseVersion",
                "sort": "-uploadedDate",
                "limit": 50,
                "fields[builds]": "version,processingState,uploadedDate,preReleaseVersion",
                "fields[preReleaseVersions]": "version",
            },
        )
        pre_release_versions = {
            item["id"]: item.get("attributes", {}).get("version")
            for item in payload.get("included", [])
            if item.get("type") == "preReleaseVersions"
        }
        for build in payload.get("data", []):
            pre_rel = (
                build.get("relationships", {})
                .get("preReleaseVersion", {})
                .get("data")
            )
            pre_rel_id = pre_rel.get("id") if isinstance(pre_rel, dict) else None
            if pre_release_versions.get(pre_rel_id) == marketing_version:
                return build
        raise RuntimeError(f"No TestFlight build found for marketing version {marketing_version}")

    def _ensure_build_in_group(self, group_id: str, build_id: str) -> None:
        try:
            self.client.request(
                "POST",
                f"/betaGroups/{group_id}/relationships/builds",
                payload={"data": [{"type": "builds", "id": build_id}]},
            )
        except AscClientError as exc:
            if "HTTP 409" not in str(exc):
                raise

    def _group_build_ids(self, group_id: str) -> set[str]:
        builds = self.client.get_all(f"/betaGroups/{group_id}/builds", params={"limit": "200"})
        return {build["id"] for build in builds}

    def _group_tester_emails(self, group_id: str) -> set[str]:
        testers = self.client.get_all(f"/betaGroups/{group_id}/betaTesters", params={"limit": "200"})
        return {
            (tester.get("attributes", {}).get("email") or "").strip().lower()
            for tester in testers
            if tester.get("attributes", {}).get("email")
        }

    def ensure(self, *, marketing_version: str, groups: list[str], required_testers: list[str]) -> dict[str, Any]:
        try:
            app_id = self._get_app_id()
            build = self._latest_build_for_version(app_id, marketing_version)
            build_id = build["id"]
            attrs = build.get("attributes", {})
            build_number = str(attrs.get("version", "?"))
            processing_state = attrs.get("processingState", "UNKNOWN")
            app_groups = self._groups_for_app(app_id)

            missing_groups: list[str] = []
            missing_tester_details: list[str] = []
            verified_groups: list[str] = []

            for group_name in groups:
                group = app_groups.get(group_name)
                if not group:
                    missing_groups.append(group_name)
                    continue
                group_id = group["id"]
                is_internal_group = bool(group.get("attributes", {}).get("isInternalGroup"))
                if not is_internal_group:
                    self._ensure_build_in_group(group_id, build_id)
                if build_id not in self._group_build_ids(group_id):
                    return _error(
                        f"Build {build_number} for {marketing_version} is missing from TestFlight group '{group_name}'"
                    )
                testers = self._group_tester_emails(group_id)
                missing = [email for email in required_testers if email.lower() not in testers]
                if missing:
                    missing_tester_details.append(f"{group_name}: {', '.join(missing)}")
                verified_groups.append(group_name)

            if missing_groups:
                return _error("Missing TestFlight groups: " + ", ".join(missing_groups))
            if missing_tester_details:
                return _error(
                    "Required internal TestFlight testers missing from group membership: "
                    + "; ".join(missing_tester_details)
                )
            if processing_state != "VALID":
                return _error(
                    f"Latest TestFlight build {build_number} for {marketing_version} is not VALID (processingState={processing_state})"
                )

            return {
                "passed": True,
                "status": "VISIBLE",
                "details": (
                    f"TestFlight {marketing_version} build {build_number} is attached to groups "
                    f"{', '.join(verified_groups)} and required tester membership is present."
                ),
            }
        except Exception as exc:
            return _error(f"TestFlight internal distribution check failed: {exc}")


class FirebaseInternalDistributor:
    def __init__(
        self,
        *,
        app_id: str,
        service_account_key: str | None = None,
        requests_module: Any | None = None,
    ):
        self.app_id = app_id
        self.project_number = self._project_number_from_app_id(app_id)
        self._service_account_key = (
            service_account_key
            or os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
            or os.environ.get("GOOGLE_PLAY_JSON_KEY", "")
        )
        self._requests = requests_module
        self._token: str | None = None

    @staticmethod
    def _project_number_from_app_id(app_id: str) -> str:
        parts = app_id.split(":")
        if len(parts) < 2 or not parts[1].isdigit():
            raise RuntimeError(f"Could not parse project number from Firebase app id '{app_id}'")
        return parts[1]

    def _get_token(self) -> str:
        if self._token:
            return self._token
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
        except ImportError as exc:
            raise RuntimeError(
                "Missing google-auth dependencies. Install: pip install google-auth requests"
            ) from exc

        info = load_google_play_service_account_dict(self._service_account_key)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=list(FIREBASE_SCOPE),
        )
        credentials.refresh(Request())
        self._token = credentials.token
        return self._token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        requests_module = self._requests
        if requests_module is None:
            try:
                import requests as requests_module  # type: ignore
            except ImportError as exc:
                raise RuntimeError("Missing requests. Install: pip install requests") from exc

        response = requests_module.request(
            method.upper(),
            f"https://firebaseappdistribution.googleapis.com{path}",
            headers={
                "Authorization": f"Bearer {self._get_token()}",
                "Content-Type": "application/json",
            },
            params=params or {},
            json=payload,
            timeout=30,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"{method.upper()} {path} failed: HTTP {response.status_code} {response.text[:1000]}")
        return response.json() if getattr(response, "text", "") else {}

    def _list_releases(self) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            f"/v1/projects/{self.project_number}/apps/{quote(self.app_id, safe=':')}/releases",
            params={"pageSize": 50},
        )
        return payload.get("releases", [])

    def _find_release(self, *, build_version: str | None, display_version: str | None) -> dict[str, Any]:
        releases = self._list_releases()
        if build_version:
            releases = [release for release in releases if str(release.get("buildVersion", "")) == str(build_version)]
        if display_version:
            releases = [release for release in releases if str(release.get("displayVersion", "")) == str(display_version)]
        if not releases:
            raise RuntimeError(
                f"No Firebase release found for app {self.app_id}"
                + (f" buildVersion={build_version}" if build_version else "")
                + (f" displayVersion={display_version}" if display_version else "")
            )
        return max(releases, key=lambda release: release.get("createTime", ""))

    def _distribute_release(self, release_name: str, *, tester_emails: list[str], group_aliases: list[str]) -> None:
        if not tester_emails and not group_aliases:
            return
        self._request(
            "POST",
            f"/v1/{quote(release_name, safe='/:')}:distribute",
            payload={"testerEmails": tester_emails, "groupAliases": group_aliases},
        )

    def _list_testers(self) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            f"/v1/projects/{self.project_number}/testers",
            params={"pageSize": 200},
        )
        return payload.get("testers", [])

    def _get_group(self, alias: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/projects/{self.project_number}/groups/{quote(alias, safe='')}")

    def ensure(
        self,
        *,
        build_version: str | None,
        display_version: str | None,
        group_aliases: list[str],
        tester_emails: list[str],
        required_testers: list[str],
    ) -> dict[str, Any]:
        try:
            release = self._find_release(build_version=build_version, display_version=display_version)
            if not tester_emails and not group_aliases:
                return _error(
                    "Firebase release found, but no tester emails or group aliases were provided for visibility verification"
                )

            direct_tester_emails = {email.strip().lower() for email in tester_emails if email.strip()}
            self._distribute_release(
                release["name"],
                tester_emails=tester_emails,
                group_aliases=group_aliases,
            )

            project_testers = {
                (tester.get("email") or "").strip().lower()
                for tester in self._list_testers()
                if tester.get("email")
            }
            missing_project_testers = [email for email in required_testers if email.lower() not in project_testers]
            missing_undistributed_testers = [
                email
                for email in missing_project_testers
                if email.lower() not in direct_tester_emails
            ]
            if missing_undistributed_testers:
                return _error(
                    "Required Firebase testers are missing from the project tester list "
                    f"and were not included in direct distribution (count={len(missing_undistributed_testers)})"
                )

            group_summaries: list[str] = []
            for alias in group_aliases:
                group = self._get_group(alias)
                tester_count = int(group.get("testerCount", 0))
                release_count = int(group.get("releaseCount", 0))
                if tester_count <= 0:
                    return _error(f"Firebase group '{alias}' has no testers")
                if release_count <= 0:
                    return _error(f"Firebase group '{alias}' has no accessible releases")
                group_summaries.append(f"{alias}(testers={tester_count}, releases={release_count})")

            direct_summary = (
                f"direct tester distribution accepted for {len(direct_tester_emails)} tester(s)"
                if direct_tester_emails
                else "no direct tester emails requested"
            )
            propagation_summary = (
                f"; project tester list pending for {len(missing_project_testers)} required tester(s)"
                if missing_project_testers
                else ""
            )
            return {
                "passed": True,
                "status": "VISIBLE",
                "details": (
                    f"Firebase release {release.get('displayVersion', '?')} ({release.get('buildVersion', '?')}) "
                    f"is distributed. Firebase distribute API accepted the release; {direct_summary}. "
                    f"Groups verified: {', '.join(group_summaries) if group_summaries else 'none'}"
                    f"{propagation_summary}."
                ),
            }
        except Exception as exc:
            return _error(f"Firebase internal distribution check failed: {exc}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure internal TestFlight/Firebase visibility before signoff.")
    parser.add_argument("--platform", choices=["ios", "firebase", "both"], required=True)
    parser.add_argument("--ios-version", default="")
    parser.add_argument("--ios-groups", default="")
    parser.add_argument("--ios-required-testers", default="")
    parser.add_argument("--firebase-app-id", default=os.environ.get("FIREBASE_ANDROID_APP_ID", ""))
    parser.add_argument("--firebase-build-version", default="")
    parser.add_argument("--firebase-display-version", default="")
    parser.add_argument("--firebase-group-aliases", default="")
    parser.add_argument("--firebase-tester-emails", default="")
    parser.add_argument("--firebase-required-testers", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    results: list[dict[str, Any]] = []

    if args.platform in {"ios", "both"}:
        if not args.ios_version:
            print("❌ --ios-version is required for iOS checks", file=sys.stderr)
            return 2
        results.append(
            {"platform": "iOS", **TestFlightInternalDistributor().ensure(
                marketing_version=args.ios_version,
                groups=_csv(args.ios_groups),
                required_testers=[email.lower() for email in _csv(args.ios_required_testers)],
            )}
        )

    if args.platform in {"firebase", "both"}:
        if not args.firebase_app_id:
            print("❌ --firebase-app-id is required for Firebase checks", file=sys.stderr)
            return 2
        results.append(
            {"platform": "Firebase", **FirebaseInternalDistributor(app_id=args.firebase_app_id).ensure(
                build_version=args.firebase_build_version or None,
                display_version=args.firebase_display_version or None,
                group_aliases=_csv(args.firebase_group_aliases),
                tester_emails=[email.lower() for email in _csv(args.firebase_tester_emails)],
                required_testers=[email.lower() for email in _csv(args.firebase_required_testers or args.firebase_tester_emails)],
            )}
        )

    all_passed = True
    for result in results:
        icon = "✅" if result["passed"] else "❌"
        print(f"{icon} {result['platform']}: {result['status']} — {result['details']}")
        all_passed = all_passed and result["passed"]
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
