import unittest

from hospitality_ai.real_data_evaluation import RealDailyRecord
from hospitality_ai.time_series_baselines import predict_time_series_baselines


def record(day: int, value: float, venue_id: str = "VENUE-A") -> RealDailyRecord:
    return RealDailyRecord(
        venue_id=venue_id,
        utc_date=f"2026-01-{day:02d}",
        venue_type="hotel",
        outside_temperature_c=10.0,
        electricity_kwh=value,
    )


class TimeSeriesBaselineTests(unittest.TestCase):
    def test_expected_lags_and_rolling_mean_are_used(self) -> None:
        training = [record(day, float(day)) for day in range(1, 9)]
        predictions = predict_time_series_baselines(training, [record(9, 90.0)])
        self.assertEqual(predictions.previous_day_kwh, (8.0,))
        self.assertEqual(predictions.seven_day_rolling_mean_kwh, (5.0,))
        self.assertEqual(predictions.same_weekday_last_week_kwh, (2.0,))

    def test_later_test_dates_only_use_already_observed_test_values(self) -> None:
        training = [record(day, float(day)) for day in range(1, 9)]
        test = [record(9, 90.0), record(10, 100.0)]
        predictions = predict_time_series_baselines(training, test)
        self.assertEqual(predictions.previous_day_kwh, (8.0, 90.0))
        self.assertEqual(predictions.same_weekday_last_week_kwh, (2.0, 3.0))
        self.assertAlmostEqual(
            predictions.seven_day_rolling_mean_kwh[1],
            (3.0 + 4.0 + 5.0 + 6.0 + 7.0 + 8.0 + 90.0) / 7,
        )

    def test_future_rows_do_not_change_an_earlier_prediction(self) -> None:
        training = [record(day, float(day)) for day in range(1, 9)]
        first = predict_time_series_baselines(training, [record(9, 90.0)])
        with_future = predict_time_series_baselines(
            training, [record(9, 90.0), record(10, 100_000.0)]
        )
        self.assertEqual(first.previous_day_kwh[0], with_future.previous_day_kwh[0])
        self.assertEqual(
            first.seven_day_rolling_mean_kwh[0],
            with_future.seven_day_rolling_mean_kwh[0],
        )
        self.assertEqual(
            first.same_weekday_last_week_kwh[0],
            with_future.same_weekday_last_week_kwh[0],
        )

    def test_missing_lags_fall_back_to_training_only_venue_mean(self) -> None:
        training = [record(1, 10.0), record(3, 30.0)]
        predictions = predict_time_series_baselines(training, [record(10, 999.0)])
        self.assertEqual(predictions.previous_day_kwh, (20.0,))
        self.assertEqual(predictions.same_weekday_last_week_kwh, (30.0,))
        self.assertEqual(predictions.seven_day_rolling_mean_kwh, (20.0,))

    def test_unseen_test_venue_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            predict_time_series_baselines(
                [record(1, 10.0)], [record(2, 20.0, venue_id="VENUE-B")]
            )

    def test_training_must_end_before_the_test_period(self) -> None:
        with self.assertRaises(ValueError):
            predict_time_series_baselines([record(3, 30.0)], [record(2, 20.0)])


if __name__ == "__main__":
    unittest.main()
