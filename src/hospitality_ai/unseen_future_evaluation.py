"""Evaluate completely unseen venues on their newest future period."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .real_data_evaluation import mean_absolute_error
from .unseen_venue_evaluation import (
    LOCKED_VENUES,
    UnseenVenueRecord,
    fit_venue_independent_model,
    load_unseen_venue_records,
)


@dataclass(frozen=True)
class UnseenFutureResult:
    venue_id: str
    venue_type: str
    training_rows: int
    test_rows: int
    training_end_date: str
    test_start_date: str
    test_end_date: str
    baseline_mae_kwh: float
    model_mae_kwh: float
    improvement_pct: float
    model_beats_baseline: bool


@dataclass(frozen=True)
class UnseenFutureEvaluation:
    test_days: int
    results: tuple[UnseenFutureResult, ...]
    success_on_every_venue: bool


def split_unseen_future(
    records: list[UnseenVenueRecord], venue_id: str, test_days: int = 60
) -> tuple[list[UnseenVenueRecord], list[UnseenVenueRecord]]:
    """Remove the venue from training and remove future dates from training."""
    if test_days < 1:
        raise ValueError("test_days must be positive")
    venue_records = [record for record in records if record.venue_id == venue_id]
    if not venue_records:
        raise ValueError(f"Held-out venue not found: {venue_id}")
    venue_dates = sorted({record.utc_date for record in venue_records})
    if len(venue_dates) <= test_days:
        raise ValueError("More held-out venue dates than test_days are required")
    test_dates = set(venue_dates[-test_days:])
    test_start_date = min(test_dates)
    training = [
        record
        for record in records
        if record.venue_id != venue_id and record.utc_date < test_start_date
    ]
    test = [
        record
        for record in venue_records
        if record.utc_date in test_dates
    ]
    if not training or not test:
        raise ValueError("Non-empty training and test records are required")
    if any(record.venue_id == venue_id for record in training):
        raise AssertionError("Held-out venue leaked into training")
    if max(record.utc_date for record in training) >= min(
        record.utc_date for record in test
    ):
        raise AssertionError("Future dates leaked into training")
    return training, test


def evaluate_unseen_future(
    records: list[UnseenVenueRecord],
    venue_ids: tuple[str, ...] = LOCKED_VENUES,
    test_days: int = 60,
) -> UnseenFutureEvaluation:
    """Evaluate the fixed two-venue success criterion without building or time leakage."""
    if len(set(venue_ids)) != len(venue_ids):
        raise ValueError("Each held-out venue must be unique")
    results = []
    for venue_id in venue_ids:
        training, test = split_unseen_future(records, venue_id, test_days)
        venue_type = test[0].venue_type
        same_type_training = [
            record for record in training if record.venue_type == venue_type
        ]
        if not same_type_training:
            raise ValueError(f"No {venue_type} training records for {venue_id}")
        baseline_value = sum(
            record.electricity_kwh for record in same_type_training
        ) / len(same_type_training)
        model = fit_venue_independent_model(training)
        actual = [record.electricity_kwh for record in test]
        baseline_mae = mean_absolute_error(actual, [baseline_value] * len(test))
        model_mae = mean_absolute_error(
            actual, [model.predict(record) for record in test]
        )
        improvement = (baseline_mae - model_mae) / baseline_mae * 100
        results.append(
            UnseenFutureResult(
                venue_id=venue_id,
                venue_type=venue_type,
                training_rows=len(training),
                test_rows=len(test),
                training_end_date=max(record.utc_date for record in training),
                test_start_date=min(record.utc_date for record in test),
                test_end_date=max(record.utc_date for record in test),
                baseline_mae_kwh=baseline_mae,
                model_mae_kwh=model_mae,
                improvement_pct=improvement,
                model_beats_baseline=model_mae < baseline_mae,
            )
        )
    return UnseenFutureEvaluation(
        test_days=test_days,
        results=tuple(results),
        success_on_every_venue=all(result.model_beats_baseline for result in results),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/bdg2_hospitality_daily.csv"),
    )
    parser.add_argument("--test-days", type=int, default=60)
    args = parser.parse_args()
    evaluation = evaluate_unseen_future(
        load_unseen_venue_records(args.data), test_days=args.test_days
    )
    print("BDG2 unseen-venue plus future-period evaluation")
    print("Locked venues: " + ", ".join(LOCKED_VENUES))
    for result in evaluation.results:
        verdict = "model improved" if result.model_beats_baseline else "model did not improve"
        print(
            f"{result.venue_id} ({result.venue_type}): "
            f"train={result.training_rows:,} through {result.training_end_date}; "
            f"test={result.test_rows:,} from {result.test_start_date} to {result.test_end_date}; "
            f"baseline MAE={result.baseline_mae_kwh:,.2f}; "
            f"model MAE={result.model_mae_kwh:,.2f}; "
            f"improvement={result.improvement_pct:,.1f}% ({verdict})"
        )
    print(
        "Predefined success criterion met: "
        + ("yes" if evaluation.success_on_every_venue else "no")
    )


if __name__ == "__main__":
    main()
