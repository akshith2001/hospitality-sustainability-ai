import tempfile
import unittest
from pathlib import Path

from hospitality_ai.meter_data import (
    MeterReading,
    validate_dataset,
    validate_reading,
    write_meter_csv,
)


def valid_reading(timestamp: str = "2026-01-01T00:00:00Z") -> MeterReading:
    return MeterReading("VENUE-0001", timestamp, 30, 12.5, "verified")


class MeterDataTests(unittest.TestCase):
    def test_valid_reading_has_no_errors(self) -> None:
        self.assertEqual(validate_reading(valid_reading()), ())

    def test_reading_must_align_to_half_hour(self) -> None:
        errors = validate_reading(valid_reading("2026-01-01T00:12:00Z"))
        self.assertTrue(any("30-minute boundary" in error for error in errors))

    def test_missing_reading_has_no_fake_number(self) -> None:
        reading = MeterReading("VENUE-0001", "2026-01-01T00:00:00Z", 30, None, "missing")
        self.assertEqual(validate_reading(reading), ())

    def test_duplicate_timestamp_is_rejected(self) -> None:
        errors = validate_dataset([valid_reading(), valid_reading()])
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_csv_is_written_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "meter.csv"
            write_meter_csv([valid_reading()], path)
            self.assertIn("interval_start_utc", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
