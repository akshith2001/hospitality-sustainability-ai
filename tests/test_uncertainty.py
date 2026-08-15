import unittest
from dataclasses import replace

from hospitality_ai.synthetic_data import generate_records
from hospitality_ai.uncertainty import fit_uncertainty_model


class UncertaintyTests(unittest.TestCase):
    def test_prediction_is_inside_its_range(self) -> None:
        records = generate_records(500, seed=10)
        result = fit_uncertainty_model(records).predict_range(records[0])
        self.assertLess(result.lower_kwh, result.predicted_kwh)
        self.assertGreater(result.upper_kwh, result.predicted_kwh)

    def test_out_of_range_input_has_low_confidence(self) -> None:
        records = generate_records(500, seed=10)
        unusual = replace(records[0], customers=10_000)
        result = fit_uncertainty_model(records).predict_range(unusual)
        self.assertEqual(result.confidence, "low")
        self.assertIn("customers", result.warning)

    def test_small_training_set_has_low_confidence(self) -> None:
        records = generate_records(50, seed=10)
        result = fit_uncertainty_model(records).predict_range(records[0])
        self.assertEqual(result.confidence, "low")
        self.assertIn("more relevant data", result.warning)

    def test_invalid_multiplier_is_rejected(self) -> None:
        records = generate_records(100, seed=10)
        with self.assertRaises(ValueError):
            fit_uncertainty_model(records).predict_range(records[0], multiplier=0)


if __name__ == "__main__":
    unittest.main()
