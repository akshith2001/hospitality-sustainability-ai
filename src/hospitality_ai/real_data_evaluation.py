"""Chronological evaluation on the real BDG2 hospitality-related subset."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from math import cos, pi, sin
from pathlib import Path

from .linear_model import _solve_linear_system


@dataclass(frozen=True)
class RealDailyRecord:
    venue_id: str
    utc_date: str
    venue_type: str
    outside_temperature_c: float
    electricity_kwh: float


@dataclass(frozen=True)
class VenueEvaluation:
    venue_id: str
    test_rows: int
    baseline_mae_kwh: float
    model_mae_kwh: float


@dataclass(frozen=True)
class RealDataEvaluation:
    training_rows: int
    test_rows: int
    training_end_date: str
    test_start_date: str
    baseline_mae_kwh: float
    model_mae_kwh: float
    improvement_pct: float
    venue_results: tuple[VenueEvaluation, ...]
    missing_test_venues: tuple[str, ...] = ()


@dataclass(frozen=True)
class RealLinearModel:
    coefficients: tuple[float, ...]
    venue_ids: tuple[str, ...]

    def predict(self, record: RealDailyRecord) -> float:
        return sum(
            coefficient * feature
            for coefficient, feature in zip(self.coefficients, encode_features(record, self.venue_ids))
        )


def load_real_daily_records(
    path: Path, minimum_daily_kwh: float = 1.0
) -> list[RealDailyRecord]:
    """Load eligible days, excluding zero or near-zero meter states.

    The selected buildings are all larger than 1,500 square metres. Daily totals below
    1 kWh are treated as meter dropout, stuck readings or closure rather than normal
    operating observations. This rule is fixed before chronological splitting.
    """
    records = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if not row["outside_temperature_c"]:
                continue
            electricity_kwh = float(row["electricity_kwh"])
            if electricity_kwh < minimum_daily_kwh:
                continue
            records.append(
                RealDailyRecord(
                    venue_id=row["venue_id"],
                    utc_date=row["utc_date"],
                    venue_type=row["venue_type"],
                    outside_temperature_c=float(row["outside_temperature_c"]),
                    electricity_kwh=electricity_kwh,
                )
            )
    return records


def chronological_split(
    records: list[RealDailyRecord], test_days: int = 60
) -> tuple[list[RealDailyRecord], list[RealDailyRecord]]:
    if test_days < 1:
        raise ValueError("test_days must be positive")
    dates = sorted({record.utc_date for record in records})
    if len(dates) <= test_days:
        raise ValueError("More unique dates than test_days are required")
    test_dates = set(dates[-test_days:])
    training = [record for record in records if record.utc_date not in test_dates]
    test = [record for record in records if record.utc_date in test_dates]
    training_venues = {record.venue_id for record in training}
    missing = {record.venue_id for record in test} - training_venues
    if missing:
        raise ValueError(f"Test venues missing from training: {sorted(missing)}")
    return training, test


def encode_features(record: RealDailyRecord, venue_ids: tuple[str, ...]) -> tuple[float, ...]:
    record_date = date.fromisoformat(record.utc_date)
    weekday = record_date.weekday()
    temperature_distance = record.outside_temperature_c - 18.0
    annual_angle = 2.0 * pi * (record_date.timetuple().tm_yday - 1) / 365.25
    annual_sin = sin(annual_angle)
    annual_cos = cos(annual_angle)
    return (
        1.0,
        temperature_distance,
        temperature_distance**2,
        annual_sin,
        annual_cos,
        *(float(weekday == value) for value in range(1, 7)),
        *(float(record.venue_id == venue_id) for venue_id in venue_ids[1:]),
        *(
            value
            for venue_id in venue_ids[1:]
            for value in (
                float(record.venue_id == venue_id) * annual_sin,
                float(record.venue_id == venue_id) * annual_cos,
            )
        ),
    )


def fit_real_linear_model(records: list[RealDailyRecord]) -> RealLinearModel:
    venue_ids = tuple(sorted({record.venue_id for record in records}))
    rows = [encode_features(record, venue_ids) for record in records]
    feature_count = len(rows[0])
    if len(rows) <= feature_count:
        raise ValueError("More training rows than coefficients are required")
    xtx = [[0.0] * feature_count for _ in range(feature_count)]
    xty = [0.0] * feature_count
    for row, record in zip(rows, records):
        for left in range(feature_count):
            xty[left] += row[left] * record.electricity_kwh
            for right in range(feature_count):
                xtx[left][right] += row[left] * row[right]
    for index in range(1, feature_count):
        xtx[index][index] += 1e-6
    return RealLinearModel(tuple(_solve_linear_system(xtx, xty)), venue_ids)


def mean_absolute_error(actual: list[float], predicted: list[float]) -> float:
    if not actual or len(actual) != len(predicted):
        raise ValueError("Equal, non-empty actual and predicted values are required")
    return sum(abs(left - right) for left, right in zip(actual, predicted)) / len(actual)


def evaluate_real_data(
    records: list[RealDailyRecord], test_days: int = 60
) -> RealDataEvaluation:
    training, test = chronological_split(records, test_days)
    model = fit_real_linear_model(training)
    venue_means = {
        venue_id: sum(record.electricity_kwh for record in training if record.venue_id == venue_id)
        / sum(record.venue_id == venue_id for record in training)
        for venue_id in sorted({record.venue_id for record in training})
    }
    actual = [record.electricity_kwh for record in test]
    baseline_predictions = [venue_means[record.venue_id] for record in test]
    model_predictions = [model.predict(record) for record in test]
    baseline_mae = mean_absolute_error(actual, baseline_predictions)
    model_mae = mean_absolute_error(actual, model_predictions)
    improvement = (baseline_mae - model_mae) / baseline_mae * 100
    venue_results = []
    for venue_id in sorted({record.venue_id for record in test}):
        indices = [index for index, record in enumerate(test) if record.venue_id == venue_id]
        venue_results.append(
            VenueEvaluation(
                venue_id=venue_id,
                test_rows=len(indices),
                baseline_mae_kwh=mean_absolute_error(
                    [actual[index] for index in indices],
                    [baseline_predictions[index] for index in indices],
                ),
                model_mae_kwh=mean_absolute_error(
                    [actual[index] for index in indices],
                    [model_predictions[index] for index in indices],
                ),
            )
        )
    return RealDataEvaluation(
        training_rows=len(training),
        test_rows=len(test),
        training_end_date=max(record.utc_date for record in training),
        test_start_date=min(record.utc_date for record in test),
        baseline_mae_kwh=baseline_mae,
        model_mae_kwh=model_mae,
        improvement_pct=improvement,
        venue_results=tuple(venue_results),
        missing_test_venues=tuple(
            sorted(
                {record.venue_id for record in training}
                - {record.venue_id for record in test}
            )
        ),
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
    result = evaluate_real_data(load_real_daily_records(args.data), args.test_days)
    print("BDG2 chronological real-data evaluation")
    print(f"Training rows: {result.training_rows:,}; test rows: {result.test_rows:,}")
    print(f"Training ends: {result.training_end_date}")
    print(f"Unseen test period starts: {result.test_start_date}")
    print(f"Per-venue mean baseline MAE: {result.baseline_mae_kwh:,.2f} kWh/day")
    print(f"Linear model MAE: {result.model_mae_kwh:,.2f} kWh/day")
    print(f"MAE improvement: {result.improvement_pct:,.1f}%")
    print("Every held-out venue:")
    for venue in result.venue_results:
        print(
            f"  {venue.venue_id}: n={venue.test_rows}, "
            f"baseline={venue.baseline_mae_kwh:,.2f}, model={venue.model_mae_kwh:,.2f}"
        )
    if result.missing_test_venues:
        print("No eligible test-period readings:")
        for venue_id in result.missing_test_venues:
            print(f"  {venue_id}")


if __name__ == "__main__":
    main()
