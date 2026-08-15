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


def write_meter_csv(readings: list[MeterReading], output_path: Path) -> None:
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid meter data: " + "; ".join(errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MeterReading.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(reading) for reading in readings)
