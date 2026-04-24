"""
Regression test for HTTP 409 ITEM_PART_OF_ANOTHER_SUBMISSION in iOS submit-for-review.

_list_review_submission_items must request relationships in fields[reviewSubmissionItems]
so _find_submission_for_version can match an existing submission by appStoreVersion id.

If sparse fieldset omits relationships (JSON:API spec), relationships collapse to None,
the function returns (None, None), and the caller ends up creating/reusing a different
submission while the version is still attached to the original one — producing a 409.
"""
import unittest

from scripts.tests.router_client import RouterClient


class ListReviewSubmissionItemsSparseFieldsetTests(unittest.TestCase):
    def test_list_review_submission_items_requests_appstoreversion_relationship_in_fields(self):
        from scripts.asc.asc_submit_for_review import _list_review_submission_items

        submission_id = "sub-1"
        client = RouterClient(
            {
                ("GET", f"/reviewSubmissions/{submission_id}/items"): {"data": []},
            }
        )

        _list_review_submission_items(client, submission_id)

        self.assertEqual(len(client.calls), 1)
        params = client.calls[0]["params"] or {}
        fields = params.get("fields[reviewSubmissionItems]", "")
        self.assertIn(
            "appStoreVersion",
            fields,
            "fields[reviewSubmissionItems] must request appStoreVersion so "
            "_find_submission_for_version can locate the owning submission.",
        )

    def test_find_submission_for_version_matches_by_relationship_when_response_includes_it(self):
        """End-to-end: when the endpoint returns relationships (as it will after fix),
        the existing submission holding the version is found and the code does NOT
        try to create a duplicate submission item (which would 409)."""
        from scripts.asc.asc_submit_for_review import _find_submission_for_version

        submission_id = "d3ce3d68"
        version_id = "884770007"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/reviewSubmissions"): {
                    "data": [
                        {
                            "id": submission_id,
                            "type": "reviewSubmissions",
                            "attributes": {"state": "READY_FOR_REVIEW"},
                        }
                    ]
                },
                ("GET", f"/reviewSubmissions/{submission_id}/items"): {
                    "data": [
                        {
                            "id": "item-1",
                            "type": "reviewSubmissionItems",
                            "attributes": {"state": "READY_FOR_REVIEW"},
                            "relationships": {
                                "appStoreVersion": {
                                    "data": {"type": "appStoreVersions", "id": version_id}
                                }
                            },
                        }
                    ]
                },
            }
        )

        found_submission, found_item = _find_submission_for_version(
            client, app_id="app-1", version_id=version_id
        )

        self.assertIsNotNone(found_submission)
        self.assertEqual(found_submission["id"], submission_id)
        self.assertIsNotNone(found_item)
        self.assertEqual(found_item["id"], "item-1")


if __name__ == "__main__":
    unittest.main()
