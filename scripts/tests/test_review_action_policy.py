import unittest

from scripts.review_action_policy import evaluate_policy


class ReviewActionPolicyTests(unittest.TestCase):
    def test_enforce_blocks_on_sla_breaches(self):
        reviews = {
            "slaBreachCount": 2,
            "unresolvedLowStarCount": 4,
            "averageRating": 4.2,
            "totalReviews": 50,
            "slaBreaches": [{"id": "a", "ageHours": 40.0}, {"id": "b", "ageHours": 30.0}],
        }
        anomaly = {"status": "warn", "maxSeverity": "medium", "score": 5, "anomalies": []}

        out = evaluate_policy(mode="enforce", reviews_report=reviews, anomaly_report=anomaly)
        decision = out["decision"]
        self.assertEqual(decision["route"], "ESCALATE_HUMAN")
        self.assertTrue(decision["blocking"])

    def test_observe_routes_to_auto_respond_for_unresolved_low_star(self):
        reviews = {
            "slaBreachCount": 0,
            "unresolvedLowStarCount": 3,
            "averageRating": 4.5,
            "totalReviews": 50,
            "slaBreaches": [],
        }
        anomaly = {"status": "ok", "maxSeverity": "low", "score": 1, "anomalies": []}

        out = evaluate_policy(mode="observe", reviews_report=reviews, anomaly_report=anomaly)
        decision = out["decision"]
        self.assertEqual(decision["route"], "AUTO_RESPOND_TEMPLATE")
        self.assertFalse(decision["blocking"])

    def test_monitor_when_healthy(self):
        reviews = {
            "slaBreachCount": 0,
            "unresolvedLowStarCount": 0,
            "averageRating": 4.8,
            "totalReviews": 50,
            "slaBreaches": [],
        }
        anomaly = {"status": "ok", "maxSeverity": "none", "score": 0, "anomalies": []}

        out = evaluate_policy(mode="observe", reviews_report=reviews, anomaly_report=anomaly)
        decision = out["decision"]
        self.assertEqual(decision["route"], "MONITOR")
        self.assertFalse(decision["blocking"])


if __name__ == "__main__":
    unittest.main()
