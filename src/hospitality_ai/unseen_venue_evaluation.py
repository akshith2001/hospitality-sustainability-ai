"""Evaluate a venue-independent model on two completely unseen BDG2 venues."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from math import cos, pi, sin
from pathlib import Path

from .linear_model import _solve_linear_system
from .real_data_evaluation import mean_absolute_error


LOCKED_VENUES = ("Fox_food_Francesco", "Mouse_lodging_Vicente")


@dataclass(frozen=True)
class UnseenVenueRecord:
    venue_id: str
    utc_date: str
    venue_type: str
    floor_area_sqm: float
    outside_temperature_c: float
    electricity_kwh: float


@dataclass(frozen=True)
class UnseenVenueResult:
    venue_id: str
    venue_type: str
    training_rows: int
    test_rows: int
    baseline_mae_kwh: float
    model_mae_kwh: float
    improvement_pct: float
    model_beats_baseline: bool


@dataclass(frozen=True)
class UnseenVenueEvaluation:
    results: tuple[UnseenVenueResult, ...]
    success_on_every_venue: bool


@dataclass(frozen=True)
class VenueIndependentModel:
    coefficients: tuple[float, ...]

    def predict(self, record: UnseenVenueRecord) -> float:
        return sum(
            coefficient * feature
            for coefficient, feature in zip(self.coefficients, encode_features(record))
        )


def load_unseen_venue_records(
    path: Path, minimum_daily_kwh: float = 1.0
) -> list[UnseenVenueRecord]:
    """Load valid daily records using the already documented near-zero rule."""
    records = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if not row["outside_temperature_c"]:
                continue
            electricity_kwh = float(row["electricity_kwh"])
            if electricity_kwh < minimum_daily_kwh:
                continue
            records.append(
                UnseenVenueRecord(
                    venue_id=row["venue_id"],
                    utc_date=row["utc_date"],
                    venue_type=row["venue_type"],
                    floor_area_sqm=float(row["floor_area_sqm"]),
                    outside_temperature_c=float(row["outside_temperature_c"]),
                    electricity_kwh=electricity_kwh,
                )
            )
    return records


def encode_features(record: UnseenVenueRecord) -> tuple[float, ...]:
    """Encode only features available for a venue never observed during training."""
    record_date = date.fromisoformat(record.utc_date)
    temperature_distance = record.outside_temperature_c - 18.0
    annual_angle = 2.0 * pi * (record_date.timetuple().tm_yday - 1) / 365.25
    return (
        1.0,
        float(record.venue_type == "hotel"),
        record.floor_area_sqm,
        temperature_distance,
        temperature_distance**2,
        sin(annual_angle),
        cos(annual_angle),
        *(float(record_date.weekday() == value) for value in range(1, 7)),
    )


def fit_venue_independent_model(
    records: list[UnseenVenueRecord],
) -> VenueIndependentModel:
    if not records:
        raise ValueError("Training records are required")
    rows = [encode_features(record) for record in records]
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
    return VenueIndependentModel(tuple(_solve_linear_system(xtx, xty)))


def evaluate_unseen_venues(
    records: list[UnseenVenueRecord],
    venue_ids: tuple[str, ...] = LOCKED_VENUES,
) -> UnseenVenueEvaluation:
    """Hold out each locked venue completely and report both results separately."""
    if len(set(venue_ids)) != len(venue_ids):
        raise ValueError("Each held-out venue must be unique")
    available = {record.venue_id for record in records}
    missing = set(venue_ids) - available
    if missing:
        raise ValueError(f"Held-out venues not found: {sorted(missing)}")

    results = []
    for venue_id in venue_ids:
        test = [record for record in records if record.venue_id == venue_id]
        training = [record for record in records if record.venue_id != venue_id]
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
        baseline_predictions = [baseline_value] * len(test)
        model_predictions = [model.predict(record) for record in test]
        baseline_mae = mean_absolute_error(actual, baseline_predictions)
        model_mae = mean_absolute_error(actual, model_predictions)
        improvement = (baseline_mae - model_mae) / baseline_mae * 100
        results.append(
            UnseenVenueResult(
                venue_id=venue_id,
                venue_type=venue_type,
                training_rows=len(training),
                test_rows=len(test),
                baseline_mae_kwh=baseline_mae,
                model_mae_kwh=model_mae,
                improvement_pct=improvement,
                model_beats_baseline=model_mae < baseline_mae,
            )
        )
    return UnseenVenueEvaluation(
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
    args = parser.parse_args()
    evaluation = evaluate_unseen_venues(load_unseen_venue_records(args.data))
    print("BDG2 completely unseen-venue evaluation")
    print("Locked venues: " + ", ".join(LOCKED_VENUES))
    for result in evaluation.results:
        verdict = "model improved" if result.model_beats_baseline else "model did not improve"
        print(
            f"{result.venue_id} ({result.venue_type}): "
            f"train={result.training_rows:,}, test={result.test_rows:,}, "
            f"baseline MAE={result.baseline_mae_kwh:,.2f}, "
            f"model MAE={result.model_mae_kwh:,.2f}, "
            f"improvement={result.improvement_pct:,.1f}% ({verdict})"
        )
    print(
        "Predefined success criterion met: "
        + ("yes" if evaluation.success_on_every_venue else "no")
    )


if __name__ == "__main__":
    main()
