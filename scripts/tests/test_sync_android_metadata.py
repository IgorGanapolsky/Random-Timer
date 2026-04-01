from __future__ import annotations

import pytest
from pathlib import Path

from scripts import sync_android_metadata


class _FakeRequest:
    def __init__(self, exc: Exception | None = None):
        self._exc = exc

    def execute(self):
        if self._exc is not None:
            raise self._exc
        return {"ok": True}


class _FakeEdits:
    def __init__(self, first_error: Exception | None = None):
        self.first_error = first_error
        self.calls: list[dict[str, object]] = []

    def commit(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1 and self.first_error is not None:
            return _FakeRequest(self.first_error)
        return _FakeRequest()


def test_commit_edit_retries_without_changes_not_sent_for_review_flag() -> None:
    edits = _FakeEdits(
        Exception(
            'HttpError 400: "Changes are sent for review automatically. The query parameter '
            'changesNotSentForReview must not be set."'
        )
    )

    sync_android_metadata.commit_edit(edits, edit_id="123")

    assert edits.calls == [
        {
            "packageName": sync_android_metadata.PACKAGE_NAME,
            "editId": "123",
            "changesNotSentForReview": True,
        },
        {
            "packageName": sync_android_metadata.PACKAGE_NAME,
            "editId": "123",
        },
    ]


def test_commit_edit_uses_changes_not_sent_for_review_when_supported() -> None:
    edits = _FakeEdits()

    sync_android_metadata.commit_edit(edits, edit_id="123")

    assert edits.calls == [
        {
            "packageName": sync_android_metadata.PACKAGE_NAME,
            "editId": "123",
            "changesNotSentForReview": True,
        }
    ]


def test_commit_edit_does_not_swallow_unrelated_failures() -> None:
    edits = _FakeEdits(Exception("some other commit failure"))

    with pytest.raises(Exception, match="some other commit failure"):
        sync_android_metadata.commit_edit(edits, edit_id="123")


def test_collect_image_assets_requires_core_play_assets_when_strict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metadata_root = tmp_path / "metadata"
    (metadata_root / "en-US" / "images" / "phoneScreenshots").mkdir(parents=True, exist_ok=True)
    (metadata_root / "en-US" / "images" / "phoneScreenshots" / "1.png").write_bytes(b"png")
    monkeypatch.setattr(sync_android_metadata, "METADATA_ROOT", metadata_root)

    with pytest.raises(RuntimeError, match="missing required"):
        sync_android_metadata.collect_image_assets("en-US", strict=True)
