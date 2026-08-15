"""Human approval gate for promoting a newly trained candidate model."""

from __future__ import annotations

from dataclasses import dataclass, replace


APPROVER_ROLES = frozenset({"research", "sustainability", "model_governance"})


@dataclass(frozen=True)
class ModelPromotion:
    current_mae_kwh: float
    candidate_mae_kwh: float
    current_worst_venue_mae_kwh: float
    candidate_worst_venue_mae_kwh: float
    evaluation_passed: bool
    evaluation_reason: str
    approved_by_role: str | None = None

    @property
    def eligible_for_deployment(self) -> bool:
        return self.evaluation_passed and self.approved_by_role is not None


@dataclass(frozen=True)
class MonitoringDecision:
    approved_mae_kwh: float
    observed_mae_kwh: float
    degradation_limit_pct: float
    recommendations_paused: bool
    action: str


def evaluate_candidate(
    current_mae_kwh: float,
    candidate_mae_kwh: float,
    current_worst_venue_mae_kwh: float,
    candidate_worst_venue_mae_kwh: float,
) -> ModelPromotion:
    """Evaluate aggregate and worst-venue accuracy before any human decision."""
    values = (
        current_mae_kwh,
        candidate_mae_kwh,
        current_worst_venue_mae_kwh,
        candidate_worst_venue_mae_kwh,
    )
    if any(value < 0 for value in values):
        raise ValueError("MAE values cannot be negative")
    if candidate_mae_kwh >= current_mae_kwh:
        passed = False
        reason = "Candidate does not improve overall MAE."
    elif candidate_worst_venue_mae_kwh > current_worst_venue_mae_kwh:
        passed = False
        reason = "Candidate worsens performance for the worst-performing venue."
    else:
        passed = True
        reason = "Candidate improves overall MAE without worsening worst-venue MAE."
    return ModelPromotion(
        current_mae_kwh=current_mae_kwh,
        candidate_mae_kwh=candidate_mae_kwh,
        current_worst_venue_mae_kwh=current_worst_venue_mae_kwh,
        candidate_worst_venue_mae_kwh=candidate_worst_venue_mae_kwh,
        evaluation_passed=passed,
        evaluation_reason=reason,
    )


def approve_candidate(promotion: ModelPromotion, approver_role: str) -> ModelPromotion:
    """Record approval only after the candidate has passed evaluation."""
    if not promotion.evaluation_passed:
        raise ValueError("A candidate that failed evaluation cannot be approved")
    if approver_role not in APPROVER_ROLES:
        raise ValueError("Approver role is not authorised")
    return replace(promotion, approved_by_role=approver_role)


def monitor_deployed_model(
    approved_mae_kwh: float,
    observed_mae_kwh: float,
    degradation_limit_pct: float = 25.0,
) -> MonitoringDecision:
    """Pause recommendations when observed error exceeds the approved tolerance."""
    if approved_mae_kwh <= 0 or observed_mae_kwh < 0:
        raise ValueError("MAE values must be valid and approved_mae_kwh must be positive")
    if degradation_limit_pct <= 0:
        raise ValueError("degradation_limit_pct must be positive")
    limit = approved_mae_kwh * (1 + degradation_limit_pct / 100)
    paused = observed_mae_kwh > limit
    action = (
        "Pause recommendations and request human review; continue collecting data."
        if paused
        else "Continue monitored operation."
    )
    return MonitoringDecision(
        approved_mae_kwh=approved_mae_kwh,
        observed_mae_kwh=observed_mae_kwh,
        degradation_limit_pct=degradation_limit_pct,
        recommendations_paused=paused,
        action=action,
    )
