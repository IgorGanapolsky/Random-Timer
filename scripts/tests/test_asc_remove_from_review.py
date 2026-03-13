import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import asc_remove_from_review


class _FakeClient:
    def __init__(self, *, initial_state="WAITING_FOR_REVIEW", final_state="DEVELOPER_REJECTED", submission_id="sub-1"):
        self.initial_state = initial_state
        self.final_state = final_state
        self.state = initial_state
        self.submission_id = submission_id
        self.deleted = []

    def request(self, method, path, params=None, payload=None):
        if method == "GET" and path.endswith("/appStoreVersionSubmission"):
            if self.submission_id:
                return {"data": {"id": self.submission_id, "type": "appStoreVersionSubmissions"}}
            return {"data": None}
        if method == "DELETE" and path == f"/appStoreVersionSubmissions/{self.submission_id}":
            self.deleted.append(path)
            self.state = self.final_state
            return {}
        raise AssertionError(f"Unhandled request: {method} {path}")


class AscRemoveFromReviewTests(unittest.TestCase):
    def test_submission_id_extracts_dict_payload(self):
        self.assertEqual(
            asc_remove_from_review._submission_id({"data": {"id": "sub-123"}}),
            "sub-123",
        )
        self.assertEqual(asc_remove_from_review._submission_id({"data": None}), "")

    def test_remove_from_review_deletes_submission_and_waits_for_editable_state(self):
        client = _FakeClient()
        with (
            patch.object(asc_remove_from_review, "get_app", return_value={"id": "app-1"}),
            patch.object(
                asc_remove_from_review,
                "find_app_store_version_id",
                return_value=("version-1", "WAITING_FOR_REVIEW"),
            ),
            patch.object(asc_remove_from_review, "get_version_state", side_effect=["WAITING_FOR_REVIEW", "DEVELOPER_REJECTED"]),
            patch.object(asc_remove_from_review.time, "sleep", return_value=None),
        ):
            result = asc_remove_from_review.remove_from_review(
                client,
                bundle_id="com.example.app",
                version="1.2.6",
                wait=True,
                timeout=10,
                poll_interval=1,
            )

        self.assertTrue(result.removed)
        self.assertTrue(result.became_editable)
        self.assertEqual(result.final_state, "DEVELOPER_REJECTED")
        self.assertEqual(result.submission_id, "sub-1")
        self.assertEqual(client.deleted, ["/appStoreVersionSubmissions/sub-1"])

    def test_remove_from_review_is_noop_when_submission_is_missing(self):
        client = _FakeClient(initial_state="PREPARE_FOR_SUBMISSION", final_state="PREPARE_FOR_SUBMISSION", submission_id="")
        with (
            patch.object(asc_remove_from_review, "get_app", return_value={"id": "app-1"}),
            patch.object(
                asc_remove_from_review,
                "find_app_store_version_id",
                return_value=("version-1", "PREPARE_FOR_SUBMISSION"),
            ),
            patch.object(asc_remove_from_review, "get_version_state", return_value="PREPARE_FOR_SUBMISSION"),
        ):
            result = asc_remove_from_review.remove_from_review(
                client,
                bundle_id="com.example.app",
                version="1.2.6",
                wait=False,
                timeout=0,
                poll_interval=1,
            )

        self.assertFalse(result.removed)
        self.assertTrue(result.became_editable)
        self.assertEqual(result.reason, "no_submission_found")

    def test_main_writes_json_output(self):
        client = _FakeClient()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "remove.json"
            with (
                patch.object(asc_remove_from_review.ASCClient, "from_env", return_value=client),
                patch.object(asc_remove_from_review, "get_app", return_value={"id": "app-1"}),
                patch.object(
                    asc_remove_from_review,
                    "find_app_store_version_id",
                    return_value=("version-1", "WAITING_FOR_REVIEW"),
                ),
                patch.object(asc_remove_from_review, "get_version_state", side_effect=["DEVELOPER_REJECTED"]),
                patch(
                    "sys.argv",
                    [
                        "asc_remove_from_review.py",
                        "--version",
                        "1.2.6",
                        "--json-out",
                        str(out),
                    ],
                ),
            ):
                self.assertEqual(asc_remove_from_review.main(), 0)

            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], "1.2.6")
            self.assertEqual(payload["submission_id"], "sub-1")


if __name__ == "__main__":
    unittest.main()
