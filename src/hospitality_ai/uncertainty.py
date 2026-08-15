"""Transparent prediction ranges and simple out-of-distribution warnings."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from statistics import median

from .anomaly import MAD_NORMAL_SCALE
from .baseline import train_test_split
from .linear_model import LinearModel, fit_linear_model
from .synthetic_data import DailyVenueRecord, generate_records


NUMERIC_FIELDS = (
    "customers",
    "opening_hours",
    "outside_temperature_c",
    "floor_area_m2",
    "kitchen_equipment_count",
)


@dataclass(frozen=True)
class PredictionRange:
    predicted_kwh: float
    lower_kwh: float
    upper_kwh: float
    confidence: str
    warning: str


@dataclass(frozen=True)
class UncertaintyModel:
    model: LinearModel
    residual_centre_kwh: float
    residual_scale_kwh: float
    training_rows: int
    numeric_ranges: dict[str, tuple[float, float]]
    known_venue_types: frozenset[str]

    def predict_range(
        self, record: DailyVenueRecord, multiplier: float = 1.96
    ) -> PredictionRange:
        if multiplier <= 0:
            raise ValueError("multiplier must be positive")
        prediction = self.model.predict(record) + self.residual_centre_kwh
        margin = multiplier * self.residual_scale_kwh
        reasons = []
        if self.training_rows < 100:
            reasons.append("fewer than 100 training observations")
        if record.venue_type not in self.known_venue_types:
            reasons.append("unseen venue type")
        for field, (minimum, maximum) in self.numeric_ranges.items():
            value = float(getattr(record, field))
            if not minimum <= value <= maximum:
                reasons.append(f"{field} is outside the training range")
        if reasons:
            confidence = "low"
            warning = "Low confidence: " + "; ".join(reasons) + ". Collect more relevant data."
        else:
            confidence = "standard"
            warning = (
                "Model-based estimate only; validate against real measurements before action."
            )
        return PredictionRange(
            predicted_kwh=prediction,
            lower_kwh=max(0.0, prediction - margin),
            upper_kwh=prediction + margin,
            confidence=confidence,
            warning=warning,
        )


def fit_uncertainty_model(records: list[DailyVenueRecord]) -> UncertaintyModel:
    """Fit the model and estimate a robust empirical residual spread."""
    if not records:
        raise ValueError("At least one training record is required")
    model = fit_linear_model(records)
    residuals = [record.electricity_kwh - model.predict(record) for record in records]
    centre = median(residuals)
    mad = median(abs(value - centre) for value in residuals)
    scale = max(MAD_NORMAL_SCALE * mad, 1e-9)
    ranges = {
        field: (
            min(float(getattr(record, field)) for record in records),
            max(float(getattr(record, field)) for record in records),
        )
        for field in NUMERIC_FIELDS
    }
    return UncertaintyModel(
        model=model,
        residual_centre_kwh=centre,
        residual_scale_kwh=scale,
        training_rows=len(records),
        numeric_ranges=ranges,
        known_venue_types=frozenset(record.venue_type for record in records),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Show a prediction uncertainty range")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    training, test = train_test_split(generate_records(args.rows, args.seed), seed=args.seed)
    uncertainty_model = fit_uncertainty_model(training)
    record = test[0]
    result = uncertainty_model.predict_range(record)
    print("Electricity prediction with uncertainty")
    print(f"Date: {record.date}; venue: {record.venue_type}")
    print(f"Predicted: {result.predicted_kwh:,.2f} kWh")
    print(f"Expected range: {result.lower_kwh:,.2f}-{result.upper_kwh:,.2f} kWh")
    print(f"Actual: {record.electricity_kwh:,.2f} kWh")
    print(f"Confidence: {result.confidence}")
    print(result.warning)


if __name__ == "__main__":
    main()
