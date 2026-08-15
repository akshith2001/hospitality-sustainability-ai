"""Dependency-free multivariable linear regression for the learning project."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from .baseline import evaluate_mean_baseline, mean_absolute_error, train_test_split
from .synthetic_data import DailyVenueRecord, generate_records


FEATURE_NAMES = (
    "intercept",
    "customers",
    "opening_hours",
    "floor_area_m2",
    "kitchen_equipment_count",
    "temperature_distance_squared",
    "venue_is_hotel",
    "venue_is_bar",
    "venue_is_event_venue",
)


@dataclass(frozen=True)
class LinearModel:
    coefficients: tuple[float, ...]

    def predict(self, record: DailyVenueRecord) -> float:
        return sum(
            coefficient * value
            for coefficient, value in zip(self.coefficients, encode_features(record))
        )


@dataclass(frozen=True)
class LinearEvaluation:
    training_rows: int
    test_rows: int
    baseline_mae_kwh: float
    model_mae_kwh: float
    mae_improvement_pct: float


def encode_features(record: DailyVenueRecord) -> tuple[float, ...]:
    """Convert one record to numerical model inputs without using the target."""
    return (
        1.0,
        float(record.customers),
        record.opening_hours,
        record.floor_area_m2,
        float(record.kitchen_equipment_count),
        (record.outside_temperature_c - 18.0) ** 2,
        float(record.venue_type == "hotel"),
        float(record.venue_type == "bar"),
        float(record.venue_type == "event_venue"),
    )


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve Ax=b using Gaussian elimination with partial pivoting."""
    size = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Feature matrix is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                current - factor * pivot_current
                for current, pivot_current in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(size)]


def fit_linear_model(records: list[DailyVenueRecord]) -> LinearModel:
    """Fit ordinary least squares using training records only."""
    if len(records) < len(FEATURE_NAMES):
        raise ValueError("More training rows than coefficients are required")
    rows = [encode_features(record) for record in records]
    targets = [record.electricity_kwh for record in records]
    feature_count = len(FEATURE_NAMES)
    xtx = [[0.0] * feature_count for _ in range(feature_count)]
    xty = [0.0] * feature_count
    for row, target in zip(rows, targets):
        for left in range(feature_count):
            xty[left] += row[left] * target
            for right in range(feature_count):
                xtx[left][right] += row[left] * row[right]
    # A tiny ridge term protects against numerical singularity without materially
    # changing the learned coefficients. The intercept is not regularised.
    for index in range(1, feature_count):
        xtx[index][index] += 1e-8
    return LinearModel(tuple(_solve_linear_system(xtx, xty)))


def evaluate_linear_model(
    records: list[DailyVenueRecord],
    test_fraction: float = 0.20,
    seed: int = 2026,
) -> tuple[LinearModel, LinearEvaluation]:
    training, test = train_test_split(records, test_fraction, seed)
    model = fit_linear_model(training)
    predictions = [model.predict(record) for record in test]
    actual = [record.electricity_kwh for record in test]
    model_mae = mean_absolute_error(actual, predictions)
    baseline = evaluate_mean_baseline(records, test_fraction, seed)
    improvement = (baseline.mean_absolute_error_kwh - model_mae) / baseline.mean_absolute_error_kwh * 100
    return model, LinearEvaluation(
        training_rows=len(training),
        test_rows=len(test),
        baseline_mae_kwh=baseline.mean_absolute_error_kwh,
        model_mae_kwh=model_mae,
        mae_improvement_pct=improvement,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate linear regression")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    records = generate_records(args.rows, args.seed)
    model, result = evaluate_linear_model(records, seed=args.seed)
    print("Multivariable linear regression")
    print(f"Training rows: {result.training_rows:,}; test rows: {result.test_rows:,}")
    print(f"Baseline MAE: {result.baseline_mae_kwh:,.2f} kWh")
    print(f"Model MAE: {result.model_mae_kwh:,.2f} kWh")
    print(f"MAE improvement: {result.mae_improvement_pct:,.1f}%")
    print("Learned coefficients:")
    for name, coefficient in zip(FEATURE_NAMES, model.coefficients):
        print(f"  {name}: {coefficient:,.4f}")


if __name__ == "__main__":
    main()

