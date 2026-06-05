from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from unittest import mock

import pytest

from scripts import prune_actions_artifacts as paa


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["gh"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_parse_github_ts_accepts_z_suffix():
    parsed = paa.parse_github_ts("2026-06-01T12:34:56Z")
    assert parsed == datetime(2026, 6, 1, 12, 34, 56, tzinfo=timezone.utc)


def test_is_rate_limited_detects_403_and_phrases():
    assert paa._is_rate_limited(_completed(1, stderr="HTTP 403: rate limit exceeded"))
    assert paa._is_rate_limited(_completed(1, stderr="secondary rate limit"))
    assert not paa._is_rate_limited(_completed(0))


def test_retry_after_seconds_parses_header_then_exponential_backoff():
    with_retry = _completed(1, stderr="retry after: 42")
    assert paa._retry_after_seconds(with_retry, attempt=0) == 42.0
    assert paa._retry_after_seconds(_completed(1), attempt=2) == min(30 * (2**2), 300)


def test_run_gh_with_retry_sleeps_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_run(args):
        calls["n"] += 1
        if calls["n"] == 1:
            return _completed(1, stderr="403 rate limit")
        return _completed(0, stdout="{}")

    monkeypatch.setattr(paa, "_run_gh", fake_run)
    monkeypatch.setattr(paa.time, "sleep", lambda _s: None)

    result = paa._run_gh_with_retry(["api", "repos/x"], label="test")
    assert result.returncode == 0
    assert calls["n"] == 2


def test_gh_api_json_non_paginate_returns_artifacts_and_total_count():
    payload = {"artifacts": [{"id": 1}], "total_count": 5}
    with mock.patch.object(paa, "_run_gh_with_retry", return_value=_completed(0, stdout=json.dumps(payload))):
        artifacts, total_count, complete = paa.gh_api_json("repos/o/r/actions/artifacts")

    assert artifacts == [{"id": 1}]
    assert total_count == 5
    assert complete is True


def test_paginate_artifacts_stops_on_rate_limit_with_resume_hint():
    page1 = {"artifacts": [{"id": i} for i in range(100)], "total_count": 250}
    rate_limited = _completed(1, stderr="403 rate limit")

    with mock.patch.object(
        paa,
        "_run_gh_with_retry",
        side_effect=[_completed(0, stdout=json.dumps(page1)), rate_limited],
    ):
        artifacts, total_count, complete = paa._paginate_artifacts("repos/o/r/actions/artifacts", start_page=1)

    assert len(artifacts) == 100
    assert total_count == 250
    assert complete is False


def test_delete_artifact_raises_rate_limited_message():
    with mock.patch.object(
        paa,
        "_run_gh_with_retry",
        return_value=_completed(1, stderr="403 rate limit"),
    ):
        with pytest.raises(RuntimeError, match="rate limited deleting artifact 99"):
            paa.delete_artifact("owner/repo", 99)


def test_paginate_artifacts_completes_multi_page_list():
    page1 = {"artifacts": [{"id": i} for i in range(100)], "total_count": 120}
    page2 = {"artifacts": [{"id": 100}, {"id": 101}]}

    with mock.patch.object(
        paa,
        "_run_gh_with_retry",
        side_effect=[
            _completed(0, stdout=json.dumps(page1)),
            _completed(0, stdout=json.dumps(page2)),
        ],
    ):
        artifacts, total_count, complete = paa._paginate_artifacts("repos/o/r/actions/artifacts", start_page=2)

    assert len(artifacts) == 102
    assert total_count == 120
    assert complete is True


def test_gh_api_json_raises_on_nonzero_exit():
    with mock.patch.object(paa, "_run_gh_with_retry", return_value=_completed(1, stderr="boom")):
        with pytest.raises(RuntimeError, match="boom"):
            paa.gh_api_json("repos/o/r/actions/artifacts")


def test_delete_artifact_raises_generic_failure():
    with mock.patch.object(
        paa,
        "_run_gh_with_retry",
        return_value=_completed(1, stderr="permission denied"),
    ):
        with pytest.raises(RuntimeError, match="delete artifact 7 failed"):
            paa.delete_artifact("owner/repo", 7)
