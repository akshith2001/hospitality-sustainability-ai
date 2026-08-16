import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hospitality_ai.real_data_chart import write_real_data_chart
from hospitality_ai.real_data_evaluation import RealDataEvaluation, VenueEvaluation


class RealDataChartTests(unittest.TestCase):
    @patch("hospitality_ai.real_data_chart.load_real_daily_records", return_value=[])
    @patch("hospitality_ai.real_data_chart.evaluate_real_data")
    def test_accessible_chart_is_written(self, evaluate, _load) -> None:
        evaluate.return_value = RealDataEvaluation(
            training_rows=100,
            test_rows=20,
            training_end_date="2026-01-10",
            test_start_date="2026-01-11",
            baseline_mae_kwh=20.0,
            model_mae_kwh=15.0,
            improvement_pct=25.0,
            venue_results=(VenueEvaluation("VENUE-A", 10, 20.0, 15.0),),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chart.svg"
            write_real_data_chart(Path("unused.csv"), output)
            svg = output.read_text(encoding="utf-8")
            self.assertIn("<title", svg)
            self.assertIn("Overall improvement: 25.0%", svg)


if __name__ == "__main__":
    unittest.main()
