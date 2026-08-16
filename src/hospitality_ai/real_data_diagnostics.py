"""Diagnose venue-level failures in the chronological BDG2 evaluation."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .real_data_evaluation import (
    RealDailyRecord,
    chronological_split,
    fit_real_linear_model,
    load_real_daily_records,
    mean_absolute_error,
)


@dataclass(frozen=True)
class VenueDiagnostic:
    venue_id: str
    training_rows: int
    test_rows: int
    training_mean_kwh: float
    test_mean_kwh: float
    consumption_shift_pct: float
    training_mean_temperature_c: float
    test_mean_temperature_c: float
    baseline_mae_kwh: float
    model_mae_kwh: float
    model_mean_error_kwh: float
    finding: str


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def diagnose_venues(
    records: list[RealDailyRecord], test_days: int = 60
) -> tuple[VenueDiagnostic, ...]:
    training, test = chronological_split(records, test_days)
    model = fit_real_linear_model(training)
    diagnostics = []
    for venue_id in sorted({record.venue_id for record in test}):
        venue_training = [record for record in training if record.venue_id == venue_id]
        venue_test = [record for record in test if record.venue_id == venue_id]
        training_mean = _mean([record.electricity_kwh for record in venue_training])
        test_mean = _mean([record.electricity_kwh for record in venue_test])
        actual = [record.electricity_kwh for record in venue_test]
        baseline_predictions = [training_mean] * len(venue_test)
        model_predictions = [model.predict(record) for record in venue_test]
        baseline_mae = mean_absolute_error(actual, baseline_predictions)
        model_mae = mean_absolute_error(actual, model_predictions)
        mean_error = _mean(
            [prediction - observed for prediction, observed in zip(model_predictions, actual)]
        )
        consumption_shift = (test_mean - training_mean) / training_mean * 100
        if model_mae <= baseline_mae:
            finding = "model_improved"
        elif abs(mean_error) >= 0.5 * model_mae:
            finding = "systematic_overprediction" if mean_error > 0 else "systematic_underprediction"
        else:
            finding = "unexplained_daily_variability"
        diagnostics.append(
            VenueDiagnostic(
                venue_id=venue_id,
                training_rows=len(venue_training),
                test_rows=len(venue_test),
                training_mean_kwh=training_mean,
                test_mean_kwh=test_mean,
                consumption_shift_pct=consumption_shift,
                training_mean_temperature_c=_mean(
                    [record.outside_temperature_c for record in venue_training]
                ),
                test_mean_temperature_c=_mean(
                    [record.outside_temperature_c for record in venue_test]
                ),
                baseline_mae_kwh=baseline_mae,
                model_mae_kwh=model_mae,
                model_mean_error_kwh=mean_error,
                finding=finding,
            )
        )
    return tuple(diagnostics)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", type=Path, default=Path("data/processed/bdg2_hospitality_daily.csv")
    )
    parser.add_argument("--test-days", type=int, default=60)
    args = parser.parse_args()
    print("BDG2 venue diagnostics")
    for result in diagnose_venues(load_real_daily_records(args.data), args.test_days):
        print(
            f"{result.venue_id}: {result.finding}; "
            f"mean shift={result.consumption_shift_pct:+.1f}%; "
            f"temperature={result.training_mean_temperature_c:.1f}C->"
            f"{result.test_mean_temperature_c:.1f}C; "
            f"baseline MAE={result.baseline_mae_kwh:.2f}; "
            f"model MAE={result.model_mae_kwh:.2f}; "
            f"model bias={result.model_mean_error_kwh:+.2f} kWh/day"
        )


if __name__ == "__main__":
    main()
