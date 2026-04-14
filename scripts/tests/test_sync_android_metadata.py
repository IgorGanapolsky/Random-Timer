from __future__ import annotations

import pytest

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


def test_commit_edit_propagates_api_errors() -> None:
    edits = _FakeEdits(
        Exception(
            'HttpError 400: "Changes are sent for review automatically. The query parameter '
            'changesNotSentForReview must not be set."'
        )
    )

    import pytest
    with pytest.raises(Exception, match="changesNotSentForReview"):
        sync_android_metadata.commit_edit(edits, edit_id="123")


def test_commit_edit_uses_changes_not_sent_for_review_when_supported() -> None:
    edits = _FakeEdits()

    sync_android_metadata.commit_edit(edits, edit_id="123")

    assert edits.calls == [
        {
            "packageName": sync_android_metadata.PACKAGE_NAME,
            "editId": "123",
        }
    ]


def test_commit_edit_does_not_swallow_unrelated_failures() -> None:
    edits = _FakeEdits(Exception("some other commit failure"))

    with pytest.raises(Exception, match="some other commit failure"):
        sync_android_metadata.commit_edit(edits, edit_id="123")
