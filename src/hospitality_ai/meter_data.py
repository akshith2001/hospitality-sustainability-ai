"""Schema and validation for real-world 30-minute smart-meter readings."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


VENUE_ID_PATTERN = re.compile(r"^VENUE-\d{4}$")
QUALITY_FLAGS = frozenset({"verified", "estimated", "missing", "fault"})


@dataclass(frozen=True)
class MeterReading:
    venue_id: str
    interval_start_utc: str
    interval_minutes: int
    electricity_kwh: float | None
    quality_flag: str


@dataclass(frozen=True)
class DailyMeterSummary:
    venue_id: str
    utc_date: str
    available_kwh: float
    verified_intervals: int
    estimated_intervals: int
    unavailable_intervals: int
    coverage_pct: float
    quality_status: str


@dataclass(frozen=True)
class DailyReconciliation:
    interval_sum_kwh: float
    verified_daily_total_kwh: float
    difference_kwh: float
    difference_pct: float
    within_tolerance: bool
    status: str


def validate_reading(reading: MeterReading) -> tuple[str, ...]:
    """Return every validation problem rather than failing at the first one."""
    errors = []
    if not VENUE_ID_PATTERN.fullmatch(reading.venue_id):
        errors.append("venue_id must match VENUE-0000")
    try:
        timestamp = datetime.fromisoformat(reading.interval_start_utc.replace("Z", "+00:00"))
        if timestamp.tzinfo is None or timestamp.utcoffset() != timezone.utc.utcoffset(timestamp):
            errors.append("interval_start_utc must include UTC timezone information")
        if timestamp.minute not in (0, 30) or timestamp.second or timestamp.microsecond:
            errors.append("timestamp must align to a 30-minute boundary")
    except ValueError:
        errors.append("interval_start_utc must be a valid ISO 8601 timestamp")
    if reading.interval_minutes != 30:
        errors.append("interval_minutes must equal 30")
    if reading.quality_flag not in QUALITY_FLAGS:
        errors.append("quality_flag is invalid")
    if reading.quality_flag in {"missing", "fault"}:
        if reading.electricity_kwh is not None:
            errors.append("missing or faulty readings must not contain a kWh value")
    elif reading.electricity_kwh is None or reading.electricity_kwh < 0:
        errors.append("verified or estimated readings require non-negative kWh")
    return tuple(errors)


def validate_dataset(readings: list[MeterReading]) -> tuple[str, ...]:
    errors = []
    seen = set()
    for row_number, reading in enumerate(readings, start=2):
        errors.extend(f"row {row_number}: {error}" for error in validate_reading(reading))
        key = (reading.venue_id, reading.interval_start_utc)
        if key in seen:
            errors.append(f"row {row_number}: duplicate venue and timestamp")
        seen.add(key)
    return tuple(errors)


def primary_evaluation_readings(readings: list[MeterReading]) -> list[MeterReading]:
    """Return only directly measured readings suitable for primary evaluation."""
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid meter data: " + "; ".join(errors))
    return [reading for reading in readings if reading.quality_flag == "verified"]


def sensitivity_evaluation_readings(readings: list[MeterReading]) -> list[MeterReading]:
    """Return measured and estimated values for a separately labelled analysis."""
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid meter data: " + "; ".join(errors))
    return [
        reading
        for reading in readings
        if reading.quality_flag in {"verified", "estimated"}
    ]


def summarise_utc_day(readings: list[MeterReading]) -> DailyMeterSummary:
    """Reconcile one venue's UTC day without inventing missing consumption."""
    if not readings:
        raise ValueError("At least one reading is required")
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid meter data: " + "; ".join(errors))
    venue_ids = {reading.venue_id for reading in readings}
    dates = {
        datetime.fromisoformat(reading.interval_start_utc.replace("Z", "+00:00"))
        .date()
        .isoformat()
        for reading in readings
    }
    if len(venue_ids) != 1 or len(dates) != 1:
        raise ValueError("All readings must belong to one venue and one UTC date")
    if len(readings) > 48:
        raise ValueError("A UTC day cannot contain more than 48 half-hour intervals")
    verified = sum(reading.quality_flag == "verified" for reading in readings)
    estimated = sum(reading.quality_flag == "estimated" for reading in readings)
    explicitly_unavailable = sum(
        reading.quality_flag in {"missing", "fault"} for reading in readings
    )
    implicit_missing = 48 - len(readings)
    unavailable = explicitly_unavailable + implicit_missing
    available = [
        reading.electricity_kwh
        for reading in readings
        if reading.electricity_kwh is not None
    ]
    if verified == 48:
        status = "complete_verified"
    elif verified + estimated == 48:
        status = "complete_with_estimates"
    else:
        status = "incomplete"
    return DailyMeterSummary(
        venue_id=next(iter(venue_ids)),
        utc_date=next(iter(dates)),
        available_kwh=sum(available),
        verified_intervals=verified,
        estimated_intervals=estimated,
        unavailable_intervals=unavailable,
        coverage_pct=(verified + estimated) / 48 * 100,
        quality_status=status,
    )


def reconcile_daily_total(
    summary: DailyMeterSummary,
    verified_daily_total_kwh: float,
    tolerance_pct: float = 1.0,
) -> DailyReconciliation:
    """Compare complete interval data with an independently verified daily total."""
    if verified_daily_total_kwh < 0:
        raise ValueError("verified_daily_total_kwh cannot be negative")
    if tolerance_pct < 0:
        raise ValueError("tolerance_pct cannot be negative")
    difference = summary.available_kwh - verified_daily_total_kwh
    denominator = max(verified_daily_total_kwh, 1e-9)
    difference_pct = abs(difference) / denominator * 100
    complete = summary.quality_status == "complete_verified"
    within_tolerance = complete and difference_pct <= tolerance_pct
    if not complete:
        status = "not_comparable_incomplete_intervals"
    elif within_tolerance:
        status = "reconciled"
    else:
        status = "mismatch_requires_investigation"
    return DailyReconciliation(
        interval_sum_kwh=summary.available_kwh,
        verified_daily_total_kwh=verified_daily_total_kwh,
        difference_kwh=difference,
        difference_pct=difference_pct,
        within_tolerance=within_tolerance,
        status=status,
    )


def write_meter_csv(readings: list[MeterReading], output_path: Path) -> None:
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid meter data: " + "; ".join(errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MeterReading.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(reading) for reading in readings)
