import unittest

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewSubmissionFlowTests(unittest.TestCase):
    def test_submit_for_review_resolves_rejected_item_and_resubmits_existing_submission(self):
        from scripts.asc.asc_submit_for_review import submit_for_review

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

        self.assertEqual(client.calls[0]["path"], "/apps/app-1/subscriptionGroups")
        self.assertEqual(client.calls[1]["path"], "/apps/app-1/reviewSubmissions")
        self.assertEqual(client.calls[2]["path"], f"/reviewSubmissions/{submission_id}/items")
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
        from scripts.asc.asc_submit_for_review import submit_for_review

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

        self.assertEqual(client.calls[0]["path"], "/apps/app-1/subscriptionGroups")
        self.assertEqual(client.calls[1]["path"], "/apps/app-1/reviewSubmissions")
        self.assertEqual(client.calls[2]["path"], "/apps/app-1/reviewSubmissions")
        self.assertEqual(
            client.calls[3]["path"],
            "/reviewSubmissions",
        )
        self.assertEqual(
            client.calls[3]["payload"],
            {
                "data": {
                    "type": "reviewSubmissions",
                    "attributes": {"platform": "IOS"},
                    "relationships": {"app": {"data": {"type": "apps", "id": "app-1"}}},
                }
            },
        )
        self.assertEqual(client.calls[4]["path"], "/reviewSubmissionItems")
        self.assertEqual(
            client.calls[4]["payload"],
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

    def test_submit_for_review_reuses_empty_ready_for_review_submission_when_limit_shell_exists(self):
        from scripts.asc.asc_submit_for_review import submit_for_review

        submission_id = "sub-empty"
        version_id = "ver-1"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/subscriptionGroups"): {"data": []},
                ("GET", "/apps/app-1/reviewSubmissions"): {
                    "data": [
                        {
                            "id": submission_id,
                            "type": "reviewSubmissions",
                            "attributes": {"state": "READY_FOR_REVIEW", "submittedDate": None},
                        }
                    ]
                },
                ("GET", f"/reviewSubmissions/{submission_id}/items"): {"data": []},
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

        self.assertEqual(
            [call["path"] for call in client.calls],
            [
                "/apps/app-1/subscriptionGroups",
                "/apps/app-1/reviewSubmissions",
                f"/reviewSubmissions/{submission_id}/items",
                "/apps/app-1/reviewSubmissions",
                f"/reviewSubmissions/{submission_id}/items",
                "/reviewSubmissionItems",
                f"/reviewSubmissions/{submission_id}",
            ],
        )

    def test_submit_for_review_recovers_existing_rejected_submission_from_item_conflict(self):
        from scripts.asc.asc_submit_for_review import submit_for_review

        existing_submission_id = "d3ce3d68-cf57-4204-9d3a-44fdc69a4ef4"
        conflict_shell_id = "sub-empty"
        version_id = "ver-1"
        item_id = "item-existing"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/subscriptionGroups"): {"data": []},
                ("GET", "/apps/app-1/reviewSubmissions"): {
                    "data": [
                        {
                            "id": conflict_shell_id,
                            "type": "reviewSubmissions",
                            "attributes": {"state": "READY_FOR_REVIEW", "submittedDate": None},
                        }
                    ]
                },
                ("GET", f"/reviewSubmissions/{conflict_shell_id}/items"): {"data": []},
                ("POST", "/reviewSubmissionItems"): RuntimeError(
                    "POST /reviewSubmissionItems failed: HTTP 409 {'errors': [{'code': "
                    "'STATE_ERROR.ITEM_PART_OF_ANOTHER_SUBMISSION', 'detail': "
                    "'appStoreVersions with id 884770007 was already added to another "
                    f"reviewSubmission with id {existing_submission_id}'}}]"
                ),
                ("GET", f"/reviewSubmissions/{existing_submission_id}"): {
                    "data": {
                        "id": existing_submission_id,
                        "type": "reviewSubmissions",
                        "attributes": {"state": "UNRESOLVED_ISSUES"},
                    }
                },
                ("GET", f"/reviewSubmissions/{existing_submission_id}/items"): {
                    "data": [
                        {
                            "id": item_id,
                            "type": "reviewSubmissionItems",
                            "attributes": {"state": "REJECTED"},
                        }
                    ],
                    "included": [
                        {
                            "id": version_id,
                            "type": "appStoreVersions",
                        }
                    ],
                },
                ("PATCH", f"/reviewSubmissionItems/{item_id}"): {
                    "data": {
                        "id": item_id,
                        "type": "reviewSubmissionItems",
                        "attributes": {"state": "READY_FOR_REVIEW"},
                    }
                },
                ("PATCH", f"/reviewSubmissions/{existing_submission_id}"): {
                    "data": {
                        "id": existing_submission_id,
                        "type": "reviewSubmissions",
                        "attributes": {"state": "WAITING_FOR_REVIEW"},
                    }
                },
            }
        )

        submit_for_review(client, "app-1", version_id)

        self.assertEqual(
            [call["path"] for call in client.calls],
            [
                "/apps/app-1/subscriptionGroups",
                "/apps/app-1/reviewSubmissions",
                f"/reviewSubmissions/{conflict_shell_id}/items",
                "/apps/app-1/reviewSubmissions",
                f"/reviewSubmissions/{conflict_shell_id}/items",
                "/reviewSubmissionItems",
                f"/reviewSubmissions/{existing_submission_id}",
                f"/reviewSubmissions/{existing_submission_id}/items",
                f"/reviewSubmissionItems/{item_id}",
                f"/reviewSubmissions/{existing_submission_id}",
            ],
        )

    def test_submit_for_review_with_attach_subscriptions_skips_existing_waiting_submission_when_none_pending(self):
        from scripts.asc.asc_submit_for_review import submit_for_review

        submission_id = "sub-1"
        version_id = "ver-1"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/subscriptionGroups"): {"data": []},
                ("GET", "/apps/app-1/reviewSubmissions"): {
                    "data": [
                        {
                            "id": submission_id,
                            "type": "reviewSubmissions",
                            "attributes": {"state": "WAITING_FOR_REVIEW"},
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
                                "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}
                            },
                        }
                    ]
                },
            }
        )

        submit_for_review(client, "app-1", version_id, attach_subscriptions=True)

        self.assertEqual(
            [call["path"] for call in client.calls],
            [
                "/apps/app-1/subscriptionGroups",
                "/apps/app-1/reviewSubmissions",
                f"/reviewSubmissions/{submission_id}/items",
            ],
        )

    def test_submit_for_review_fails_when_subscription_requires_manual_review_attachment(self):
        from scripts.asc.asc_submit_for_review import submit_for_review

        client = RouterClient(
            {
                ("GET", "/apps/app-1/subscriptionGroups"): {
                    "data": [
                        {
                            "id": "group-1",
                            "type": "subscriptionGroups",
                        }
                    ]
                },
                ("GET", "/subscriptionGroups/group-1/subscriptions"): {
                    "data": [
                        {
                            "id": "sub-1",
                            "type": "subscriptions",
                            "attributes": {
                                "name": "Pro Tactical Annual",
                                "state": "WAITING_FOR_REVIEW",
                            },
                        }
                    ]
                },
            }
        )

        with self.assertRaises(SystemExit) as exc:
            submit_for_review(client, "app-1", "ver-1")

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(
            [call["path"] for call in client.calls],
            [
                "/apps/app-1/subscriptionGroups",
                "/subscriptionGroups/group-1/subscriptions",
            ],
        )


if __name__ == "__main__":
    unittest.main()
