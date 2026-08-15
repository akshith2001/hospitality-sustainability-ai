import unittest

from hospitality_ai.recommend import rank_interventions


class RecommendationTests(unittest.TestCase):
    def test_results_are_ranked_highest_score_first(self) -> None:
        ranked = rank_interventions(400.0, 2_000.0)
        self.assertGreater(len(ranked), 1)
        self.assertEqual(
            [item.overall_score for item in ranked],
            sorted((item.overall_score for item in ranked), reverse=True),
        )

    def test_budget_excludes_expensive_options(self) -> None:
        ranked = rank_interventions(400.0, 500.0)
        self.assertTrue(ranked)
        self.assertTrue(all(item.implementation_cost_gbp <= 500.0 for item in ranked))

    def test_no_affordable_option_returns_empty_list(self) -> None:
        self.assertEqual(rank_interventions(400.0, 100.0), [])

    def test_weights_must_sum_to_one(self) -> None:
        with self.assertRaises(ValueError):
            rank_interventions(400.0, 2_000.0, emissions_weight=0.5)


if __name__ == "__main__":
    unittest.main()
