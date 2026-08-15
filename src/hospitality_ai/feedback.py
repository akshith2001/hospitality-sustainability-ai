"""Privacy-preserving human review for feedback about electricity alerts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import uuid4


CAUSE_CATEGORIES = frozenset(
    {
        "confirmed_waste",
        "equipment_fault",
        "special_event",
        "incorrect_data",
        "normal_operation",
        "unknown",
    }
)
REVIEW_STATUSES = frozenset({"pending", "approved", "rejected"})


@dataclass(frozen=True)
class AnonymousFeedback:
    feedback_id: str
    alert_id: str
    venue_id: str
    submitted_at_utc: str
    cause_category: str
    action_taken: str
    notes: str
    review_status: str = "pending"

    @property
    def eligible_for_training(self) -> bool:
        return self.review_status == "approved"


def submit_feedback(
    alert_id: str,
    venue_id: str,
    cause_category: str,
    action_taken: str,
    notes: str = "",
) -> AnonymousFeedback:
    """Create feedback without collecting employee identity or device details."""
    if cause_category not in CAUSE_CATEGORIES:
        raise ValueError(f"Unknown cause category: {cause_category}")
    if not alert_id.strip() or not venue_id.strip():
        raise ValueError("alert_id and venue_id are required")
    return AnonymousFeedback(
        feedback_id=str(uuid4()),
        alert_id=alert_id.strip(),
        venue_id=venue_id.strip(),
        submitted_at_utc=datetime.now(timezone.utc).isoformat(),
        cause_category=cause_category,
        action_taken=action_taken.strip(),
        notes=notes.strip(),
    )


def review_feedback(feedback: AnonymousFeedback, decision: str) -> AnonymousFeedback:
    """Record an approval or rejection before feedback can influence training."""
    if decision not in REVIEW_STATUSES - {"pending"}:
        raise ValueError("decision must be approved or rejected")
    return replace(feedback, review_status=decision)
