import unittest

from hospitality_ai.baseline import (
    evaluate_mean_baseline,
    mean_absolute_error,
    train_test_split,
)
from hospitality_ai.synthetic_data import generate_records


class BaselineTests(unittest.TestCase):
    def test_eighty_twenty_split(self) -> None:
        training, test = train_test_split(generate_records(1_000), test_fraction=0.20)
        self.assertEqual(len(training), 800)
        self.assertEqual(len(test), 200)

    def test_split_is_reproducible_and_has_no_overlap(self) -> None:
        records = generate_records(100, seed=5)
        first_training, first_test = train_test_split(records, seed=8)
        second_training, second_test = train_test_split(records, seed=8)
        self.assertEqual(first_training, second_training)
        self.assertEqual(first_test, second_test)
        self.assertTrue(set(first_training).isdisjoint(set(first_test)))

    def test_absolute_error_example(self) -> None:
        self.assertEqual(mean_absolute_error([250.0], [290.0]), 40.0)

    def test_baseline_returns_positive_mae(self) -> None:
        result = evaluate_mean_baseline(generate_records(500, seed=9), seed=9)
        self.assertGreater(result.mean_absolute_error_kwh, 0)
        self.assertEqual(result.training_rows + result.test_rows, 500)


if __name__ == "__main__":
    unittest.main()
