import unittest
from datetime import date, timedelta

from hospitality_ai.real_data_evaluation import RealDailyRecord
from hospitality_ai.rolling_validation import (
    METHOD_NAMES,
    evaluate_rolling_validation,
    rolling_date_splits,
)


def records() -> list[RealDailyRecord]:
    values = []
    start = date(2025, 1, 1)
    for day in range(90):
        utc_date = (start + timedelta(days=day)).isoformat()
        for venue_id, offset in (("VENUE-A", 100.0), ("VENUE-B", 200.0)):
            temperature = float(day % 20)
            values.append(
                RealDailyRecord(
                    venue_id=venue_id,
                    utc_date=utc_date,
                    venue_type="hotel",
                    outside_temperature_c=temperature,
                    electricity_kwh=offset + day + 2.0 * temperature,
                )
            )
    return values


class RollingValidationTests(unittest.TestCase):
    def test_folds_end_before_the_reserved_test_period(self) -> None:
        reserved_start, folds = rolling_date_splits(
            records(), reserved_test_days=10, fold_days=10, fold_count=3
        )
        self.assertEqual(len(folds), 3)
        for training, validation in folds:
            self.assertLess(max(row.utc_date for row in training), min(row.utc_date for row in validation))
            self.assertLess(max(row.utc_date for row in validation), reserved_start)

    def test_every_candidate_and_venue_is_reported(self) -> None:
        result = evaluate_rolling_validation(
            records(), reserved_test_days=10, fold_days=10, fold_count=2
        )
        self.assertEqual(tuple(score.method for score in result.overall_scores), METHOD_NAMES)
        self.assertEqual({item.venue_id for item in result.venue_results}, {"VENUE-A", "VENUE-B"})
        self.assertEqual(len(result.folds), 2)

    def test_reserved_test_targets_cannot_change_validation_results(self) -> None:
        original = records()
        changed = [
            RealDailyRecord(
                venue_id=row.venue_id,
                utc_date=row.utc_date,
                venue_type=row.venue_type,
                outside_temperature_c=row.outside_temperature_c,
                electricity_kwh=(
                    row.electricity_kwh
                    if row.utc_date < "2025-03-22"
                    else 1_000_000.0
                ),
            )
            for row in original
        ]
        first = evaluate_rolling_validation(
            original, reserved_test_days=10, fold_days=10, fold_count=2
        )
        second = evaluate_rolling_validation(
            changed, reserved_test_days=10, fold_days=10, fold_count=2
        )
        self.assertEqual(first, second)

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            rolling_date_splits(records(), reserved_test_days=0)
        with self.assertRaises(ValueError):
            rolling_date_splits(
                records(), reserved_test_days=60, fold_days=30, fold_count=4
            )


if __name__ == "__main__":
    unittest.main()
