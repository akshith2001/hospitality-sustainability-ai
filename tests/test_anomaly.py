import unittest

from hospitality_ai.anomaly import evaluate_anomaly_detector, fit_anomaly_detector
from hospitality_ai.synthetic_data import generate_records


class AnomalyTests(unittest.TestCase):
    def test_threshold_is_above_training_residual_centre(self) -> None:
        detector = fit_anomaly_detector(generate_records(500, seed=8))
        self.assertGreater(detector.threshold_kwh, detector.residual_median_kwh)

    def test_detector_finds_most_injected_anomalies(self) -> None:
        _, result = evaluate_anomaly_detector(generate_records(2_000, seed=2026), seed=2026)
        self.assertGreaterEqual(result.recall, 0.80)
        self.assertGreaterEqual(result.precision, 0.70)

    def test_invalid_threshold_multiplier_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fit_anomaly_detector(generate_records(100), threshold_multiplier=0)


if __name__ == "__main__":
    unittest.main()
