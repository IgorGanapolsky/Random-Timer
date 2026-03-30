import unittest

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewSubmissionFlowTests(unittest.TestCase):
    def test_submit_for_review_resolves_rejected_item_and_resubmits_existing_submission(self):
        from scripts.asc_submit_for_review import submit_for_review

        item_id = "item-1"
        submission_id = "sub-1"
        version_id = "ver-1"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/reviewSubmissions"): {
                    "data": [
                        {
                            "id": submission_id,
                            "type": "reviewSubmissions",
                            "attributes": {"state": "UNRESOLVED_ISSUES"},
                        }
                    ]
                },
                ("GET", f"/reviewSubmissions/{submission_id}/items"): {
                    "data": [
                        {
                            "id": item_id,
                            "type": "reviewSubmissionItems",
                            "attributes": {"state": "REJECTED"},
                            "relationships": {
                                "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}
                            },
                        }
                    ]
                },
                ("PATCH", f"/reviewSubmissionItems/{item_id}"): {
                    "data": {
                        "id": item_id,
                        "type": "reviewSubmissionItems",
                        "attributes": {"state": "READY_FOR_REVIEW"},
                    }
                },
                ("PATCH", f"/reviewSubmissions/{submission_id}"): {
                    "data": {
                        "id": submission_id,
                        "type": "reviewSubmissions",
                        "attributes": {"state": "WAITING_FOR_REVIEW"},
                    }
                },
                ("GET", "/apps/app-1/subscriptionGroups"): {
                    "data": []
                },
            }
        )

        submit_for_review(client, "app-1", version_id)

        self.assertEqual(client.calls[0]["path"], "/apps/app-1/reviewSubmissions")
        self.assertEqual(client.calls[1]["path"], f"/reviewSubmissions/{submission_id}/items")
        # calls[2] is the subscription groups lookup (returns empty)
        self.assertEqual(client.calls[2]["path"], "/apps/app-1/subscriptionGroups")
        self.assertEqual(client.calls[3]["path"], f"/reviewSubmissionItems/{item_id}")
        self.assertEqual(
            client.calls[3]["payload"],
            {
                "data": {
                    "type": "reviewSubmissionItems",
                    "id": item_id,
                    "attributes": {"resolved": True},
                }
            },
        )
        self.assertEqual(client.calls[4]["path"], f"/reviewSubmissions/{submission_id}")
        self.assertEqual(
            client.calls[4]["payload"],
            {
                "data": {
                    "type": "reviewSubmissions",
                    "id": submission_id,
                    "attributes": {"submitted": True},
                }
            },
        )

    def test_submit_for_review_creates_submission_and_item_when_missing(self):
        from scripts.asc_submit_for_review import submit_for_review

        submission_id = "sub-new"
        version_id = "ver-1"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/reviewSubmissions"): {"data": []},
                ("POST", "/reviewSubmissions"): {
                    "data": {
                        "id": submission_id,
                        "type": "reviewSubmissions",
                        "attributes": {"state": "PREPARE_FOR_SUBMISSION"},
                    }
                },
                ("POST", "/reviewSubmissionItems"): {
                    "data": {
                        "id": "item-new",
                        "type": "reviewSubmissionItems",
                        "attributes": {"state": "READY_FOR_REVIEW"},
                    }
                },
                ("PATCH", f"/reviewSubmissions/{submission_id}"): {
                    "data": {
                        "id": submission_id,
                        "type": "reviewSubmissions",
                        "attributes": {"state": "WAITING_FOR_REVIEW"},
                    }
                },
            }
        )

        submit_for_review(client, "app-1", version_id)

        self.assertEqual(client.calls[1]["path"], "/reviewSubmissions")
        self.assertEqual(
            client.calls[1]["payload"],
            {
                "data": {
                    "type": "reviewSubmissions",
                    "attributes": {"platform": "IOS"},
                    "relationships": {"app": {"data": {"type": "apps", "id": "app-1"}}},
                }
            },
        )
        self.assertEqual(client.calls[2]["path"], "/reviewSubmissionItems")
        self.assertEqual(
            client.calls[2]["payload"],
            {
                "data": {
                    "type": "reviewSubmissionItems",
                    "relationships": {
                        "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": submission_id}},
                        "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}},
                    },
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
