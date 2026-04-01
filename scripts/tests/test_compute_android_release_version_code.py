from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest import mock

import pytest

from scripts import compute_android_release_version_code as calc


def test_read_gradle_version_code_extracts_integer(tmp_path: Path):
    gradle_file = tmp_path / "build.gradle.kts"
    gradle_file.write_text(
        """
        android {
            defaultConfig {
                versionCode = 1774400000
            }
        }
        """,
        encoding="utf-8",
    )

    assert calc._read_gradle_version_code(gradle_file) == 1774400000


def test_read_gradle_version_code_extracts_elvis_fallback_integer(tmp_path: Path):
    gradle_file = tmp_path / "build.gradle.kts"
    gradle_file.write_text(
        """
        android {
            defaultConfig {
                versionCode = ciVersionCode ?: 1774400000
            }
        }
        """,
        encoding="utf-8",
    )

    assert calc._read_gradle_version_code(gradle_file) == 1774400000


def test_extract_release_codes_skips_invalid_values():
    payload = {
        "releases": [
            {"versionCodes": ["12", "bad", 14]},
            {"versionCodes": [None, "15"]},
        ]
    }

    assert calc._extract_release_codes(payload) == [12, 14, 15]


def test_compute_next_version_code_prefers_higher_play_code():
    next_code = calc.compute_next_version_code(
        1774400000,
        {
            "production": [1773900000],
            "alpha": [1774400005],
            "beta": [],
            "internal": [1774399999],
        },
    )

    assert next_code == 1774400006


def test_compute_next_version_code_prefers_higher_gradle_code_when_tracks_lower():
    next_code = calc.compute_next_version_code(
        1774400000,
        {
            "production": [1773900000],
            "alpha": [1773899999],
        },
    )

    assert next_code == 1774400001


def test_fetch_existing_track_codes_reads_each_track_and_cleans_up():
    events: list[tuple[str, str | None, int | None]] = []

    class _Tracks:
        def get(self, *, packageName: str, editId: str, track: str):
            events.append(("get", track, None))

            class _Request:
                def execute(self_nonlocal, num_retries=None):
                    events.append(("execute", track, num_retries))
                    payloads = {
                        "production": {"releases": [{"versionCodes": ["100", "101"]}]},
                        "beta": {"releases": []},
                    }
                    return payloads[track]

            return _Request()

    class _Edits:
        def insert(self, *, body: dict, packageName: str):
            events.append(("insert", None, None))

            class _Request:
                def execute(self_nonlocal, num_retries=None):
                    events.append(("execute", "insert", num_retries))
                    return {"id": "edit-1"}

            return _Request()

        def tracks(self):
            return _Tracks()

        def delete(self, *, packageName: str, editId: str):
            events.append(("delete", None, None))

            class _Request:
                def execute(self_nonlocal, num_retries=None):
                    events.append(("execute", "delete", num_retries))
                    return {}

            return _Request()

    class _Service:
        def edits(self):
            return _Edits()

    result = calc._fetch_existing_track_codes(_Service(), "pkg", ["production", "beta"], request_retries=5)

    assert result == {"production": [100, 101], "beta": []}
    assert events == [
        ("insert", None, None),
        ("execute", "insert", 5),
        ("get", "production", None),
        ("execute", "production", 5),
        ("get", "beta", None),
        ("execute", "beta", 5),
        ("delete", None, None),
        ("execute", "delete", 5),
    ]


def test_load_play_service_uses_authorized_http_timeout(tmp_path: Path):
    """Patch the real google-auth entry point, but keep sys.modules stubs for optional Play HTTP deps."""
    service_account = tmp_path / "play.json"
    service_account.write_text("{}", encoding="utf-8")
    observed: dict[str, object] = {}

    class _Credentials:
        pass

    def _authorized_http(credentials, http):
        observed["authorized_http_credentials"] = credentials
        observed["authorized_http_http"] = http
        return "authorized-http"

    def _http_factory(timeout=None):
        observed["http_timeout"] = timeout
        return {"timeout": timeout}

    def _build(api_name, api_version, *, credentials, http, cache_discovery):
        observed["build_args"] = {
            "api_name": api_name,
            "api_version": api_version,
            "credentials": credentials,
            "http": http,
            "cache_discovery": cache_discovery,
        }
        return "service"

    creds_path = str(service_account)
    expected_scopes = ["https://www.googleapis.com/auth/androidpublisher"]

    monkeypatch_modules = {
        "google_auth_httplib2": types.SimpleNamespace(AuthorizedHttp=_authorized_http),
        "googleapiclient.discovery": types.SimpleNamespace(build=_build),
        "httplib2": types.SimpleNamespace(Http=_http_factory),
    }
    with (
        mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            autospec=True,
        ) as mock_from_file,
        mock.patch.dict(sys.modules, monkeypatch_modules),
    ):
        mock_from_file.return_value = _Credentials()
        result = calc._load_play_service(service_account, timeout_seconds=240)

    assert result == "service"
    mock_from_file.assert_called_once_with(creds_path, scopes=expected_scopes)
    assert observed["http_timeout"] == 240
    assert observed["build_args"] == {
        "api_name": "androidpublisher",
        "api_version": "v3",
        "credentials": observed["authorized_http_credentials"],
        "http": "authorized-http",
        "cache_discovery": False,
    }


def test_main_writes_json_output(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    gradle_file = tmp_path / "build.gradle.kts"
    gradle_file.write_text("versionCode = 1774400000", encoding="utf-8")
    service_account = tmp_path / "play.json"
    service_account.write_text("{}", encoding="utf-8")
    json_output = tmp_path / "result.json"

    monkeypatch.setattr(calc, "_load_play_service", lambda _path, timeout_seconds=calc.DEFAULT_HTTP_TIMEOUT_SECONDS: object())
    monkeypatch.setattr(
        calc,
        "_fetch_existing_track_codes",
        lambda _service, _package, _tracks, request_retries=calc.DEFAULT_REQUEST_RETRIES: {"production": [1774400002], "beta": []},
    )
    monkeypatch.setattr(
        calc,
        "_parse_args",
        lambda: type(
            "Args",
            (),
            {
                "service_account_json": str(service_account),
                "package": "com.iganapolsky.randomtimer",
                "gradle_file": str(gradle_file),
                "tracks": "production,beta",
                "timeout_seconds": 240,
                "request_retries": 5,
                "json_output": str(json_output),
            },
        )(),
    )

    assert calc.main() == 0
    assert capsys.readouterr().out.strip() == "1774400003"
    assert '"next_version_code": 1774400003' in json_output.read_text(encoding="utf-8")
