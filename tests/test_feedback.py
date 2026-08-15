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

    def test_unanimous_approval_is_required_for_training(self) -> None:
        feedback = submit_feedback(
            "alert-1", "venue-1", "confirmed_waste", "Equipment switched off"
        )
        feedback = review_feedback(feedback, "manager", "approved")
        feedback = review_feedback(feedback, "sustainability", "approved")
        self.assertFalse(feedback.eligible_for_training)
        feedback = review_feedback(feedback, "research", "approved")
        self.assertTrue(feedback.eligible_for_training)

    def test_one_rejection_prevents_training_use(self) -> None:
        feedback = submit_feedback("alert-1", "venue-1", "unknown", "None")
        feedback = review_feedback(feedback, "manager", "approved")
        feedback = review_feedback(feedback, "sustainability", "rejected")
        feedback = review_feedback(feedback, "research", "approved")
        self.assertEqual(feedback.review_status, "rejected")
        self.assertFalse(feedback.eligible_for_training)

    def test_unknown_category_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            submit_feedback("alert-1", "venue-1", "guess", "None")

    def test_pending_is_not_a_review_decision(self) -> None:
        feedback = submit_feedback("alert-1", "venue-1", "unknown", "None")
        with self.assertRaises(ValueError):
            review_feedback(feedback, "manager", "pending")

    def test_unknown_reviewer_role_is_rejected(self) -> None:
        feedback = submit_feedback("alert-1", "venue-1", "unknown", "None")
        with self.assertRaises(ValueError):
            review_feedback(feedback, "owner", "approved")


if __name__ == "__main__":
    unittest.main()
