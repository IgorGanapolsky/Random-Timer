from pathlib import Path
from unittest.mock import Mock

from scripts import sync_android_metadata as syncer


def test_locale_listing_reads_available_fields(tmp_path: Path) -> None:
    locale_dir = tmp_path / "en-US"
    locale_dir.mkdir(parents=True, exist_ok=True)
    (locale_dir / "title.txt").write_text("Random Tactical Timer", encoding="utf-8")
    (locale_dir / "short_description.txt").write_text("Train reaction honestly.", encoding="utf-8")

    listing = syncer._locale_listing(locale_dir)

    assert listing == {
        "title": "Random Tactical Timer",
        "shortDescription": "Train reaction honestly.",
    }


def test_update_release_notes_updates_matching_track_release(tmp_path: Path) -> None:
    changelog_dir = tmp_path / "changelogs"
    changelog_dir.mkdir(parents=True, exist_ok=True)
    (changelog_dir / "1773900042.txt").write_text("Latest internal notes", encoding="utf-8")

    service = Mock()
    service.edits().tracks().get.return_value.execute.return_value = {
        "releases": [
            {"versionCodes": ["1773900042"], "status": "completed"},
        ]
    }

    updated, source = syncer._update_release_notes(
        service,
        "pkg",
        "edit-1",
        "internal",
        "1773900042",
        changelog_dir,
    )

    assert updated is True
    assert source.endswith("1773900042.txt")
    service.edits().tracks().update.assert_called_once()
    body = service.edits().tracks().update.call_args.kwargs["body"]
    assert body["releases"][0]["releaseNotes"][0]["text"] == "Latest internal notes"


def test_update_release_notes_errors_when_version_missing(tmp_path: Path) -> None:
    changelog_dir = tmp_path / "changelogs"
    changelog_dir.mkdir(parents=True, exist_ok=True)
    (changelog_dir / "default.txt").write_text("Fallback notes", encoding="utf-8")

    service = Mock()
    service.edits().tracks().get.return_value.execute.return_value = {"releases": []}

    try:
        syncer._update_release_notes(
            service,
            "pkg",
            "edit-1",
            "internal",
            "1773900042",
            changelog_dir,
        )
    except syncer.MetadataSyncError as exc:
        assert "Could not find versionCode 1773900042" in str(exc)
    else:
        raise AssertionError("Expected missing track version to raise MetadataSyncError")


def test_resolve_key_path_prefers_explicit_file(tmp_path: Path) -> None:
    key_path = tmp_path / "play-service-account.json"
    key_path.write_text("{}", encoding="utf-8")
    assert syncer._resolve_key_path(str(key_path)) == key_path.resolve()
