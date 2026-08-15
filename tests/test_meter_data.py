import tempfile
import unittest
from pathlib import Path

from hospitality_ai.meter_data import (
    MeterReading,
    primary_evaluation_readings,
    sensitivity_evaluation_readings,
    summarise_utc_day,
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

    def test_primary_evaluation_uses_only_verified_values(self) -> None:
        estimated = MeterReading(
            "VENUE-0001", "2026-01-01T00:30:00Z", 30, 12.8, "estimated"
        )
        readings = [valid_reading(), estimated]
        self.assertEqual(primary_evaluation_readings(readings), [valid_reading()])
        self.assertEqual(len(sensitivity_evaluation_readings(readings)), 2)

    def test_forty_seven_readings_are_kept_as_incomplete(self) -> None:
        readings = []
        for interval in range(47):
            hour, minute_index = divmod(interval, 2)
            readings.append(
                valid_reading(f"2026-01-01T{hour:02d}:{minute_index * 30:02d}:00Z")
            )
        summary = summarise_utc_day(readings)
        self.assertEqual(summary.quality_status, "incomplete")
        self.assertEqual(summary.unavailable_intervals, 1)
        self.assertAlmostEqual(summary.coverage_pct, 47 / 48 * 100)

    def test_forty_eight_verified_readings_are_complete(self) -> None:
        readings = []
        for interval in range(48):
            hour, minute_index = divmod(interval, 2)
            readings.append(
                valid_reading(f"2026-01-01T{hour:02d}:{minute_index * 30:02d}:00Z")
            )
        summary = summarise_utc_day(readings)
        self.assertEqual(summary.quality_status, "complete_verified")
        self.assertEqual(summary.coverage_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
