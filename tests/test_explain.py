import unittest

from hospitality_ai.anomaly import fit_anomaly_detector
from hospitality_ai.explain import explain_record, most_positive_residual_record
from hospitality_ai.synthetic_data import generate_records


class ExplainabilityTests(unittest.TestCase):
    def test_contributions_sum_to_prediction(self) -> None:
        records = generate_records(500, seed=6)
        detector = fit_anomaly_detector(records[:400])
        explanation = explain_record(detector, records[400])
        total = sum(item.contribution_kwh for item in explanation.contributions)
        self.assertAlmostEqual(total, explanation.predicted_kwh, places=8)

    def test_highest_residual_record_is_selected(self) -> None:
        records = generate_records(500, seed=14)
        detector = fit_anomaly_detector(records[:400])
        chosen = most_positive_residual_record(detector, records[400:])
        self.assertEqual(
            detector.residual(chosen),
            max(detector.residual(record) for record in records[400:]),
        )

    def test_alert_guidance_does_not_claim_proven_waste(self) -> None:
        records = generate_records(1_000, seed=2026)
        detector = fit_anomaly_detector(records[:800])
        record = most_positive_residual_record(detector, records[800:])
        explanation = explain_record(detector, record)
        self.assertTrue(explanation.is_alert)
        self.assertIn("not proof of waste", explanation.guidance)


if __name__ == "__main__":
    unittest.main()
