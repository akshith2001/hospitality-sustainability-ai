"""Evaluate generalisation on a pseudonymous venue excluded from training."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from .baseline import mean_absolute_error
from .linear_model import fit_linear_model
from .synthetic_data import DailyVenueRecord, generate_records


@dataclass(frozen=True)
class VenueEvaluation:
    held_out_venue_id: str
    training_venues: int
    training_rows: int
    test_rows: int
    baseline_mae_kwh: float
    model_mae_kwh: float
    improvement_pct: float


@dataclass(frozen=True)
class AllVenuesEvaluation:
    results: tuple[VenueEvaluation, ...]
    mean_model_mae_kwh: float
    mean_improvement_pct: float
    best_venue_id: str
    worst_venue_id: str


def leave_one_venue_out_split(
    records: list[DailyVenueRecord], held_out_venue_id: str
) -> tuple[list[DailyVenueRecord], list[DailyVenueRecord]]:
    training = [record for record in records if record.venue_id != held_out_venue_id]
    test = [record for record in records if record.venue_id == held_out_venue_id]
    if not test:
        raise ValueError(f"No records found for {held_out_venue_id}")
    if not training:
        raise ValueError("At least one other venue is required for training")
    return training, test


def evaluate_held_out_venue(
    records: list[DailyVenueRecord], held_out_venue_id: str
) -> VenueEvaluation:
    training, test = leave_one_venue_out_split(records, held_out_venue_id)
    model = fit_linear_model(training)
    actual = [record.electricity_kwh for record in test]
    predictions = [model.predict(record) for record in test]
    training_mean = sum(record.electricity_kwh for record in training) / len(training)
    baseline_mae = mean_absolute_error(actual, [training_mean] * len(test))
    model_mae = mean_absolute_error(actual, predictions)
    improvement = (baseline_mae - model_mae) / baseline_mae * 100
    return VenueEvaluation(
        held_out_venue_id=held_out_venue_id,
        training_venues=len({record.venue_id for record in training}),
        training_rows=len(training),
        test_rows=len(test),
        baseline_mae_kwh=baseline_mae,
        model_mae_kwh=model_mae,
        improvement_pct=improvement,
    )


def evaluate_all_venues(records: list[DailyVenueRecord]) -> AllVenuesEvaluation:
    """Repeat held-out evaluation for every venue without selecting favourites."""
    venue_ids = sorted({record.venue_id for record in records})
    if len(venue_ids) < 2:
        raise ValueError("At least two venues are required")
    results = tuple(evaluate_held_out_venue(records, venue_id) for venue_id in venue_ids)
    best = min(results, key=lambda result: result.model_mae_kwh)
    worst = max(results, key=lambda result: result.model_mae_kwh)
    return AllVenuesEvaluation(
        results=results,
        mean_model_mae_kwh=sum(result.model_mae_kwh for result in results) / len(results),
        mean_improvement_pct=sum(result.improvement_pct for result in results) / len(results),
        best_venue_id=best.held_out_venue_id,
        worst_venue_id=worst.held_out_venue_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate on one unseen venue")
    parser.add_argument("--rows", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--venue-id", default="VENUE-001")
    parser.add_argument(
        "--all-venues", action="store_true", help="Evaluate every venue in turn"
    )
    args = parser.parse_args()
    records = generate_records(args.rows, args.seed)
    if args.all_venues:
        summary = evaluate_all_venues(records)
        print("Leave-one-venue-out evaluation for every venue")
        for result in summary.results:
            print(
                f"{result.held_out_venue_id}: model MAE {result.model_mae_kwh:,.2f} kWh; "
                f"baseline {result.baseline_mae_kwh:,.2f} kWh; "
                f"improvement {result.improvement_pct:,.1f}%"
            )
        print(f"Mean model MAE: {summary.mean_model_mae_kwh:,.2f} kWh")
        print(f"Mean improvement: {summary.mean_improvement_pct:,.1f}%")
        print(f"Best venue by MAE: {summary.best_venue_id}")
        print(f"Worst venue by MAE: {summary.worst_venue_id}")
        return
    result = evaluate_held_out_venue(records, args.venue_id)
    print("Leave-one-venue-out evaluation")
    print(f"Held-out venue: {result.held_out_venue_id}")
    print(f"Training venues: {result.training_venues}")
    print(f"Training rows: {result.training_rows}; test rows: {result.test_rows}")
    print(f"Baseline MAE: {result.baseline_mae_kwh:,.2f} kWh")
    print(f"Model MAE: {result.model_mae_kwh:,.2f} kWh")
    print(f"Improvement: {result.improvement_pct:,.1f}%")


if __name__ == "__main__":
    main()
