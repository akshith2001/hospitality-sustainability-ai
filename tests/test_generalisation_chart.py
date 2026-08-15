import tempfile
import unittest
from pathlib import Path

from hospitality_ai.generalisation_chart import (
    collect_evaluation_pairs,
    write_generalisation_chart,
)


class GeneralisationChartTests(unittest.TestCase):
    def test_all_documented_evaluations_are_reported(self) -> None:
        pairs = collect_evaluation_pairs(seed=2026)
        self.assertEqual(len(pairs), 3)
        self.assertTrue(all(pair.model_mae_kwh < pair.baseline_mae_kwh for pair in pairs))

    def test_accessible_svg_chart_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "generalisation.svg"
            write_generalisation_chart(path, seed=2026)
            content = path.read_text(encoding="utf-8")
            self.assertIn("<title", content)
            self.assertIn("Mean baseline", content)
            self.assertIn("Linear regression", content)
            self.assertIn("Held-out venue mean", content)
            self.assertIn("not real-world accuracy", content)


if __name__ == "__main__":
    unittest.main()
