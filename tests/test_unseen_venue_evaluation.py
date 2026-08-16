import unittest

from hospitality_ai.unseen_venue_evaluation import (
    UnseenVenueRecord,
    encode_features,
    evaluate_unseen_venues,
)


def sample_records() -> list[UnseenVenueRecord]:
    records = []
    venues = (
        ("FOOD-A", "food_service", 100.0, 30.0),
        ("FOOD-B", "food_service", 200.0, 30.0),
        ("HOTEL-A", "hotel", 300.0, 80.0),
        ("HOTEL-B", "hotel", 400.0, 80.0),
    )
    for day in range(1, 31):
        for venue_id, venue_type, area, type_offset in venues:
            temperature = float(day % 15)
            records.append(
                UnseenVenueRecord(
                    venue_id=venue_id,
                    utc_date=f"2026-01-{day:02d}",
                    venue_type=venue_type,
                    floor_area_sqm=area,
                    outside_temperature_c=temperature,
                    electricity_kwh=type_offset + 0.5 * area + 2.0 * temperature,
                )
            )
    return records


class UnseenVenueEvaluationTests(unittest.TestCase):
    def test_features_do_not_include_venue_identity(self) -> None:
        left, right = sample_records()[0], sample_records()[1]
        right = UnseenVenueRecord(
            venue_id="A-DIFFERENT-ID",
            utc_date=left.utc_date,
            venue_type=left.venue_type,
            floor_area_sqm=left.floor_area_sqm,
            outside_temperature_c=left.outside_temperature_c,
            electricity_kwh=left.electricity_kwh,
        )
        self.assertEqual(encode_features(left), encode_features(right))

    def test_each_venue_is_removed_completely_from_its_training_set(self) -> None:
        result = evaluate_unseen_venues(
            sample_records(), venue_ids=("FOOD-B", "HOTEL-B")
        )
        self.assertEqual([item.test_rows for item in result.results], [30, 30])
        self.assertEqual([item.training_rows for item in result.results], [90, 90])

    def test_linear_pattern_beats_type_mean_for_both_unseen_venues(self) -> None:
        result = evaluate_unseen_venues(
            sample_records(), venue_ids=("FOOD-B", "HOTEL-B")
        )
        self.assertTrue(result.success_on_every_venue)
        self.assertTrue(all(item.model_beats_baseline for item in result.results))

    def test_duplicate_or_missing_venues_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_unseen_venues(sample_records(), venue_ids=("FOOD-A", "FOOD-A"))
        with self.assertRaises(ValueError):
            evaluate_unseen_venues(sample_records(), venue_ids=("UNKNOWN",))


if __name__ == "__main__":
    unittest.main()
