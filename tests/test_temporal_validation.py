import unittest

from hospitality_ai.synthetic_data import generate_records
from hospitality_ai.temporal_validation import evaluate_newest_days, newest_days_split


class TemporalValidationTests(unittest.TestCase):
    def test_newest_thirty_days_are_reserved(self) -> None:
        training, test = newest_days_split(generate_records(365, seed=4), test_days=30)
        self.assertEqual(len(training), 335)
        self.assertEqual(len(test), 30)
        self.assertLess(training[-1].date, test[0].date)

    def test_temporal_model_beats_baseline(self) -> None:
        result = evaluate_newest_days(generate_records(365, seed=2026), test_days=30)
        self.assertLess(result.model_mae_kwh, result.baseline_mae_kwh)

    def test_invalid_test_period_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            newest_days_split(generate_records(30), test_days=30)


if __name__ == "__main__":
    unittest.main()
