import unittest

from hospitality_ai.feedback import review_feedback, submit_feedback


class FeedbackTests(unittest.TestCase):
    def test_new_feedback_is_anonymous_and_pending(self) -> None:
        feedback = submit_feedback(
            "alert-1", "venue-1", "equipment_fault", "Engineer contacted"
        )
        self.assertEqual(feedback.review_status, "pending")
        self.assertFalse(feedback.eligible_for_training)
        self.assertFalse(hasattr(feedback, "employee_name"))
        self.assertFalse(hasattr(feedback, "email"))
        self.assertFalse(hasattr(feedback, "ip_address"))

    def test_only_approved_feedback_is_eligible_for_training(self) -> None:
        feedback = submit_feedback(
            "alert-1", "venue-1", "confirmed_waste", "Equipment switched off"
        )
        self.assertTrue(review_feedback(feedback, "approved").eligible_for_training)
        self.assertFalse(review_feedback(feedback, "rejected").eligible_for_training)

    def test_unknown_category_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            submit_feedback("alert-1", "venue-1", "guess", "None")

    def test_pending_is_not_a_review_decision(self) -> None:
        feedback = submit_feedback("alert-1", "venue-1", "unknown", "None")
        with self.assertRaises(ValueError):
            review_feedback(feedback, "pending")


if __name__ == "__main__":
    unittest.main()
