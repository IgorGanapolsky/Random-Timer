import unittest

from scripts.review_anomaly_detector import detect_anomalies


def _report(
    *,
    generated_at: str,
    avg: float,
    r1: int,
    r2: int,
    r3: int,
    r4: int,
    r5: int,
    unresolved: int,
    sla: int,
) -> dict:
    total = r1 + r2 + r3 + r4 + r5
    return {
        "generatedAt": generated_at,
        "averageRating": avg,
        "ratings": {"1": r1, "2": r2, "3": r3, "4": r4, "5": r5},
        "totalReviews": total,
        "unresolvedLowStarCount": unresolved,
        "slaBreachCount": sla,
    }


class ReviewAnomalyDetectorTests(unittest.TestCase):
    def test_detects_alert_on_rating_drop_and_sla_spike(self):
        history = [
            _report(
                generated_at=f"2026-02-18T{h:02d}:00:00+00:00",
                avg=4.7,
                r1=1,
                r2=1,
                r3=2,
                r4=10,
                r5=36,
                unresolved=0,
                sla=0,
            )
            for h in range(0, 10)
        ]
        current = _report(
            generated_at="2026-02-19T11:00:00+00:00",
            avg=3.7,
            r1=8,
            r2=5,
            r3=5,
            r4=12,
            r5=20,
            unresolved=9,
            sla=3,
        )

        out = detect_anomalies(
            current_report=current,
            history_reports=history,
            min_history=8,
            rating_drop_threshold=0.25,
            low_star_rate_spike_threshold=0.05,
            unresolved_spike_threshold=3.0,
            sla_breach_spike_threshold=1.0,
        )

        self.assertEqual(out["status"], "alert")
        metrics = {a["metric"] for a in out["anomalies"]}
        self.assertIn("average_rating", metrics)
        self.assertIn("sla_breach_count", metrics)

    def test_observe_when_history_is_insufficient(self):
        history = [
            _report(
                generated_at="2026-02-18T00:00:00+00:00",
                avg=4.7,
                r1=1,
                r2=1,
                r3=1,
                r4=10,
                r5=37,
                unresolved=0,
                sla=0,
            )
        ]
        current = _report(
            generated_at="2026-02-19T11:00:00+00:00",
            avg=4.69,
            r1=1,
            r2=1,
            r3=1,
            r4=10,
            r5=37,
            unresolved=0,
            sla=0,
        )

        out = detect_anomalies(
            current_report=current,
            history_reports=history,
            min_history=8,
            rating_drop_threshold=0.25,
            low_star_rate_spike_threshold=0.05,
            unresolved_spike_threshold=3.0,
            sla_breach_spike_threshold=1.0,
        )

        self.assertTrue(out["insufficientHistory"])
        self.assertEqual(out["status"], "observe")
        self.assertEqual(out["anomalies"], [])

    def test_warn_when_sla_breaches_present_without_baseline(self):
        current = _report(
            generated_at="2026-02-19T11:00:00+00:00",
            avg=4.6,
            r1=2,
            r2=2,
            r3=3,
            r4=10,
            r5=33,
            unresolved=4,
            sla=1,
        )

        out = detect_anomalies(
            current_report=current,
            history_reports=[],
            min_history=8,
            rating_drop_threshold=0.25,
            low_star_rate_spike_threshold=0.05,
            unresolved_spike_threshold=3.0,
            sla_breach_spike_threshold=1.0,
        )

        self.assertEqual(out["status"], "warn")
        self.assertGreaterEqual(len(out["anomalies"]), 1)
        self.assertEqual(out["anomalies"][0]["metric"], "sla_breach_count")


if __name__ == "__main__":
    unittest.main()
