"""Transparent train/test split and mean-prediction baseline."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from statistics import fmean

from .synthetic_data import DailyVenueRecord, generate_records


@dataclass(frozen=True)
class BaselineResult:
    training_rows: int
    test_rows: int
    training_mean_kwh: float
    mean_absolute_error_kwh: float


def train_test_split(
    records: list[DailyVenueRecord],
    test_fraction: float = 0.20,
    seed: int = 2026,
) -> tuple[list[DailyVenueRecord], list[DailyVenueRecord]]:
    """Shuffle reproducibly and return separate training and test records."""
    if len(records) < 2:
        raise ValueError("At least two records are required")
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")

    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    test_count = max(1, round(len(shuffled) * test_fraction))
    test = shuffled[:test_count]
    training = shuffled[test_count:]
    if not training:
        raise ValueError("The selected split leaves no training records")
    return training, test


def mean_absolute_error(actual: list[float], predicted: list[float]) -> float:
    if not actual or len(actual) != len(predicted):
        raise ValueError("Actual and predicted values must have equal non-zero length")
    return fmean(abs(observed - estimate) for observed, estimate in zip(actual, predicted))


def evaluate_mean_baseline(
    records: list[DailyVenueRecord],
    test_fraction: float = 0.20,
    seed: int = 2026,
) -> BaselineResult:
    """Predict the training-set mean for every unseen test record."""
    training, test = train_test_split(records, test_fraction, seed)
    training_mean = fmean(record.electricity_kwh for record in training)
    actual = [record.electricity_kwh for record in test]
    predicted = [training_mean] * len(test)
    return BaselineResult(
        training_rows=len(training),
        test_rows=len(test),
        training_mean_kwh=training_mean,
        mean_absolute_error_kwh=mean_absolute_error(actual, predicted),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the mean electricity baseline")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    records = generate_records(args.rows, args.seed)
    result = evaluate_mean_baseline(records, seed=args.seed)
    print("Mean-prediction baseline")
    print(f"Training rows: {result.training_rows:,}")
    print(f"Test rows: {result.test_rows:,}")
    print(f"Training mean: {result.training_mean_kwh:,.2f} kWh")
    print(f"Test MAE: {result.mean_absolute_error_kwh:,.2f} kWh")


if __name__ == "__main__":
    main()

