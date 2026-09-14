"""Unit tests for monthly audio pack helpers (no network)."""

from __future__ import annotations


def test_preview_url_prefers_hq() -> None:
    from scripts import generate_monthly_audio_pack as gmap

    assert (
        gmap._preview_url(
            {"previews": {"preview-hq-mp3": "https://hq", "preview-lq-mp3": "https://lq"}}
        )
        == "https://hq"
    )


def test_preview_url_falls_back_to_lq() -> None:
    from scripts import generate_monthly_audio_pack as gmap

    assert gmap._preview_url({"previews": {"preview-lq-mp3": "https://lq"}}) == "https://lq"


def test_preview_url_missing() -> None:
    from scripts import generate_monthly_audio_pack as gmap

    assert gmap._preview_url({}) is None
    assert gmap._preview_url({"previews": {}}) is None


def test_parse_args_dry_run(monkeypatch) -> None:
    from scripts import generate_monthly_audio_pack as gmap

    monkeypatch.setattr("sys.argv", ["generate_monthly_audio_pack.py", "--dry-run", "--skip-voice"])
    ns = gmap._parse_args()
    assert ns.dry_run is True
    assert ns.skip_voice is True
