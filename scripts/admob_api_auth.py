"""Resolve AdMob API OAuth token + quota project for REST calls."""

from __future__ import annotations

import os
import subprocess
from typing import NamedTuple

ADMOB_READONLY_SCOPE = "https://www.googleapis.com/auth/admob.readonly"
DEFAULT_QUOTA_PROJECT = "random-timer-dist-new"


class AdmobAuth(NamedTuple):
    access_token: str
    source: str
    quota_project: str


def _sanitize_token(raw: str) -> str:
    t = raw.strip()
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    if (t.startswith("'") and t.endswith("'")) or (t.startswith('"') and t.endswith('"')):
        t = t[1:-1].strip()
    return t


def _adc_via_google_auth() -> AdmobAuth | None:
    try:
        import google.auth
        import google.auth.transport.requests
    except ImportError:
        return None

    try:
        creds, _ = google.auth.default(scopes=[ADMOB_READONLY_SCOPE])
        creds.refresh(google.auth.transport.requests.Request())
    except Exception:
        return None

    token = getattr(creds, "token", None)
    if not token:
        return None
    quota = (
        getattr(creds, "quota_project_id", None)
        or os.environ.get("ADMOB_QUOTA_PROJECT")
        or DEFAULT_QUOTA_PROJECT
    )
    return AdmobAuth(access_token=token, source="application-default-credentials", quota_project=quota)


def _adc_via_gcloud() -> AdmobAuth | None:
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "application-default", "print-access-token"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not token:
        return None
    quota = os.environ.get("ADMOB_QUOTA_PROJECT", DEFAULT_QUOTA_PROJECT)
    return AdmobAuth(access_token=token, source="gcloud-adc", quota_project=quota)


def resolve_admob_auth(explicit_token: str | None = None) -> AdmobAuth | None:
    if explicit_token:
        t = _sanitize_token(explicit_token)
        if t:
            quota = os.environ.get("ADMOB_QUOTA_PROJECT", DEFAULT_QUOTA_PROJECT)
            return AdmobAuth(access_token=t, source="--access-token", quota_project=quota)

    env = _sanitize_token(os.environ.get("ADMOB_ACCESS_TOKEN", ""))
    if env:
        quota = os.environ.get("ADMOB_QUOTA_PROJECT", DEFAULT_QUOTA_PROJECT)
        return AdmobAuth(access_token=env, source="ADMOB_ACCESS_TOKEN", quota_project=quota)

    return _adc_via_google_auth() or _adc_via_gcloud()
