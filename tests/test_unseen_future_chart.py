import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hospitality_ai.unseen_future_chart import write_unseen_future_chart
from hospitality_ai.unseen_future_evaluation import (
    UnseenFutureEvaluation,
    UnseenFutureResult,
)


class UnseenFutureChartTests(unittest.TestCase):
    @patch("hospitality_ai.unseen_future_chart.load_unseen_venue_records", return_value=[])
    @patch("hospitality_ai.unseen_future_chart.evaluate_unseen_future")
    def test_accessible_chart_contains_both_results(self, evaluate, _load) -> None:
        evaluate.return_value = UnseenFutureEvaluation(
            test_days=60,
            results=(
                UnseenFutureResult(
                    "FOOD", "food_service", 100, 60, "2025-12-31", "2026-01-01",
                    "2026-03-01", 658.50, 389.82, 40.8, True,
                ),
                UnseenFutureResult(
                    "HOTEL", "hotel", 100, 60, "2025-12-31", "2026-01-01",
                    "2026-03-01", 1019.06, 506.20, 50.3, True,
                ),
            ),
            success_on_every_venue=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chart.svg"
            write_unseen_future_chart(Path("unused.csv"), output)
            svg = output.read_text(encoding="utf-8")
            self.assertIn("<title", svg)
            self.assertIn("40.8% lower MAE", svg)
            self.assertIn("50.3% lower MAE", svg)


if __name__ == "__main__":
    unittest.main()
