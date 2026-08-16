"""Leakage-safe time-series baselines for chronological daily evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import fmean
from typing import Protocol


class DailyEnergyRecord(Protocol):
    venue_id: str
    utc_date: str
    electricity_kwh: float


@dataclass(frozen=True)
class TimeSeriesBaselinePredictions:
    """Predictions aligned with the caller's test-record order."""

    previous_day_kwh: tuple[float, ...]
    seven_day_rolling_mean_kwh: tuple[float, ...]
    same_weekday_last_week_kwh: tuple[float, ...]


def predict_time_series_baselines(
    training: list[DailyEnergyRecord], test: list[DailyEnergyRecord]
) -> TimeSeriesBaselinePredictions:
    """Predict each test row using only values observed before its date.

    This is a rolling-origin backtest: once a test date has been predicted, its
    observations become history for later dates. Missing lags use the venue's mean
    from the original training period, so every fallback is also leakage-safe.
    """
    if not training or not test:
        raise ValueError("Non-empty training and test records are required")

    training_end = max(date.fromisoformat(record.utc_date) for record in training)
    test_start = min(date.fromisoformat(record.utc_date) for record in test)
    if training_end >= test_start:
        raise ValueError("All training dates must be earlier than every test date")

    venue_values: dict[str, list[float]] = {}
    history: dict[str, dict[date, float]] = {}
    for record in training:
        record_date = date.fromisoformat(record.utc_date)
        venue_history = history.setdefault(record.venue_id, {})
        if record_date in venue_history:
            raise ValueError("Each venue must have at most one record per date")
        venue_history[record_date] = record.electricity_kwh
        venue_values.setdefault(record.venue_id, []).append(record.electricity_kwh)

    fallback = {venue_id: fmean(values) for venue_id, values in venue_values.items()}
    indexed_test = sorted(
        enumerate(test), key=lambda item: (item[1].utc_date, item[1].venue_id)
    )
    previous_day = [0.0] * len(test)
    rolling_mean = [0.0] * len(test)
    same_weekday = [0.0] * len(test)

    position = 0
    while position < len(indexed_test):
        current_date = date.fromisoformat(indexed_test[position][1].utc_date)
        date_group = []
        while position < len(indexed_test):
            index, record = indexed_test[position]
            if date.fromisoformat(record.utc_date) != current_date:
                break
            date_group.append((index, record))
            position += 1

        # Predict the entire date before adding any outcomes from that date.
        if len({record.venue_id for _, record in date_group}) != len(date_group):
            raise ValueError("Each venue must have at most one record per date")
        for index, record in date_group:
            if record.venue_id not in fallback:
                raise ValueError(f"Test venue missing from training: {record.venue_id}")
            venue_history = history[record.venue_id]
            default = fallback[record.venue_id]
            previous_day[index] = venue_history.get(current_date - timedelta(days=1), default)
            same_weekday[index] = venue_history.get(current_date - timedelta(days=7), default)
            earlier_values = [
                value
                for observed_date, value in sorted(venue_history.items(), reverse=True)
                if observed_date < current_date
            ][:7]
            rolling_mean[index] = fmean(earlier_values) if earlier_values else default

        for _, record in date_group:
            history[record.venue_id][current_date] = record.electricity_kwh

    return TimeSeriesBaselinePredictions(
        previous_day_kwh=tuple(previous_day),
        seven_day_rolling_mean_kwh=tuple(rolling_mean),
        same_weekday_last_week_kwh=tuple(same_weekday),
    )
