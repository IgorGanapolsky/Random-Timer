"""Tests for ElevenLabs voice verification helpers (no live API calls)."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts import verify_elevenlabs_voices as vev

MALE_ALLOWED_ID = "2EiwWnXFnvU5JabPnv8n"
FEMALE_ALLOWED_ID = "EXAVITQu4vr4xnSDxMaL"
FORBIDDEN_ANGST_VOICE_ID = "DGzg6RaUqxGRTHSBjfgF"


@pytest.mark.parametrize("voice_id", [MALE_ALLOWED_ID, FEMALE_ALLOWED_ID, "sS5fXGlqomdGXa7mxBcy"])
def test_supported_voice_id_accepts_allowlisted(voice_id: str) -> None:
    assert vev._supported_voice_id(f"  {voice_id}  ") == voice_id


def test_supported_voice_id_rejects_unknown() -> None:
    with pytest.raises(RuntimeError, match="allowlist"):
        vev._supported_voice_id("not_in_list")


def test_supported_voice_id_rejects_angst_san_francisco_voice() -> None:
    with pytest.raises(RuntimeError, match="allowlist"):
        vev._supported_voice_id(FORBIDDEN_ANGST_VOICE_ID)


def test_text_to_speech_url() -> None:
    url = vev._text_to_speech_url(MALE_ALLOWED_ID)
    assert MALE_ALLOWED_ID in url
    assert vev.API_BASE_URL in url
    assert vev.OUTPUT_FORMAT in url


def test_load_json_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert vev._load_json(p) == {"a": 1}


def test_read_error_body_decodes_http_error() -> None:
    err = urllib.error.HTTPError(
        "https://example.com",
        401,
        "Unauthorized",
        {},
        io.BytesIO(b'{"detail":"nope"}'),
    )
    assert "nope" in vev._read_error_body(err)


def test_read_error_body_empty_on_read_failure() -> None:
    err = urllib.error.HTTPError("https://example.com", 500, "Err", {}, None)
    assert vev._read_error_body(err) == ""


def test_extract_error_status_from_detail_object() -> None:
    body = json.dumps({"detail": {"status": "payment_issue", "message": "billing"}})
    assert vev._extract_error_status(body) == "payment_issue"
    assert vev._is_controlled_provider_unavailable(body) is True


@patch("scripts.verify_elevenlabs_voices.urllib.request.urlopen")
def test_probe_synthesis_success(mock_urlopen: MagicMock) -> None:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = b"\x00" * 64
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    out = vev._probe_synthesis(
        api_key="k",
        voice_id=MALE_ALLOWED_ID,
        model_id="eleven_multilingual_v2",
        text="hi",
        label="t1",
    )
    assert out["label"] == "t1"
    assert out["audioBytes"] == 64
    assert out["voiceId"] == MALE_ALLOWED_ID


@patch("scripts.verify_elevenlabs_voices.urllib.request.urlopen")
def test_probe_synthesis_http_error(mock_urlopen: MagicMock) -> None:
    err = urllib.error.HTTPError(
        "https://api.elevenlabs.io",
        403,
        "Forbidden",
        {},
        io.BytesIO(b"quota"),
    )
    mock_urlopen.side_effect = err

    with pytest.raises(RuntimeError, match="HTTP 403"):
        vev._probe_synthesis(
            api_key="k",
            voice_id=MALE_ALLOWED_ID,
            model_id="m",
            text="t",
            label="x",
        )


@patch("scripts.verify_elevenlabs_voices.urllib.request.urlopen")
def test_probe_synthesis_payment_issue_is_controlled_skip(mock_urlopen: MagicMock) -> None:
    err = urllib.error.HTTPError(
        "https://api.elevenlabs.io",
        401,
        "Unauthorized",
        {},
        io.BytesIO(
            b'{"detail":{"status":"payment_issue","message":"Your subscription has a failed or incomplete payment."}}'
        ),
    )
    mock_urlopen.side_effect = err

    with pytest.raises(vev.ControlledProviderUnavailable, match="payment_issue"):
        vev._probe_synthesis(
            api_key="k",
            voice_id=MALE_ALLOWED_ID,
            model_id="m",
            text="t",
            label="x",
        )


@patch("scripts.verify_elevenlabs_voices.urllib.request.urlopen")
def test_probe_synthesis_empty_audio(mock_urlopen: MagicMock) -> None:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = b""
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with pytest.raises(RuntimeError, match="empty audio"):
        vev._probe_synthesis(
            api_key="k",
            voice_id=MALE_ALLOWED_ID,
            model_id="m",
            text="t",
            label="x",
        )


def test_main_missing_api_key(capsys: pytest.CaptureFixture[str]) -> None:
    with patch.object(sys, "argv", ["verify_elevenlabs_voices.py"]):
        with patch.dict("os.environ", {"ELEVENLABS_API_KEY": ""}, clear=False):
            assert vev.main() == 1
    err = capsys.readouterr().err
    assert "ELEVENLABS_API_KEY" in err


@patch("scripts.verify_elevenlabs_voices._probe_synthesis")
def test_main_success_json(mock_probe: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    contract = {
        "provider": "elevenlabs",
        "male": {
            "voiceId": MALE_ALLOWED_ID,
            "modelId": "eleven_multilingual_v2",
            "probeText": "a",
        },
        "female": {
            "modelId": "eleven_multilingual_v2",
            "primaryVoice": {
                "voiceId": FEMALE_ALLOWED_ID,
                "probeText": "b",
            },
            "fallbackVoices": [
                {"voiceId": "sS5fXGlqomdGXa7mxBcy", "probeText": "c"},
            ],
        },
    }
    cpath = tmp_path / "contract.json"
    cpath.write_text(json.dumps(contract), encoding="utf-8")

    def fake_probe(**kwargs: object) -> dict:
        return {"label": kwargs["label"], "stub": True}

    mock_probe.side_effect = fake_probe

    with patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"}):
        with patch("sys.argv", ["verify_elevenlabs_voices.py", "--contract", str(cpath)]):
            assert vev.main() == 0

    out = json.loads(capsys.readouterr().out)
    assert out["provider"] == "elevenlabs"
    assert len(out["verifiedProbes"]) == 3


@patch("scripts.verify_elevenlabs_voices._probe_synthesis")
def test_main_provider_unavailable_returns_controlled_skip(
    mock_probe: MagicMock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    contract = {
        "provider": "elevenlabs",
        "male": {
            "voiceId": MALE_ALLOWED_ID,
            "modelId": "eleven_multilingual_v2",
            "probeText": "a",
        },
        "female": {
            "modelId": "eleven_multilingual_v2",
            "primaryVoice": {
                "voiceId": FEMALE_ALLOWED_ID,
                "probeText": "b",
            },
            "fallbackVoices": [],
        },
    }
    cpath = tmp_path / "contract.json"
    cpath.write_text(json.dumps(contract), encoding="utf-8")
    mock_probe.side_effect = vev.ControlledProviderUnavailable("payment_issue with HTTP 401")

    with patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"}):
        with patch("sys.argv", ["verify_elevenlabs_voices.py", "--contract", str(cpath)]):
            assert vev.main() == 78

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "controlled_skip"
    assert "payment_issue" in out["reason"]
