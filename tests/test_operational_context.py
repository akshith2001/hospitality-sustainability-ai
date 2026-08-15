import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from hospitality_ai.operational_context import (
    DailyOperationalContext,
    validate_context,
    validate_context_dataset,
    write_context_csv,
)


def valid_context() -> DailyOperationalContext:
    return DailyOperationalContext(
        venue_id="VENUE-0001",
        utc_date="2026-01-01",
        customers=180,
        customers_quality="verified",
        opening_hours=12.0,
        outside_temperature_c=8.5,
        weather_station_id="WX-LONDON-01",
        special_event_category="wedding",
        equipment_change=False,
    )


class OperationalContextTests(unittest.TestCase):
    def test_valid_context_has_no_errors(self) -> None:
        self.assertEqual(validate_context(valid_context()), ())

    def test_impossible_opening_hours_are_rejected(self) -> None:
        errors = validate_context(replace(valid_context(), opening_hours=25.0))
        self.assertTrue(any("opening_hours" in error for error in errors))

    def test_duplicate_venue_date_is_rejected(self) -> None:
        errors = validate_context_dataset([valid_context(), valid_context()])
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_unknown_event_category_is_rejected(self) -> None:
        errors = validate_context(replace(valid_context(), special_event_category="party name"))
        self.assertTrue(any("event" in error for error in errors))

    def test_csv_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.csv"
            write_context_csv([valid_context()], path)
            self.assertIn("customers_quality", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
