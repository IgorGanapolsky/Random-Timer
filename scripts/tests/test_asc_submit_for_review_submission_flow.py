import unittest
from unittest import mock

from scripts.tests.router_client import RouterClient


class AscSubmitForReviewSubmissionFlowTests(unittest.TestCase):
    @staticmethod
    def _subscription_groups_routes(*, state, group_id="group-1", subscription_id="sub-1"):
        return {
            ("GET", "/apps/app-1/subscriptionGroups"): {
                "data": [
                    {
                        "id": group_id,
                        "type": "subscriptionGroups",
                    }
                ]
            },
            ("GET", f"/subscriptionGroups/{group_id}/subscriptions"): {
                "data": [
                    {
                        "id": subscription_id,
                        "type": "subscriptions",
                        "attributes": {
                            "name": "Pro Tactical Annual",
                            "state": state,
                        },
                    }
                ]
            },
        }

    @staticmethod
    def _subscription_submission_routes(*, state_after_submit, subscription_id="sub-1"):
        return {
            ("POST", "/subscriptionSubmissions"): {
                "data": {
                    "id": "subm-1",
                    "type": "subscriptionSubmissions",
                }
            },
            ("GET", f"/subscriptions/{subscription_id}"): {
                "data": {
                    "id": subscription_id,
                    "type": "subscriptions",
                    "attributes": {
                        "name": "Pro Tactical Annual",
                        "state": state_after_submit,
                    },
                }
            },
        }

    @staticmethod
    def _new_review_submission_routes(*, submission_id, version_id="ver-1"):
        return {
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
                    "relationships": {
                        "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}
                    },
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
        from scripts.asc_submit_for_review import submit_for_review

        submission_id = "sub-new"
        version_id = "ver-1"

        client = RouterClient(
            {
                ("GET", "/apps/app-1/subscriptionGroups"): {"data": []},
                **self._new_review_submission_routes(submission_id=submission_id, version_id=version_id),
            }
        )

        submit_for_review(client, "app-1", version_id)

        self.assertEqual(client.calls[0]["path"], "/apps/app-1/subscriptionGroups")
        self.assertEqual(client.calls[1]["path"], "/apps/app-1/reviewSubmissions")
        self.assertEqual(client.calls[2]["path"], "/reviewSubmissions")
        self.assertEqual(
            client.calls[2]["payload"],
            {
                "data": {
                    "type": "reviewSubmissions",
                    "attributes": {"platform": "IOS"},
                    "relationships": {"app": {"data": {"type": "apps", "id": "app-1"}}},
                }
            },
        )
        self.assertEqual(client.calls[3]["path"], "/reviewSubmissionItems")
        self.assertEqual(
            client.calls[3]["payload"],
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

    def test_submit_for_review_creates_subscription_submission_before_app_submission(self):
        from scripts.asc_submit_for_review import submit_for_review

        submission_id = "sub-new"
        client = RouterClient(
            {
                **self._subscription_groups_routes(state="READY_TO_SUBMIT"),
                **self._subscription_submission_routes(state_after_submit="WAITING_FOR_REVIEW"),
                **self._new_review_submission_routes(submission_id=submission_id),
            }
        )

        submit_for_review(client, "app-1", "ver-1")
        self.assertEqual(
            [call["path"] for call in client.calls],
            [
                "/apps/app-1/subscriptionGroups",
                "/subscriptionGroups/group-1/subscriptions",
                "/subscriptionSubmissions",
                "/subscriptions/sub-1",
                "/apps/app-1/reviewSubmissions",
                "/reviewSubmissions",
                "/reviewSubmissionItems",
                f"/reviewSubmissions/{submission_id}",
            ],
        )

    def test_submit_for_review_fails_when_subscription_does_not_transition_to_review_state(self):
        from scripts.asc_submit_for_review import submit_for_review

        client = RouterClient(
            {
                **self._subscription_groups_routes(state="READY_TO_SUBMIT"),
                **self._subscription_submission_routes(state_after_submit="READY_TO_SUBMIT"),
            }
        )

        with mock.patch(
            "scripts.asc_submit_for_review._wait_for_subscription_state",
            return_value={
                "id": "sub-1",
                "type": "subscriptions",
                "attributes": {
                    "name": "Pro Tactical Annual",
                    "state": "READY_TO_SUBMIT",
                },
            },
        ):
            with self.assertRaises(SystemExit) as exc:
                submit_for_review(client, "app-1", "ver-1")

        self.assertEqual(exc.exception.code, 1)
        self.assertEqual(
            [call["path"] for call in client.calls],
            [
                "/apps/app-1/subscriptionGroups",
                "/subscriptionGroups/group-1/subscriptions",
                "/subscriptionSubmissions",
            ],
        )


if __name__ == "__main__":
    unittest.main()
