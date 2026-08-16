import unittest

from hospitality_ai.lag_feature_model import (
    build_lagged_test_observations,
    build_lagged_training_observations,
    fit_lag_feature_model,
)
from hospitality_ai.real_data_evaluation import RealDailyRecord
from hospitality_ai.time_series_baselines import predict_time_series_baselines


def record(day: int, value: float, venue_id: str = "VENUE-A") -> RealDailyRecord:
    return RealDailyRecord(
        venue_id=venue_id,
        utc_date=f"2026-01-{day:02d}",
        venue_type="hotel",
        outside_temperature_c=float(day),
        electricity_kwh=value,
    )


class LagFeatureModelTests(unittest.TestCase):
    def test_training_lags_use_only_earlier_targets(self) -> None:
        observations = build_lagged_training_observations(
            [record(day, float(day)) for day in range(1, 10)]
        )
        day_eight = next(item for item in observations if item.utc_date == "2026-01-08")
        self.assertEqual(day_eight.previous_day_kwh, 7.0)
        self.assertEqual(day_eight.same_weekday_last_week_kwh, 1.0)
        self.assertEqual(day_eight.seven_day_rolling_mean_kwh, 4.0)

    def test_future_target_does_not_change_earlier_training_features(self) -> None:
        original = [record(day, float(day)) for day in range(1, 10)]
        changed = original[:-1] + [record(9, 1_000_000.0)]
        first = build_lagged_training_observations(original)
        second = build_lagged_training_observations(changed)
        self.assertEqual(first[-1].previous_day_kwh, second[-1].previous_day_kwh)
        self.assertEqual(
            first[-1].seven_day_rolling_mean_kwh,
            second[-1].seven_day_rolling_mean_kwh,
        )
        self.assertEqual(
            first[-1].same_weekday_last_week_kwh,
            second[-1].same_weekday_last_week_kwh,
        )

    def test_test_features_preserve_leakage_safe_baseline_lags(self) -> None:
        training = [record(day, float(day)) for day in range(1, 9)]
        test = [record(9, 90.0), record(10, 100.0)]
        predictions = predict_time_series_baselines(training, test)
        observations = build_lagged_test_observations(test, predictions)
        self.assertEqual(observations[0].previous_day_kwh, 8.0)
        self.assertEqual(observations[1].previous_day_kwh, 90.0)

    def test_model_fits_and_predicts_lagged_rows(self) -> None:
        training = []
        for day in range(1, 31):
            for venue_id, offset in (("VENUE-A", 100.0), ("VENUE-B", 200.0)):
                training.append(record(day, offset + day, venue_id))
        model = fit_lag_feature_model(training)
        test = [record(31, 131.0), record(31, 231.0, "VENUE-B")]
        predictions = predict_time_series_baselines(training, test)
        observations = build_lagged_test_observations(test, predictions)
        self.assertEqual(len([model.predict(item) for item in observations]), 2)


if __name__ == "__main__":
    unittest.main()
