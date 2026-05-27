from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import verify_public_store_versions as vps


class _Resp:
    def __init__(self, status_code: int, payload: dict | None = None, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_reads_ios_and_android_versions(tmp_path: Path):
    ios_project = tmp_path / "native-ios/RandomTimer.xcodeproj"
    ios_project.mkdir(parents=True)
    (ios_project / "project.pbxproj").write_text(
        "MARKETING_VERSION = 1.3.20;\nMARKETING_VERSION = 1.3.20;\n",
        encoding="utf-8",
    )
    android_dir = tmp_path / "native-android/app"
    android_dir.mkdir(parents=True)
    (android_dir / "build.gradle.kts").write_text('versionName = "1.3.20"\n', encoding="utf-8")

    assert vps.read_ios_version(tmp_path) == "1.3.20"
    assert vps.read_android_version(tmp_path) == "1.3.20"


def test_app_store_public_version_passes(monkeypatch):
    monkeypatch.setattr(
        vps.requests,
        "get",
        lambda *_args, **_kwargs: _Resp(
            200,
            {
                "resultCount": 1,
                "results": [
                    {
                        "version": "1.3.20",
                        "currentVersionReleaseDate": "2026-04-14T12:00:00Z",
                    }
                ],
            },
            {"date": "Tue, 14 Apr 2026 20:00:00 GMT"},
        ),
    )

    result = vps.verify_app_store_public_version("6758355312", "1.3.20")

    assert result.passed is True
    assert result.status == "PUBLIC"
    assert result.observed_version == "1.3.20"
    assert "release_date=2026-04-14T12:00:00Z" in result.details
    assert "ios_semantics=itunes_lookup_public_version_field" in result.details


def test_app_store_public_version_mismatch(monkeypatch):
    monkeypatch.setattr(
        vps.requests,
        "get",
        lambda *_args, **_kwargs: _Resp(
            200,
            {"results": [{"version": "1.3.19"}]},
            {"date": "Tue, 14 Apr 2026 20:00:00 GMT"},
        ),
    )

    result = vps.verify_app_store_public_version("6758355312", "1.3.20")

    assert result.passed is False
    assert result.status == "VERSION_MISMATCH"
    assert result.observed_version == "1.3.19"
    assert result.expected_version == "1.3.20"


def test_play_public_version_uses_existing_play_verifier(monkeypatch):
    monkeypatch.setattr(
        vps.play,
        "verify_public_listing",
        lambda url, expected_version: vps.play.PublicListingResult(
            True,
            "PUBLIC",
            f"HTTP 200 public_version=1.3.20 expected_version={expected_version} url={url}",
        ),
    )

    result = vps.verify_play_public_version("com.iganapolsky.randomtimer", "1.3.20")

    assert result.passed is True
    assert result.status == "PUBLIC"
    assert result.observed_version == "1.3.20"


def test_poll_until_public_times_out_without_converting_version_mismatch(monkeypatch):
    monkeypatch.setattr(vps.time, "sleep", lambda *_args, **_kwargs: None)

    def verify_once():
        return [
            vps.StoreVersionResult(
                "ios",
                False,
                "VERSION_MISMATCH",
                "https://itunes.apple.com/lookup?id=1",
                "1.3.20",
                "1.3.19",
                "public_version=1.3.19",
            )
        ]

    results = vps.poll_until_public(verify_once, timeout=0, poll_interval=1)

    assert results[0].status == "VERSION_MISMATCH"
    assert "timed out after 0s" in results[0].details


def test_read_github_latest_release_version_strips_v_prefix(monkeypatch):
    monkeypatch.setattr(
        vps.subprocess,
        "run",
        lambda *_a, **_kw: subprocess.CompletedProcess(
            ["gh"],
            0,
            stdout='{"tagName":"v1.3.21"}\n',
            stderr="",
        ),
    )

    assert vps.read_github_latest_release_version(Path("/tmp")) == "1.3.21"


def test_read_github_latest_release_version_requires_gh(monkeypatch):
    def boom(*_a, **_kw):
        raise FileNotFoundError()

    monkeypatch.setattr(vps.subprocess, "run", boom)

    with pytest.raises(RuntimeError, match="gh CLI is required"):
        vps.read_github_latest_release_version(Path("/tmp"))


def test_resolve_expected_versions_uses_repo_sources(tmp_path: Path):
    ios_project = tmp_path / "native-ios/RandomTimer.xcodeproj"
    ios_project.mkdir(parents=True)
    (ios_project / "project.pbxproj").write_text(
        "MARKETING_VERSION = 1.3.20;\nMARKETING_VERSION = 1.3.20;\n",
        encoding="utf-8",
    )
    android_dir = tmp_path / "native-android/app"
    android_dir.mkdir(parents=True)
    (android_dir / "build.gradle.kts").write_text('versionName = "1.3.19"\n', encoding="utf-8")

    ios_e, android_e, label = vps.resolve_expected_versions(
        platform="both",
        expected_version="",
        ios_expected_version="",
        android_expected_version="",
        expected_source="repo",
        repo_root=tmp_path,
    )

    assert label == "repo_sources"
    assert ios_e == "1.3.20"
    assert android_e == "1.3.19"


def test_resolve_expected_versions_uses_github_release(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(vps, "read_github_latest_release_version", lambda _root: "1.3.18")

    ios_e, android_e, label = vps.resolve_expected_versions(
        platform="both",
        expected_version="",
        ios_expected_version="",
        android_expected_version="",
        expected_source="github_latest_release",
        repo_root=tmp_path,
    )

    assert label == "github_latest_release"
    assert ios_e == "1.3.18"
    assert android_e == "1.3.18"


def test_resolve_expected_versions_explicit_fills_missing_from_repo(tmp_path: Path):
    ios_project = tmp_path / "native-ios/RandomTimer.xcodeproj"
    ios_project.mkdir(parents=True)
    (ios_project / "project.pbxproj").write_text(
        "MARKETING_VERSION = 9.9.9;\nMARKETING_VERSION = 9.9.9;\n",
        encoding="utf-8",
    )
    android_dir = tmp_path / "native-android/app"
    android_dir.mkdir(parents=True)
    (android_dir / "build.gradle.kts").write_text('versionName = "8.8.8"\n', encoding="utf-8")

    ios_e, android_e, label = vps.resolve_expected_versions(
        platform="both",
        expected_version="",
        ios_expected_version="1.0.0",
        android_expected_version="",
        expected_source="github_latest_release",
        repo_root=tmp_path,
    )

    assert label == "explicit_cli"
    assert ios_e == "1.0.0"
    assert android_e == "8.8.8"


def test_poll_until_public_fail_fast_on_stable_mismatch(monkeypatch):
    mismatch = vps.StoreVersionResult(
        "ios",
        False,
        "VERSION_MISMATCH",
        "https://apps.apple.com/app/id1",
        "1.3.20",
        "1.3.19",
        "mismatch",
    )
    calls = {"n": 0}

    def verify_once():
        calls["n"] += 1
        return [mismatch]

    monkeypatch.setattr(vps.time, "sleep", lambda *_a, **_k: None)
    results = vps.poll_until_public(
        verify_once,
        timeout=60,
        poll_interval=1,
        fail_fast_on_stable_mismatch=True,
    )
    assert calls["n"] == 2
    assert results[0].status == "VERSION_MISMATCH_STABLE"
    assert "stable mismatch" in results[0].details
