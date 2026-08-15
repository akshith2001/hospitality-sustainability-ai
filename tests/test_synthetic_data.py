import tempfile
import unittest
from pathlib import Path

from hospitality_ai.synthetic_data import (
    expected_electricity_kwh,
    generate_records,
    write_csv,
)


class SyntheticDataTests(unittest.TestCase):
    def test_expected_use_increases_with_customers(self) -> None:
        low = expected_electricity_kwh("restaurant", 50, 10, 18, 120, 10)
        high = expected_electricity_kwh("restaurant", 100, 10, 18, 120, 10)
        self.assertGreater(high, low)

    def test_fixed_seed_is_reproducible(self) -> None:
        self.assertEqual(generate_records(50, seed=7), generate_records(50, seed=7))

    def test_generated_values_are_valid(self) -> None:
        records = generate_records(100, seed=4)
        self.assertTrue(all(record.electricity_kwh >= 0 for record in records))
        self.assertTrue(all(record.is_injected_anomaly in (0, 1) for record in records))

    def test_csv_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            write_csv(generate_records(10, seed=2), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("electricity_kwh", text)
            self.assertEqual(len(text.splitlines()), 11)


if __name__ == "__main__":
    unittest.main()
