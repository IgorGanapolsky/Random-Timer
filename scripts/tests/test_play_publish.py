import unittest

from scripts.play_publish import _is_failed_precondition, _release_payload


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


if __name__ == "__main__":
    unittest.main()
