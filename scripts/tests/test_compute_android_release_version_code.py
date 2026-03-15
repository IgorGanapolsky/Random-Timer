from __future__ import annotations

from pathlib import Path

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


def test_read_gradle_version_code_returns_none_for_dynamic_expression(tmp_path: Path):
    gradle_file = tmp_path / "build.gradle.kts"
    gradle_file.write_text("versionCode = ciVersionCode ?: 11", encoding="utf-8")

    assert calc._read_gradle_version_code(gradle_file) is None


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
        minimum_floor=1773596673,
    )

    assert next_code == 1774400006


def test_compute_next_version_code_prefers_higher_gradle_code_when_tracks_lower():
    next_code = calc.compute_next_version_code(
        1774400000,
        {
            "production": [1773900000],
            "alpha": [1773899999],
        },
        minimum_floor=1773596673,
    )

    assert next_code == 1774400001


def test_compute_next_version_code_uses_time_floor_when_gradle_is_dynamic():
    next_code = calc.compute_next_version_code(
        None,
        {
            "production": [1773900000],
            "alpha": [],
        },
        minimum_floor=1773901000,
    )

    assert next_code == 1773901001


def test_fetch_existing_track_codes_reads_each_track_and_cleans_up():
    events: list[tuple[str, str | None]] = []

    class _Tracks:
        def get(self, *, packageName: str, editId: str, track: str):
            events.append(("get", track))

            class _Request:
                def execute(self_nonlocal):
                    payloads = {
                        "production": {"releases": [{"versionCodes": ["100", "101"]}]},
                        "beta": {"releases": []},
                    }
                    return payloads[track]

            return _Request()

    class _Edits:
        def insert(self, *, body: dict, packageName: str):
            events.append(("insert", None))

            class _Request:
                def execute(self_nonlocal):
                    return {"id": "edit-1"}

            return _Request()

        def tracks(self):
            return _Tracks()

        def delete(self, *, packageName: str, editId: str):
            events.append(("delete", None))

            class _Request:
                def execute(self_nonlocal):
                    return {}

            return _Request()

    class _Service:
        def edits(self):
            return _Edits()

    result = calc._fetch_existing_track_codes(_Service(), "pkg", ["production", "beta"])

    assert result == {"production": [100, 101], "beta": []}
    assert events == [
        ("insert", None),
        ("get", "production"),
        ("get", "beta"),
        ("delete", None),
    ]


def test_main_writes_json_output(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    gradle_file = tmp_path / "build.gradle.kts"
    gradle_file.write_text("versionCode = ciVersionCode ?: 11", encoding="utf-8")
    service_account = tmp_path / "play.json"
    service_account.write_text("{}", encoding="utf-8")
    json_output = tmp_path / "result.json"

    monkeypatch.setattr(calc, "_load_play_service", lambda _: object())
    monkeypatch.setattr(
        calc,
        "_fetch_existing_track_codes",
        lambda _service, _package, _tracks: {"production": [1774400002], "beta": []},
    )
    monkeypatch.setattr(calc.time, "time", lambda: 1774400002)
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
                "json_output": str(json_output),
            },
        )(),
    )

    assert calc.main() == 0
    assert capsys.readouterr().out.strip() == "1774400003"
    assert '"next_version_code": 1774400003' in json_output.read_text(encoding="utf-8")
