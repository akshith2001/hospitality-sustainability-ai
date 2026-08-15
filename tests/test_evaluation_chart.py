import tempfile
import unittest
from pathlib import Path

from hospitality_ai.evaluation_chart import write_actual_vs_predicted_chart


class EvaluationChartTests(unittest.TestCase):
    def test_accessible_svg_chart_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chart.svg"
            write_actual_vs_predicted_chart(path, rows=200, seed=7)
            content = path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("<title", content)
            self.assertIn("Predicted electricity (kWh/day)", content)
            self.assertIn("Actual electricity (kWh/day)", content)


if __name__ == "__main__":
    unittest.main()
