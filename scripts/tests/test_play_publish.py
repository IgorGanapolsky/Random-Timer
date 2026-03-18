import tempfile
import unittest
from unittest.mock import call
from unittest.mock import Mock

from scripts.play_publish import (
    _commit_edit,
    _is_failed_precondition,
    _parse_args,
    _release_payload,
    _requires_manual_review_submission,
)


class _FakeHttpError(Exception):
    """Minimal HttpError stand-in for tests."""

    def __init__(self, status: int, content: str):
        super().__init__(f"HttpError {status}: {content}")
        self.resp = Mock(status=status)
        self.content = content.encode("utf-8")


class PlayPublishTests(unittest.TestCase):
    def test_detects_failed_precondition_marker(self):
        self.assertTrue(
            _is_failed_precondition(
                "HttpError 400",
                '{"error":{"status":"FAILED_PRECONDITION","message":"Precondition check failed."}}',
                400,
            )
        )

    def test_detects_precondition_phrase_for_400(self):
        self.assertTrue(
            _is_failed_precondition(
                "Bad request",
                "Precondition check failed for production publishing.",
                400,
            )
        )

    def test_does_not_false_positive_without_precondition(self):
        self.assertFalse(
            _is_failed_precondition(
                "HttpError 403",
                '{"error":{"status":"PERMISSION_DENIED","message":"No permission"}}',
                403,
            )
        )

    def test_release_payload_in_progress_clamps_invalid_fraction(self):
        payload = _release_payload(
            version_code="123",
            release_status="inProgress",
            release_notes="",
            user_fraction_raw="1.0",
        )
        self.assertEqual(payload["userFraction"], 0.1)
        self.assertEqual(payload["status"], "inProgress")

    def test_release_payload_completed_skips_user_fraction(self):
        payload = _release_payload(
            version_code="123",
            release_status="completed",
            release_notes="notes",
            user_fraction_raw="0.5",
        )
        self.assertNotIn("userFraction", payload)
        self.assertEqual(payload["releaseNotes"][0]["text"], "notes")

    def test_detects_manual_review_required_marker(self):
        self.assertTrue(
            _requires_manual_review_submission(
                "HttpError 400",
                '{"error":{"message":"Changes cannot be sent for review automatically. '
                'Please set the query parameter changesNotSentForReview to true."}}',
                400,
            )
        )

    def test_commit_edit_returns_false_when_normal_commit_succeeds(self):
        edits_service = Mock()
        edits_service.commit.return_value.execute.return_value = {}

        result = _commit_edit(edits_service, "pkg", "edit-1")

        self.assertFalse(result)
        edits_service.commit.assert_called_once_with(packageName="pkg", editId="edit-1")

    def test_commit_edit_retries_with_changes_not_sent_for_review(self):
        edits_service = Mock()
        edits_service.commit.side_effect = [
            Mock(
                execute=Mock(
                    side_effect=_FakeHttpError(
                        400,
                        '{"error":{"message":"Changes cannot be sent for review automatically. '
                        'Please set the query parameter changesNotSentForReview to true."}}',
                    )
                )
            ),
            Mock(execute=Mock(return_value={})),
        ]

        result = _commit_edit(edits_service, "pkg", "edit-1")

        self.assertTrue(result)
        self.assertEqual(
            edits_service.commit.call_args_list,
            [
                call(packageName="pkg", editId="edit-1"),
                call(packageName="pkg", editId="edit-1", changesNotSentForReview=True),
            ],
        )

    def test_commit_edit_reraises_unrelated_error(self):
        edits_service = Mock()
        edits_service.commit.return_value.execute.side_effect = _FakeHttpError(
            403,
            '{"error":{"message":"Permission denied"}}',
        )

        with self.assertRaises(_FakeHttpError):
            _commit_edit(edits_service, "pkg", "edit-1")

    def test_parse_args_default_result_error_json_use_tempdir(self):
        import sys

        tmp = tempfile.gettempdir()
        sys.argv = [
            "play_publish.py",
            "--service-account-json",
            "/fake/sa.json",
            "--package",
            "com.test",
            "--aab-path",
            "/fake/app.aab",
        ]
        args = _parse_args()
        self.assertIn(tmp, args.result_json)
        self.assertIn(tmp, args.error_json)
        self.assertTrue(args.result_json.endswith("play-upload-result.json"))
        self.assertTrue(args.error_json.endswith("play-upload-error.json"))


if __name__ == "__main__":
    unittest.main()
