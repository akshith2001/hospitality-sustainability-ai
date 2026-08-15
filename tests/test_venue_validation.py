import unittest

from hospitality_ai.synthetic_data import generate_records
from hospitality_ai.venue_validation import (
    evaluate_all_venues,
    evaluate_held_out_venue,
    leave_one_venue_out_split,
)


class VenueValidationTests(unittest.TestCase):
    def test_held_out_venue_never_appears_in_training(self) -> None:
        records = generate_records(2_000, seed=2026)
        training, test = leave_one_venue_out_split(records, "VENUE-001")
        self.assertTrue(test)
        self.assertNotIn("VENUE-001", {record.venue_id for record in training})
        self.assertEqual({record.venue_id for record in test}, {"VENUE-001"})

    def test_model_beats_baseline_on_held_out_venue(self) -> None:
        result = evaluate_held_out_venue(
            generate_records(2_000, seed=2026), "VENUE-001"
        )
        self.assertLess(result.model_mae_kwh, result.baseline_mae_kwh)

    def test_missing_venue_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            leave_one_venue_out_split(generate_records(100), "VENUE-999")

    def test_every_venue_is_reported(self) -> None:
        records = generate_records(2_000, seed=2026)
        expected_ids = {record.venue_id for record in records}
        summary = evaluate_all_venues(records)
        reported_ids = {result.held_out_venue_id for result in summary.results}
        self.assertEqual(reported_ids, expected_ids)
        self.assertIn(summary.best_venue_id, expected_ids)
        self.assertIn(summary.worst_venue_id, expected_ids)


if __name__ == "__main__":
    unittest.main()
