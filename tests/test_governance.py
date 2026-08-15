import unittest

from hospitality_ai.governance import approve_candidate, evaluate_candidate


class GovernanceTests(unittest.TestCase):
    def test_passing_evaluation_still_requires_human_approval(self) -> None:
        promotion = evaluate_candidate(25.0, 22.0, 35.0, 34.0)
        self.assertTrue(promotion.evaluation_passed)
        self.assertFalse(promotion.eligible_for_deployment)
        approved = approve_candidate(promotion, "research")
        self.assertTrue(approved.eligible_for_deployment)

    def test_worse_overall_model_fails(self) -> None:
        promotion = evaluate_candidate(25.0, 26.0, 35.0, 34.0)
        self.assertFalse(promotion.evaluation_passed)

    def test_worse_worst_venue_fails_despite_better_average(self) -> None:
        promotion = evaluate_candidate(25.0, 22.0, 35.0, 40.0)
        self.assertFalse(promotion.evaluation_passed)
        self.assertIn("worst-performing venue", promotion.evaluation_reason)

    def test_failed_candidate_cannot_be_approved(self) -> None:
        promotion = evaluate_candidate(25.0, 26.0, 35.0, 40.0)
        with self.assertRaises(ValueError):
            approve_candidate(promotion, "research")


if __name__ == "__main__":
    unittest.main()
