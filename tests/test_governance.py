import unittest

from hospitality_ai.governance import (
    approve_candidate,
    build_operational_view,
    evaluate_candidate,
    monitor_deployed_model,
)


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

    def test_large_performance_drop_pauses_recommendations(self) -> None:
        decision = monitor_deployed_model(20.0, 27.0, degradation_limit_pct=25.0)
        self.assertTrue(decision.recommendations_paused)
        self.assertIn("human review", decision.action)

    def test_performance_within_limit_continues_monitoring(self) -> None:
        decision = monitor_deployed_model(20.0, 24.0, degradation_limit_pct=25.0)
        self.assertFalse(decision.recommendations_paused)

    def test_invalid_monitoring_limit_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            monitor_deployed_model(20.0, 24.0, degradation_limit_pct=0)

    def test_verified_meter_remains_visible_when_ai_is_paused(self) -> None:
        view = build_operational_view("verified", "paused")
        self.assertTrue(view.show_raw_readings)
        self.assertFalse(view.show_ai_recommendations)

    def test_unverified_meter_hides_readings_and_recommendations(self) -> None:
        view = build_operational_view("unverified", "active")
        self.assertFalse(view.show_raw_readings)
        self.assertFalse(view.show_ai_recommendations)

    def test_verified_meter_and_active_ai_show_both(self) -> None:
        view = build_operational_view("verified", "active")
        self.assertTrue(view.show_raw_readings)
        self.assertTrue(view.show_ai_recommendations)


if __name__ == "__main__":
    unittest.main()
