"""Residual-based anomaly alerts with transparent evaluation metrics."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from statistics import median

from .baseline import train_test_split
from .linear_model import LinearModel, fit_linear_model
from .synthetic_data import DailyVenueRecord, generate_records


MAD_NORMAL_SCALE = 1.4826


@dataclass(frozen=True)
class AnomalyDetector:
    model: LinearModel
    residual_median_kwh: float
    residual_scale_kwh: float
    threshold_kwh: float

    def residual(self, record: DailyVenueRecord) -> float:
        return record.electricity_kwh - self.model.predict(record)

    def is_alert(self, record: DailyVenueRecord) -> bool:
        return self.residual(record) > self.threshold_kwh


@dataclass(frozen=True)
class AnomalyEvaluation:
    test_rows: int
    actual_anomalies: int
    alerts: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


def fit_anomaly_detector(
    training_records: list[DailyVenueRecord], threshold_multiplier: float = 3.0
) -> AnomalyDetector:
    """Fit a regression model and a median/MAD positive-residual threshold."""
    if threshold_multiplier <= 0:
        raise ValueError("threshold_multiplier must be positive")
    model = fit_linear_model(training_records)
    residuals = [record.electricity_kwh - model.predict(record) for record in training_records]
    centre = median(residuals)
    mad = median(abs(value - centre) for value in residuals)
    robust_scale = max(MAD_NORMAL_SCALE * mad, 1e-9)
    return AnomalyDetector(
        model=model,
        residual_median_kwh=centre,
        residual_scale_kwh=robust_scale,
        threshold_kwh=centre + threshold_multiplier * robust_scale,
    )


def evaluate_anomaly_detector(
    records: list[DailyVenueRecord],
    test_fraction: float = 0.20,
    seed: int = 2026,
    threshold_multiplier: float = 3.0,
) -> tuple[AnomalyDetector, AnomalyEvaluation]:
    training, test = train_test_split(records, test_fraction, seed)
    detector = fit_anomaly_detector(training, threshold_multiplier)
    predictions = [detector.is_alert(record) for record in test]
    labels = [bool(record.is_injected_anomaly) for record in test]
    true_positives = sum(predicted and actual for predicted, actual in zip(predictions, labels))
    false_positives = sum(predicted and not actual for predicted, actual in zip(predictions, labels))
    false_negatives = sum(not predicted and actual for predicted, actual in zip(predictions, labels))
    alerts = sum(predictions)
    precision = true_positives / alerts if alerts else 0.0
    actual_anomalies = sum(labels)
    recall = true_positives / actual_anomalies if actual_anomalies else 0.0
    return detector, AnomalyEvaluation(
        test_rows=len(test),
        actual_anomalies=actual_anomalies,
        alerts=alerts,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate residual anomaly alerts")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--threshold-multiplier", type=float, default=3.0)
    args = parser.parse_args()
    detector, result = evaluate_anomaly_detector(
        generate_records(args.rows, args.seed),
        seed=args.seed,
        threshold_multiplier=args.threshold_multiplier,
    )
    print("Residual-based anomaly detection")
    print(f"Alert threshold: {detector.threshold_kwh:,.2f} kWh above prediction")
    print(f"Test rows: {result.test_rows}; injected anomalies: {result.actual_anomalies}")
    print(f"Alerts: {result.alerts}; true positives: {result.true_positives}")
    print(f"False positives: {result.false_positives}; false negatives: {result.false_negatives}")
    print(f"Precision: {result.precision:.1%}; recall: {result.recall:.1%}")


if __name__ == "__main__":
    main()

