import unittest

from hospitality_ai.decision_sensitivity import analyse_weight_sensitivity


class DecisionSensitivityTests(unittest.TestCase):
    def test_all_weight_combinations_are_counted(self) -> None:
        result = analyse_weight_sensitivity(416.05, 1_500.0, step=0.10)
        self.assertEqual(sum(count for _, count in result.winner_counts), result.combinations)
        self.assertEqual(result.combinations, 66)

    def test_default_winner_share_is_a_probability(self) -> None:
        result = analyse_weight_sensitivity(416.05, 1_500.0, step=0.10)
        self.assertGreater(result.default_winner_share, 0)
        self.assertLessEqual(result.default_winner_share, 1)

    def test_invalid_step_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            analyse_weight_sensitivity(416.05, 1_500.0, step=0.3)


if __name__ == "__main__":
    unittest.main()
