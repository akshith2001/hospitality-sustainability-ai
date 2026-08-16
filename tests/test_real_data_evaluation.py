import unittest

from hospitality_ai.real_data_evaluation import (
    RealDailyRecord,
    chronological_split,
    evaluate_real_data,
)


def records() -> list[RealDailyRecord]:
    values = []
    for day in range(1, 21):
        date = f"2026-01-{day:02d}"
        for venue_id, offset in (("VENUE-A", 100.0), ("VENUE-B", 200.0)):
            temperature = float(day)
            values.append(
                RealDailyRecord(
                    venue_id=venue_id,
                    utc_date=date,
                    venue_type="food_service",
                    outside_temperature_c=temperature,
                    electricity_kwh=offset + 2.0 * temperature,
                )
            )
    return values


class RealDataEvaluationTests(unittest.TestCase):
    def test_split_reserves_newest_dates_for_every_venue(self) -> None:
        training, test = chronological_split(records(), test_days=5)
        self.assertEqual(max(record.utc_date for record in training), "2026-01-15")
        self.assertEqual(min(record.utc_date for record in test), "2026-01-16")
        self.assertEqual({record.venue_id for record in test}, {"VENUE-A", "VENUE-B"})

    def test_model_beats_per_venue_mean_on_known_linear_pattern(self) -> None:
        result = evaluate_real_data(records(), test_days=5)
        self.assertLess(result.model_mae_kwh, result.baseline_mae_kwh)
        self.assertEqual(len(result.venue_results), 2)

    def test_reports_all_leakage_safe_time_series_baselines(self) -> None:
        result = evaluate_real_data(records(), test_days=5)
        self.assertIsNotNone(result.previous_day_mae_kwh)
        self.assertIsNotNone(result.seven_day_rolling_mean_mae_kwh)
        self.assertIsNotNone(result.same_weekday_last_week_mae_kwh)

    def test_invalid_test_period_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            chronological_split(records(), test_days=0)


if __name__ == "__main__":
    unittest.main()
