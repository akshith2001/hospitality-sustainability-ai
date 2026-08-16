"""Locked evaluation of the frozen candidate on genuinely new daily data."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .lag_feature_model import (
    build_lagged_test_observations,
    fit_lag_feature_model,
)
from .real_data_evaluation import (
    RealDailyRecord,
    chronological_split,
    fit_real_linear_model,
    load_real_daily_records,
    mean_absolute_error,
)
from .time_series_baselines import predict_time_series_baselines


OBSERVED_BDG2_DATASET_ID = "bdg2-v1.0"
OBSERVED_BDG2_END_DATE = "2017-12-31"
MINIMUM_CONFIRMATION_DAYS = 60


@dataclass(frozen=True)
class ConfirmationMetadata:
    dataset_id: str
    dataset_title: str
    source_url: str
    license: str
    venue_inclusion_rule: str
    confirmation_start_date: str
    confirmation_end_date: str
    outcomes_unseen_at_freeze: bool


@dataclass(frozen=True)
class ConfirmationScore:
    method: str
    mae_kwh: float


@dataclass(frozen=True)
class VenueConfirmationResult:
    venue_id: str
    confirmation_rows: int
    previous_day_mae_kwh: float
    lag_feature_model_mae_kwh: float
    candidate_beats_previous_day: bool


@dataclass(frozen=True)
class FrozenConfirmationResult:
    metadata: ConfirmationMetadata
    training_rows: int
    confirmation_rows: int
    training_end_date: str
    confirmation_start_date: str
    confirmation_end_date: str
    scores: tuple[ConfirmationScore, ...]
    improvement_over_previous_day_pct: float
    venues_beating_previous_day: int
    eligible_venues: int
    required_venue_wins: int
    passed_frozen_success_rule: bool
    venue_results: tuple[VenueConfirmationResult, ...]


def load_confirmation_metadata(path: Path) -> ConfirmationMetadata:
    """Load and strictly validate the required provenance sidecar."""
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    required = {
        "dataset_id",
        "dataset_title",
        "source_url",
        "license",
        "venue_inclusion_rule",
        "confirmation_start_date",
        "confirmation_end_date",
        "outcomes_unseen_at_freeze",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"Metadata must contain exactly: {sorted(required)}")
    for field in required - {"outcomes_unseen_at_freeze"}:
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f"Metadata field must be a non-empty string: {field}")
    if not isinstance(value["outcomes_unseen_at_freeze"], bool):
        raise ValueError("outcomes_unseen_at_freeze must be true or false")
    return ConfirmationMetadata(**value)


def validate_new_confirmation_period(
    metadata: ConfirmationMetadata, start_date: str, end_date: str
) -> None:
    """Fail closed when provenance or the declared locked period is invalid."""
    if not metadata.outcomes_unseen_at_freeze:
        raise ValueError("Confirmation outcomes must have been unseen at specification freeze")
    if metadata.confirmation_start_date != start_date:
        raise ValueError("Declared confirmation_start_date does not match the data split")
    if metadata.confirmation_end_date != end_date:
        raise ValueError("Declared confirmation_end_date does not match the data split")
    if (
        metadata.dataset_id.casefold() == OBSERVED_BDG2_DATASET_ID
        and start_date <= OBSERVED_BDG2_END_DATE
    ):
        raise ValueError("The already-observed BDG2 confirmation period is ineligible")


def meets_frozen_success_rule(
    previous_day_mae_kwh: float,
    candidate_mae_kwh: float,
    venue_wins: int,
    eligible_venues: int,
) -> bool:
    if previous_day_mae_kwh < 0 or candidate_mae_kwh < 0:
        raise ValueError("MAE values cannot be negative")
    if eligible_venues < 1 or not 0 <= venue_wins <= eligible_venues:
        raise ValueError("Venue counts are invalid")
    required_wins = (eligible_venues + 1) // 2
    return (
        previous_day_mae_kwh > 0
        and candidate_mae_kwh <= previous_day_mae_kwh * 0.95
        and venue_wins >= required_wins
    )


def evaluate_frozen_confirmation(
    records: list[RealDailyRecord],
    metadata: ConfirmationMetadata,
    confirmation_days: int = MINIMUM_CONFIRMATION_DAYS,
) -> FrozenConfirmationResult:
    """Apply the frozen candidate, comparators and success rule without tuning."""
    if confirmation_days < MINIMUM_CONFIRMATION_DAYS:
        raise ValueError(
            f"At least {MINIMUM_CONFIRMATION_DAYS} confirmation dates are required"
        )
    training, confirmation = chronological_split(records, confirmation_days)
    confirmation_start = min(record.utc_date for record in confirmation)
    confirmation_end = max(record.utc_date for record in confirmation)
    validate_new_confirmation_period(metadata, confirmation_start, confirmation_end)

    actual = [record.electricity_kwh for record in confirmation]
    venue_means = {
        venue_id: sum(
            record.electricity_kwh
            for record in training
            if record.venue_id == venue_id
        )
        / sum(record.venue_id == venue_id for record in training)
        for venue_id in sorted({record.venue_id for record in training})
    }
    time_series = predict_time_series_baselines(training, confirmation)
    seasonal_model = fit_real_linear_model(training)
    lag_model = fit_lag_feature_model(training)
    lagged_confirmation = build_lagged_test_observations(confirmation, time_series)
    predictions = {
        "per_venue_mean": [venue_means[row.venue_id] for row in confirmation],
        "previous_day": list(time_series.previous_day_kwh),
        "seven_day_rolling_mean": list(time_series.seven_day_rolling_mean_kwh),
        "same_weekday_last_week": list(time_series.same_weekday_last_week_kwh),
        "seasonal_linear_model": [
            seasonal_model.predict(row) for row in confirmation
        ],
        "lag_feature_model": [
            lag_model.predict(row) for row in lagged_confirmation
        ],
    }
    scores = tuple(
        ConfirmationScore(method, mean_absolute_error(actual, estimates))
        for method, estimates in predictions.items()
    )
    score_by_method = {score.method: score.mae_kwh for score in scores}

    venue_results = []
    for venue_id in sorted({record.venue_id for record in confirmation}):
        indices = [
            index
            for index, record in enumerate(confirmation)
            if record.venue_id == venue_id
        ]
        previous_day_mae = mean_absolute_error(
            [actual[index] for index in indices],
            [predictions["previous_day"][index] for index in indices],
        )
        candidate_mae = mean_absolute_error(
            [actual[index] for index in indices],
            [predictions["lag_feature_model"][index] for index in indices],
        )
        venue_results.append(
            VenueConfirmationResult(
                venue_id=venue_id,
                confirmation_rows=len(indices),
                previous_day_mae_kwh=previous_day_mae,
                lag_feature_model_mae_kwh=candidate_mae,
                candidate_beats_previous_day=candidate_mae < previous_day_mae,
            )
        )

    venue_wins = sum(item.candidate_beats_previous_day for item in venue_results)
    eligible_venues = len(venue_results)
    previous_day_mae = score_by_method["previous_day"]
    candidate_mae = score_by_method["lag_feature_model"]
    improvement = (
        (previous_day_mae - candidate_mae) / previous_day_mae * 100
        if previous_day_mae > 0
        else 0.0
    )
    return FrozenConfirmationResult(
        metadata=metadata,
        training_rows=len(training),
        confirmation_rows=len(confirmation),
        training_end_date=max(record.utc_date for record in training),
        confirmation_start_date=confirmation_start,
        confirmation_end_date=confirmation_end,
        scores=scores,
        improvement_over_previous_day_pct=improvement,
        venues_beating_previous_day=venue_wins,
        eligible_venues=eligible_venues,
        required_venue_wins=(eligible_venues + 1) // 2,
        passed_frozen_success_rule=meets_frozen_success_rule(
            previous_day_mae, candidate_mae, venue_wins, eligible_venues
        ),
        venue_results=tuple(venue_results),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--confirmation-days", type=int, default=MINIMUM_CONFIRMATION_DAYS)
    args = parser.parse_args()
    result = evaluate_frozen_confirmation(
        load_real_daily_records(args.data),
        load_confirmation_metadata(args.metadata),
        args.confirmation_days,
    )
    print(f"Frozen confirmation: {result.metadata.dataset_title}")
    print(
        f"Train through {result.training_end_date}; confirm "
        f"{result.confirmation_start_date} to {result.confirmation_end_date}"
    )
    for score in result.scores:
        print(f"  {score.method}: {score.mae_kwh:,.2f} kWh/day")
    print(
        f"Candidate improvement over previous day: "
        f"{result.improvement_over_previous_day_pct:,.2f}%"
    )
    print(
        f"Venue wins: {result.venues_beating_previous_day}/{result.eligible_venues} "
        f"(required: {result.required_venue_wins})"
    )
    print(
        "Frozen success criterion met: "
        + ("yes" if result.passed_frozen_success_rule else "no")
    )


if __name__ == "__main__":
    main()
