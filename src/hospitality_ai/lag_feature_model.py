"""Linear real-data model with leakage-safe recent-history features."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import cos, pi, sin
from statistics import fmean
from typing import Protocol

from .linear_model import _solve_linear_system
from .time_series_baselines import TimeSeriesBaselinePredictions


class RealEnergyRecord(Protocol):
    venue_id: str
    utc_date: str
    outside_temperature_c: float
    electricity_kwh: float


@dataclass(frozen=True)
class LaggedObservation:
    venue_id: str
    utc_date: str
    outside_temperature_c: float
    electricity_kwh: float
    previous_day_kwh: float
    seven_day_rolling_mean_kwh: float
    same_weekday_last_week_kwh: float


@dataclass(frozen=True)
class LagFeatureModel:
    coefficients: tuple[float, ...]
    venue_ids: tuple[str, ...]

    def predict(self, observation: LaggedObservation) -> float:
        return sum(
            coefficient * feature
            for coefficient, feature in zip(
                self.coefficients, encode_lag_features(observation, self.venue_ids)
            )
        )


def build_lagged_training_observations(
    records: list[RealEnergyRecord],
) -> list[LaggedObservation]:
    """Build training rows using only values from strictly earlier dates.

    The first observation for each venue is omitted because no leakage-safe venue
    history exists. Missing calendar lags thereafter use that venue's expanding
    mean, calculated only from dates earlier than the row being encoded.
    """
    if not records:
        raise ValueError("Training records are required")
    ordered = sorted(records, key=lambda record: (record.utc_date, record.venue_id))
    history: dict[str, dict[date, float]] = {}
    observations = []
    position = 0
    while position < len(ordered):
        current_date = date.fromisoformat(ordered[position].utc_date)
        date_group = []
        while position < len(ordered):
            record = ordered[position]
            if date.fromisoformat(record.utc_date) != current_date:
                break
            date_group.append(record)
            position += 1
        if len({record.venue_id for record in date_group}) != len(date_group):
            raise ValueError("Each venue must have at most one record per date")

        # Encode the complete date before revealing any target from that date.
        for record in date_group:
            venue_history = history.setdefault(record.venue_id, {})
            if not venue_history:
                continue
            prior_mean = fmean(venue_history.values())
            earlier_values = [
                value
                for observed_date, value in sorted(venue_history.items(), reverse=True)
                if observed_date < current_date
            ][:7]
            observations.append(
                LaggedObservation(
                    venue_id=record.venue_id,
                    utc_date=record.utc_date,
                    outside_temperature_c=record.outside_temperature_c,
                    electricity_kwh=record.electricity_kwh,
                    previous_day_kwh=venue_history.get(
                        current_date - timedelta(days=1), prior_mean
                    ),
                    seven_day_rolling_mean_kwh=fmean(earlier_values),
                    same_weekday_last_week_kwh=venue_history.get(
                        current_date - timedelta(days=7), prior_mean
                    ),
                )
            )
        for record in date_group:
            history.setdefault(record.venue_id, {})[
                current_date
            ] = record.electricity_kwh
    return observations


def build_lagged_test_observations(
    records: list[RealEnergyRecord], predictions: TimeSeriesBaselinePredictions
) -> list[LaggedObservation]:
    """Combine already leakage-checked test lags with each test record."""
    lengths = {
        len(records),
        len(predictions.previous_day_kwh),
        len(predictions.seven_day_rolling_mean_kwh),
        len(predictions.same_weekday_last_week_kwh),
    }
    if len(lengths) != 1 or not records:
        raise ValueError("Records and lag predictions must have equal non-zero length")
    return [
        LaggedObservation(
            venue_id=record.venue_id,
            utc_date=record.utc_date,
            outside_temperature_c=record.outside_temperature_c,
            electricity_kwh=record.electricity_kwh,
            previous_day_kwh=predictions.previous_day_kwh[index],
            seven_day_rolling_mean_kwh=predictions.seven_day_rolling_mean_kwh[index],
            same_weekday_last_week_kwh=predictions.same_weekday_last_week_kwh[index],
        )
        for index, record in enumerate(records)
    ]


def encode_lag_features(
    observation: LaggedObservation, venue_ids: tuple[str, ...]
) -> tuple[float, ...]:
    observation_date = date.fromisoformat(observation.utc_date)
    weekday = observation_date.weekday()
    temperature_distance = observation.outside_temperature_c - 18.0
    annual_angle = 2.0 * pi * (observation_date.timetuple().tm_yday - 1) / 365.25
    return (
        1.0,
        temperature_distance,
        temperature_distance**2,
        sin(annual_angle),
        cos(annual_angle),
        *(float(weekday == value) for value in range(1, 7)),
        *(float(observation.venue_id == venue_id) for venue_id in venue_ids[1:]),
        observation.previous_day_kwh,
        observation.seven_day_rolling_mean_kwh,
        observation.same_weekday_last_week_kwh,
    )


def fit_lag_feature_model(records: list[RealEnergyRecord]) -> LagFeatureModel:
    observations = build_lagged_training_observations(records)
    venue_ids = tuple(sorted({record.venue_id for record in records}))
    rows = [encode_lag_features(observation, venue_ids) for observation in observations]
    if not rows or len(rows) <= len(rows[0]):
        raise ValueError("More lagged training rows than coefficients are required")
    feature_count = len(rows[0])
    xtx = [[0.0] * feature_count for _ in range(feature_count)]
    xty = [0.0] * feature_count
    for row, observation in zip(rows, observations):
        for left in range(feature_count):
            xty[left] += row[left] * observation.electricity_kwh
            for right in range(feature_count):
                xtx[left][right] += row[left] * row[right]
    for index in range(1, feature_count):
        xtx[index][index] += 1e-6
    return LagFeatureModel(tuple(_solve_linear_system(xtx, xty)), venue_ids)
