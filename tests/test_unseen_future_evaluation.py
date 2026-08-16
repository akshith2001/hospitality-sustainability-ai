import unittest

from hospitality_ai.unseen_future_evaluation import (
    evaluate_unseen_future,
    split_unseen_future,
)
from hospitality_ai.unseen_venue_evaluation import UnseenVenueRecord


def sample_records() -> list[UnseenVenueRecord]:
    records = []
    venues = (
        ("FOOD-A", "food_service", 100.0, 30.0),
        ("FOOD-B", "food_service", 200.0, 30.0),
        ("HOTEL-A", "hotel", 300.0, 80.0),
        ("HOTEL-B", "hotel", 400.0, 80.0),
    )
    for day in range(1, 101):
        month = 1 + (day - 1) // 28
        month_day = 1 + (day - 1) % 28
        utc_date = f"2026-{month:02d}-{month_day:02d}"
        for venue_id, venue_type, area, type_offset in venues:
            temperature = float(day % 15)
            records.append(
                UnseenVenueRecord(
                    venue_id=venue_id,
                    utc_date=utc_date,
                    venue_type=venue_type,
                    floor_area_sqm=area,
                    outside_temperature_c=temperature,
                    electricity_kwh=type_offset + 0.5 * area + 2.0 * temperature,
                )
            )
    return records


class UnseenFutureEvaluationTests(unittest.TestCase):
    def test_split_removes_held_out_venue_and_future_dates(self) -> None:
        training, test = split_unseen_future(sample_records(), "FOOD-B", test_days=20)
        self.assertEqual(len(test), 20)
        self.assertNotIn("FOOD-B", {record.venue_id for record in training})
        self.assertLess(
            max(record.utc_date for record in training),
            min(record.utc_date for record in test),
        )

    def test_both_locked_venues_must_beat_their_baselines(self) -> None:
        result = evaluate_unseen_future(
            sample_records(), venue_ids=("FOOD-B", "HOTEL-B"), test_days=20
        )
        self.assertTrue(result.success_on_every_venue)
        self.assertTrue(all(item.model_beats_baseline for item in result.results))

    def test_each_result_records_the_time_boundary(self) -> None:
        result = evaluate_unseen_future(
            sample_records(), venue_ids=("FOOD-B", "HOTEL-B"), test_days=20
        )
        for item in result.results:
            self.assertLess(item.training_end_date, item.test_start_date)
            self.assertLessEqual(item.test_start_date, item.test_end_date)

    def test_invalid_period_and_duplicate_venues_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_unseen_future(sample_records(), "FOOD-A", test_days=0)
        with self.assertRaises(ValueError):
            evaluate_unseen_future(
                sample_records(), venue_ids=("FOOD-A", "FOOD-A"), test_days=20
            )


if __name__ == "__main__":
    unittest.main()
