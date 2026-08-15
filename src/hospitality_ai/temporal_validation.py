"""Chronological evaluation that trains on the past and tests on the future."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from .baseline import mean_absolute_error
from .linear_model import fit_linear_model
from .synthetic_data import DailyVenueRecord, generate_records


@dataclass(frozen=True)
class TemporalEvaluation:
    training_rows: int
    test_rows: int
    training_end_date: str
    test_start_date: str
    baseline_mae_kwh: float
    model_mae_kwh: float
    improvement_pct: float


def newest_days_split(
    records: list[DailyVenueRecord], test_days: int = 30
) -> tuple[list[DailyVenueRecord], list[DailyVenueRecord]]:
    """Use all earlier observations for training and the newest days for testing."""
    if test_days < 1:
        raise ValueError("test_days must be positive")
    ordered = sorted(records, key=lambda record: record.date)
    if len(ordered) <= test_days:
        raise ValueError("More records than test_days are required")
    return ordered[:-test_days], ordered[-test_days:]


def evaluate_newest_days(
    records: list[DailyVenueRecord], test_days: int = 30
) -> TemporalEvaluation:
    training, test = newest_days_split(records, test_days)
    model = fit_linear_model(training)
    actual = [record.electricity_kwh for record in test]
    model_predictions = [model.predict(record) for record in test]
    training_mean = sum(record.electricity_kwh for record in training) / len(training)
    baseline_predictions = [training_mean] * len(test)
    baseline_mae = mean_absolute_error(actual, baseline_predictions)
    model_mae = mean_absolute_error(actual, model_predictions)
    improvement = (baseline_mae - model_mae) / baseline_mae * 100
    return TemporalEvaluation(
        training_rows=len(training),
        test_rows=len(test),
        training_end_date=training[-1].date,
        test_start_date=test[0].date,
        baseline_mae_kwh=baseline_mae,
        model_mae_kwh=model_mae,
        improvement_pct=improvement,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate on the newest unseen days")
    parser.add_argument("--rows", type=int, default=365)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--test-days", type=int, default=30)
    args = parser.parse_args()
    result = evaluate_newest_days(
        generate_records(args.rows, args.seed), test_days=args.test_days
    )
    print("Chronological model evaluation")
    print(f"Training rows: {result.training_rows}; test rows: {result.test_rows}")
    print(f"Training ends: {result.training_end_date}")
    print(f"Unseen test period starts: {result.test_start_date}")
    print(f"Baseline MAE: {result.baseline_mae_kwh:,.2f} kWh")
    print(f"Model MAE: {result.model_mae_kwh:,.2f} kWh")
    print(f"Improvement: {result.improvement_pct:,.1f}%")


if __name__ == "__main__":
    main()
