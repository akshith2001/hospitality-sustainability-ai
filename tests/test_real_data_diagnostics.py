import unittest

from hospitality_ai.real_data_diagnostics import diagnose_venues
from test_real_data_evaluation import records


class RealDataDiagnosticTests(unittest.TestCase):
    def test_every_test_venue_is_diagnosed(self) -> None:
        diagnostics = diagnose_venues(records(), test_days=5)
        self.assertEqual([item.venue_id for item in diagnostics], ["VENUE-A", "VENUE-B"])
        self.assertTrue(all(item.training_rows == 15 for item in diagnostics))
        self.assertTrue(all(item.test_rows == 5 for item in diagnostics))

    def test_known_linear_pattern_is_reported_as_improved(self) -> None:
        diagnostics = diagnose_venues(records(), test_days=5)
        self.assertTrue(all(item.finding == "model_improved" for item in diagnostics))


if __name__ == "__main__":
    unittest.main()
