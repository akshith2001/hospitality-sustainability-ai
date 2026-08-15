"""Human-readable explanations for electricity predictions and alerts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from .anomaly import AnomalyDetector, fit_anomaly_detector
from .baseline import train_test_split
from .linear_model import FEATURE_NAMES, encode_features
from .synthetic_data import DailyVenueRecord, generate_records


@dataclass(frozen=True)
class FeatureContribution:
    feature: str
    input_value: float
    coefficient: float
    contribution_kwh: float


@dataclass(frozen=True)
class PredictionExplanation:
    predicted_kwh: float
    actual_kwh: float
    residual_kwh: float
    threshold_kwh: float
    is_alert: bool
    contributions: tuple[FeatureContribution, ...]
    guidance: str


def explain_record(
    detector: AnomalyDetector, record: DailyVenueRecord
) -> PredictionExplanation:
    values = encode_features(record)
    contributions = tuple(
        FeatureContribution(
            feature=name,
            input_value=value,
            coefficient=coefficient,
            contribution_kwh=value * coefficient,
        )
        for name, value, coefficient in zip(
            FEATURE_NAMES, values, detector.model.coefficients
        )
    )
    predicted = sum(item.contribution_kwh for item in contributions)
    residual = record.electricity_kwh - predicted
    alert = residual > detector.threshold_kwh
    guidance = (
        "Investigate operational changes, special events, equipment condition and data quality; "
        "this alert is not proof of waste."
        if alert
        else "Consumption is within the current model threshold; continue monitoring."
    )
    return PredictionExplanation(
        predicted_kwh=predicted,
        actual_kwh=record.electricity_kwh,
        residual_kwh=residual,
        threshold_kwh=detector.threshold_kwh,
        is_alert=alert,
        contributions=contributions,
        guidance=guidance,
    )


def most_positive_residual_record(
    detector: AnomalyDetector, records: list[DailyVenueRecord]
) -> DailyVenueRecord:
    if not records:
        raise ValueError("At least one record is required")
    return max(records, key=detector.residual)


def main() -> None:
    parser = argparse.ArgumentParser(description="Explain one high-residual test record")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    records = generate_records(args.rows, args.seed)
    training, test = train_test_split(records, seed=args.seed)
    detector = fit_anomaly_detector(training)
    record = most_positive_residual_record(detector, test)
    explanation = explain_record(detector, record)
    print("Explainable electricity alert")
    print(f"Venue: {record.venue_type}; customers: {record.customers}")
    print(f"Predicted: {explanation.predicted_kwh:,.2f} kWh")
    print(f"Actual: {explanation.actual_kwh:,.2f} kWh")
    print(f"Residual: {explanation.residual_kwh:+,.2f} kWh")
    print(f"Alert threshold: {explanation.threshold_kwh:,.2f} kWh")
    print(f"Alert: {explanation.is_alert}")
    print("Feature contributions:")
    for item in sorted(
        explanation.contributions,
        key=lambda contribution: abs(contribution.contribution_kwh),
        reverse=True,
    ):
        print(f"  {item.feature}: {item.contribution_kwh:+,.2f} kWh")
    print(explanation.guidance)


if __name__ == "__main__":
    main()

