import json
import tempfile
import unittest
from pathlib import Path

from hospitality_ai.synthetic_confirmation_demo import (
    DEMO_WARNING,
    run_synthetic_confirmation_demo,
)


class SyntheticConfirmationDemoTests(unittest.TestCase):
    def test_rehearsal_exercises_complete_pipeline_and_labels_every_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "demo"
            result = run_synthetic_confirmation_demo(output, days=90, seed=7)
            self.assertTrue(result.ready_for_frozen_confirmation)
            self.assertEqual(result.supplier_interval_rows, 90 * 48)
            self.assertEqual(result.prepared_daily_rows, 90)
            expected = {
                "synthetic_supplier_export.csv",
                "synthetic_daily_weather.csv",
                "synthetic_prepared_daily.csv",
                "synthetic_confirmation_metadata.json",
                "synthetic_confirmation_report.json",
                "synthetic_demo_summary.json",
                "README.txt",
            }
            self.assertEqual({path.name for path in output.iterdir()}, expected)
            self.assertIn(DEMO_WARNING, (output / "README.txt").read_text())
            report = json.loads(
                (output / "synthetic_confirmation_report.json").read_text()
            )
            self.assertEqual(report["metadata"]["dataset_title"], DEMO_WARNING)
            self.assertEqual(
                {score["method"] for score in report["scores"]},
                {
                    "per_venue_mean",
                    "previous_day",
                    "seven_day_rolling_mean",
                    "same_weekday_last_week",
                    "seasonal_linear_model",
                    "lag_feature_model",
                },
            )

    def test_rehearsal_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            run_synthetic_confirmation_demo(first, days=90, seed=11)
            run_synthetic_confirmation_demo(second, days=90, seed=11)
            self.assertEqual(
                (first / "synthetic_confirmation_report.json").read_text(),
                (second / "synthetic_confirmation_report.json").read_text(),
            )

    def test_rehearsal_rejects_too_few_dates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "at least 90"):
                run_synthetic_confirmation_demo(Path(directory), days=89)


if __name__ == "__main__":
    unittest.main()
