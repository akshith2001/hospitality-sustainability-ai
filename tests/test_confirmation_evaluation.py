import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from hospitality_ai.confirmation_evaluation import (
    ConfirmationMetadata,
    evaluate_frozen_confirmation,
    load_confirmation_metadata,
    meets_frozen_success_rule,
    validate_new_confirmation_period,
)
from hospitality_ai.real_data_evaluation import RealDailyRecord


def records() -> list[RealDailyRecord]:
    values = []
    start = date(2025, 1, 1)
    for day in range(130):
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


def metadata(**changes: object) -> ConfirmationMetadata:
    values = {
        "dataset_id": "independent-hospitality-2025",
        "dataset_title": "Independent hospitality sample",
        "source_url": "https://example.org/independent-data",
        "license": "CC-BY-4.0",
        "venue_inclusion_rule": "All hotels with complete temperature data",
        "confirmation_start_date": "2025-03-12",
        "confirmation_end_date": "2025-05-10",
        "outcomes_unseen_at_freeze": True,
    }
    values.update(changes)
    return ConfirmationMetadata(**values)


class ConfirmationEvaluationTests(unittest.TestCase):
    def test_all_methods_and_venues_are_reported(self) -> None:
        result = evaluate_frozen_confirmation(records(), metadata())
        self.assertEqual(result.confirmation_rows, 120)
        self.assertEqual(len(result.scores), 6)
        self.assertEqual(len(result.venue_results), 2)
        self.assertEqual(result.required_venue_wins, 1)

    def test_frozen_success_rule_requires_both_conditions(self) -> None:
        self.assertTrue(meets_frozen_success_rule(100.0, 95.0, 2, 4))
        self.assertFalse(meets_frozen_success_rule(100.0, 95.1, 2, 4))
        self.assertFalse(meets_frozen_success_rule(100.0, 90.0, 1, 4))

    def test_observed_bdg2_period_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_new_confirmation_period(
                metadata(
                    dataset_id="bdg2-v1.0",
                    confirmation_start_date="2017-11-02",
                    confirmation_end_date="2017-12-31",
                ),
                "2017-11-02",
                "2017-12-31",
            )

    def test_declared_dates_and_unseen_attestation_are_enforced(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_frozen_confirmation(
                records(), metadata(confirmation_start_date="2025-03-11")
            )
        with self.assertRaises(ValueError):
            evaluate_frozen_confirmation(
                records(), metadata(outcomes_unseen_at_freeze=False)
            )

    def test_at_least_sixty_confirmation_dates_are_required(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_frozen_confirmation(records(), metadata(), confirmation_days=59)

    def test_metadata_loader_rejects_missing_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps({"dataset_id": "incomplete"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_confirmation_metadata(path)


if __name__ == "__main__":
    unittest.main()
