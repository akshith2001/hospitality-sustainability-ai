import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from hospitality_ai.meter_data import MeterReading
from hospitality_ai.venue_data_readiness import (
    import_supplier_intervals,
    load_daily_weather,
    prepare_daily_records,
    write_daily_records,
)


def complete_day(day: date, kwh: float = 1.0) -> list[MeterReading]:
    return [
        MeterReading(
            "VENUE-0001",
            f"{day.isoformat()}T{interval // 2:02d}:{(interval % 2) * 30:02d}:00Z",
            30,
            kwh,
            "verified",
        )
        for interval in range(48)
    ]


class VenueDataReadinessTests(unittest.TestCase):
    def test_supplier_columns_units_and_timezones_are_normalised(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplier.csv"
            path.write_text(
                "When,Usage Wh,State\n"
                "2026-01-01T01:00:00+01:00,1250,verified\n",
                encoding="utf-8",
            )
            rows = import_supplier_intervals(
                path, "VENUE-0001", "When", "Usage Wh", "wh", "State"
            )
        self.assertEqual(rows[0].interval_start_utc, "2026-01-01T00:00:00Z")
        self.assertEqual(rows[0].electricity_kwh, 1.25)

    def test_supplier_export_requires_timezone_and_known_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplier.csv"
            path.write_text("timestamp,value\n2026-01-01T00:00:00,1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "UTC offset"):
                import_supplier_intervals(path, "VENUE-0001", "timestamp", "value")

    def test_weather_loader_rejects_duplicate_dates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weather.csv"
            path.write_text(
                "utc_date,outside_temperature_c\n"
                "2026-01-01,8\n2026-01-01,9\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_daily_weather(path)

    def test_ready_when_ninety_complete_weather_matched_dates_exist(self) -> None:
        start = date(2026, 1, 1)
        days = [start + timedelta(days=offset) for offset in range(90)]
        readings = [row for day in days for row in complete_day(day)]
        weather = {day.isoformat(): 10.0 for day in days}
        records, report = prepare_daily_records(readings, weather, "hotel")
        self.assertEqual(len(records), 90)
        self.assertTrue(report.ready_for_frozen_confirmation)
        self.assertEqual(report.required_confirmation_dates, 60)

    def test_incomplete_and_weather_missing_dates_are_reported_not_invented(self) -> None:
        day_one = date(2026, 1, 1)
        day_two = date(2026, 1, 2)
        readings = complete_day(day_one) + complete_day(day_two)[:-1]
        records, report = prepare_daily_records(readings, {}, "restaurant")
        self.assertEqual(records, [])
        self.assertEqual(report.incomplete_dates, 1)
        self.assertEqual(report.complete_dates_missing_weather, 1)
        self.assertFalse(report.ready_for_frozen_confirmation)
        self.assertTrue(any("weather" in reason for reason in report.reasons))

    def test_each_run_is_limited_to_one_anonymous_venue(self) -> None:
        readings = complete_day(date(2026, 1, 1))
        readings.append(
            MeterReading("VENUE-0002", "2026-01-02T00:00:00Z", 30, 1.0, "verified")
        )
        with self.assertRaisesRegex(ValueError, "one pseudonymous venue"):
            prepare_daily_records(readings, {}, "hotel")

    def test_daily_output_matches_confirmation_loader_schema(self) -> None:
        day = date(2026, 1, 1)
        records, _ = prepare_daily_records(
            complete_day(day), {day.isoformat(): 12.5}, "cafe"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "daily.csv"
            write_daily_records(records, path)
            with path.open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
        self.assertEqual(row["venue_id"], "VENUE-0001")
        self.assertEqual(row["utc_date"], "2026-01-01")
        self.assertEqual(float(row["electricity_kwh"]), 48.0)


if __name__ == "__main__":
    unittest.main()
