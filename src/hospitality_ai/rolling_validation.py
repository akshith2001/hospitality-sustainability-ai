"""Train-only rolling cross-validation for the real-data candidate models."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .lag_feature_model import (
    build_lagged_test_observations,
    fit_lag_feature_model,
)
from .real_data_evaluation import (
    RealDailyRecord,
    fit_real_linear_model,
    load_real_daily_records,
    mean_absolute_error,
)
from .time_series_baselines import predict_time_series_baselines


METHOD_NAMES = (
    "per_venue_mean",
    "previous_day",
    "seven_day_rolling_mean",
    "same_weekday_last_week",
    "seasonal_linear_model",
    "lag_feature_model",
)


@dataclass(frozen=True)
class MethodScore:
    method: str
    mae_kwh: float


@dataclass(frozen=True)
class RollingFoldResult:
    fold: int
    training_rows: int
    validation_rows: int
    training_end_date: str
    validation_start_date: str
    validation_end_date: str
    scores: tuple[MethodScore, ...]


@dataclass(frozen=True)
class VenueRollingResult:
    venue_id: str
    validation_rows: int
    scores: tuple[MethodScore, ...]


@dataclass(frozen=True)
class RollingValidationResult:
    reserved_test_start_date: str
    fold_days: int
    folds: tuple[RollingFoldResult, ...]
    overall_scores: tuple[MethodScore, ...]
    venue_results: tuple[VenueRollingResult, ...]


def rolling_date_splits(
    records: list[RealDailyRecord],
    reserved_test_days: int = 60,
    fold_days: int = 30,
    fold_count: int = 4,
) -> tuple[str, tuple[tuple[list[RealDailyRecord], list[RealDailyRecord]], ...]]:
    """Reserve the final test period, then create expanding chronological folds."""
    if reserved_test_days < 1 or fold_days < 1 or fold_count < 1:
        raise ValueError("Reserved days, fold days and fold count must be positive")
    dates = sorted({record.utc_date for record in records})
    required_dates = reserved_test_days + fold_days * fold_count + 1
    if len(dates) < required_dates:
        raise ValueError(f"At least {required_dates} unique dates are required")

    reserved_test_start = dates[-reserved_test_days]
    development_dates = dates[:-reserved_test_days]
    first_validation_index = len(development_dates) - fold_days * fold_count
    folds = []
    for fold in range(fold_count):
        validation_start = first_validation_index + fold * fold_days
        validation_dates = set(
            development_dates[validation_start : validation_start + fold_days]
        )
        training_dates = set(development_dates[:validation_start])
        training = [record for record in records if record.utc_date in training_dates]
        validation = [record for record in records if record.utc_date in validation_dates]
        if not training or not validation:
            raise ValueError("Every fold requires non-empty training and validation rows")
        missing = {record.venue_id for record in validation} - {
            record.venue_id for record in training
        }
        if missing:
            raise ValueError(f"Validation venues missing from training: {sorted(missing)}")
        folds.append((training, validation))
    return reserved_test_start, tuple(folds)


def _fold_predictions(
    training: list[RealDailyRecord], validation: list[RealDailyRecord]
) -> dict[str, list[float]]:
    venue_means = {
        venue_id: sum(
            record.electricity_kwh
            for record in training
            if record.venue_id == venue_id
        )
        / sum(record.venue_id == venue_id for record in training)
        for venue_id in sorted({record.venue_id for record in training})
    }
    time_series = predict_time_series_baselines(training, validation)
    seasonal_model = fit_real_linear_model(training)
    lag_model = fit_lag_feature_model(training)
    lagged_validation = build_lagged_test_observations(validation, time_series)
    return {
        "per_venue_mean": [venue_means[record.venue_id] for record in validation],
        "previous_day": list(time_series.previous_day_kwh),
        "seven_day_rolling_mean": list(time_series.seven_day_rolling_mean_kwh),
        "same_weekday_last_week": list(time_series.same_weekday_last_week_kwh),
        "seasonal_linear_model": [
            seasonal_model.predict(record) for record in validation
        ],
        "lag_feature_model": [
            lag_model.predict(observation) for observation in lagged_validation
        ],
    }


def evaluate_rolling_validation(
    records: list[RealDailyRecord],
    reserved_test_days: int = 60,
    fold_days: int = 30,
    fold_count: int = 4,
) -> RollingValidationResult:
    """Compare fixed candidates without using the reserved final test period."""
    reserved_start, splits = rolling_date_splits(
        records, reserved_test_days, fold_days, fold_count
    )
    all_actual: list[float] = []
    all_predictions = {method: [] for method in METHOD_NAMES}
    venue_actual: dict[str, list[float]] = {}
    venue_predictions: dict[str, dict[str, list[float]]] = {}
    fold_results = []

    for fold_number, (training, validation) in enumerate(splits, start=1):
        actual = [record.electricity_kwh for record in validation]
        predictions = _fold_predictions(training, validation)
        all_actual.extend(actual)
        fold_results.append(
            RollingFoldResult(
                fold=fold_number,
                training_rows=len(training),
                validation_rows=len(validation),
                training_end_date=max(record.utc_date for record in training),
                validation_start_date=min(record.utc_date for record in validation),
                validation_end_date=max(record.utc_date for record in validation),
                scores=tuple(
                    MethodScore(method, mean_absolute_error(actual, predictions[method]))
                    for method in METHOD_NAMES
                ),
            )
        )
        for method in METHOD_NAMES:
            all_predictions[method].extend(predictions[method])
        for index, record in enumerate(validation):
            venue_actual.setdefault(record.venue_id, []).append(actual[index])
            method_values = venue_predictions.setdefault(
                record.venue_id, {method: [] for method in METHOD_NAMES}
            )
            for method in METHOD_NAMES:
                method_values[method].append(predictions[method][index])

    return RollingValidationResult(
        reserved_test_start_date=reserved_start,
        fold_days=fold_days,
        folds=tuple(fold_results),
        overall_scores=tuple(
            MethodScore(method, mean_absolute_error(all_actual, all_predictions[method]))
            for method in METHOD_NAMES
        ),
        venue_results=tuple(
            VenueRollingResult(
                venue_id=venue_id,
                validation_rows=len(venue_actual[venue_id]),
                scores=tuple(
                    MethodScore(
                        method,
                        mean_absolute_error(
                            venue_actual[venue_id], venue_predictions[venue_id][method]
                        ),
                    )
                    for method in METHOD_NAMES
                ),
            )
            for venue_id in sorted(venue_actual)
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/bdg2_hospitality_daily.csv"),
    )
    parser.add_argument("--reserved-test-days", type=int, default=60)
    parser.add_argument("--fold-days", type=int, default=30)
    parser.add_argument("--fold-count", type=int, default=4)
    args = parser.parse_args()
    result = evaluate_rolling_validation(
        load_real_daily_records(args.data),
        reserved_test_days=args.reserved_test_days,
        fold_days=args.fold_days,
        fold_count=args.fold_count,
    )
    print("BDG2 train-only rolling validation")
    print(f"Reserved final test period starts: {result.reserved_test_start_date}")
    for fold in result.folds:
        print(
            f"Fold {fold.fold}: train through {fold.training_end_date}; "
            f"validate {fold.validation_start_date} to {fold.validation_end_date}"
        )
    print("Overall validation MAE:")
    for score in result.overall_scores:
        print(f"  {score.method}: {score.mae_kwh:,.2f} kWh/day")
    print("Per-venue validation rows and best candidate:")
    for venue in result.venue_results:
        best = min(venue.scores, key=lambda score: score.mae_kwh)
        print(
            f"  {venue.venue_id}: n={venue.validation_rows}, "
            f"{best.method}={best.mae_kwh:,.2f} kWh/day"
        )


if __name__ == "__main__":
    main()
