"""Convert supplier interval exports and check frozen-evaluation readiness."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .meter_data import MeterReading, summarise_utc_day, validate_dataset


SUPPORTED_ENERGY_UNITS = frozenset({"kwh", "wh"})


@dataclass(frozen=True)
class PreparedDailyRecord:
    venue_id: str
    utc_date: str
    venue_type: str
    outside_temperature_c: float
    electricity_kwh: float


@dataclass(frozen=True)
class ReadinessReport:
    source_interval_rows: int
    source_dates: int
    complete_verified_dates: int
    incomplete_dates: int
    complete_dates_missing_weather: int
    eligible_daily_records: int
    earliest_eligible_date: str | None
    latest_eligible_date: str | None
    required_training_dates: int
    required_confirmation_dates: int
    ready_for_frozen_confirmation: bool
    reasons: tuple[str, ...]


def _normalise_timestamp(value: str) -> str:
    try:
        timestamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid ISO 8601 timestamp: {value!r}") from error
    if timestamp.tzinfo is None:
        raise ValueError("Supplier timestamps must include a UTC offset")
    utc_timestamp = timestamp.astimezone(timezone.utc)
    if utc_timestamp.minute not in (0, 30) or utc_timestamp.second or utc_timestamp.microsecond:
        raise ValueError("Supplier timestamps must align to a UTC 30-minute boundary")
    return utc_timestamp.isoformat().replace("+00:00", "Z")


def import_supplier_intervals(
    path: Path,
    venue_id: str,
    timestamp_column: str,
    energy_column: str,
    energy_unit: str = "kwh",
    quality_column: str | None = None,
) -> list[MeterReading]:
    """Map a supplier CSV into the project's anonymous interval schema."""
    unit = energy_unit.casefold()
    if unit not in SUPPORTED_ENERGY_UNITS:
        raise ValueError(f"energy_unit must be one of {sorted(SUPPORTED_ENERGY_UNITS)}")
    readings = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {timestamp_column, energy_column}
        if quality_column:
            required.add(quality_column)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Supplier CSV is missing columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            try:
                raw_energy = row[energy_column].strip()
                quality = (
                    row[quality_column].strip().casefold()
                    if quality_column
                    else "verified"
                )
                electricity_kwh = None if not raw_energy else float(raw_energy)
                if electricity_kwh is not None and unit == "wh":
                    electricity_kwh /= 1000.0
                readings.append(
                    MeterReading(
                        venue_id=venue_id,
                        interval_start_utc=_normalise_timestamp(row[timestamp_column]),
                        interval_minutes=30,
                        electricity_kwh=electricity_kwh,
                        quality_flag=quality,
                    )
                )
            except (KeyError, ValueError) as error:
                raise ValueError(f"Supplier CSV row {row_number}: {error}") from error
    if not readings:
        raise ValueError("Supplier CSV contains no readings")
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid converted meter data: " + "; ".join(errors))
    return sorted(readings, key=lambda item: item.interval_start_utc)


def load_daily_weather(path: Path) -> dict[str, float]:
    """Load daily temperatures keyed by UTC date."""
    temperatures = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"utc_date", "outside_temperature_c"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Weather CSV is missing columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            utc_date = row["utc_date"].strip()
            try:
                datetime.fromisoformat(utc_date)
                temperature = float(row["outside_temperature_c"])
            except ValueError as error:
                raise ValueError(f"Weather CSV row {row_number}: invalid value") from error
            if utc_date in temperatures:
                raise ValueError(f"Weather CSV row {row_number}: duplicate UTC date")
            temperatures[utc_date] = temperature
    return temperatures


def prepare_daily_records(
    readings: list[MeterReading],
    temperatures: dict[str, float],
    venue_type: str,
    required_training_dates: int = 30,
    required_confirmation_dates: int = 60,
) -> tuple[list[PreparedDailyRecord], ReadinessReport]:
    """Aggregate complete verified days and produce a non-evaluative readiness report."""
    if not venue_type.strip():
        raise ValueError("venue_type is required")
    if required_training_dates < 1 or required_confirmation_dates < 60:
        raise ValueError("Require at least 1 training date and 60 confirmation dates")
    errors = validate_dataset(readings)
    if errors:
        raise ValueError("Invalid meter data: " + "; ".join(errors))
    venue_ids = {reading.venue_id for reading in readings}
    if len(venue_ids) != 1:
        raise ValueError("Prepare one pseudonymous venue per run")
    groups: dict[tuple[str, str], list[MeterReading]] = {}
    for reading in readings:
        utc_date = reading.interval_start_utc[:10]
        groups.setdefault((reading.venue_id, utc_date), []).append(reading)

    complete_dates = 0
    incomplete_dates = 0
    missing_weather = 0
    daily_records = []
    for (venue_id, utc_date), day_readings in sorted(groups.items()):
        summary = summarise_utc_day(day_readings)
        if summary.quality_status != "complete_verified":
            incomplete_dates += 1
            continue
        complete_dates += 1
        if utc_date not in temperatures:
            missing_weather += 1
            continue
        daily_records.append(
            PreparedDailyRecord(
                venue_id=venue_id,
                utc_date=utc_date,
                venue_type=venue_type.strip(),
                outside_temperature_c=temperatures[utc_date],
                electricity_kwh=summary.available_kwh,
            )
        )

    required_total = required_training_dates + required_confirmation_dates
    reasons = []
    if incomplete_dates:
        reasons.append(f"{incomplete_dates} source dates are not complete and verified")
    if missing_weather:
        reasons.append(f"{missing_weather} complete dates have no weather match")
    if len(daily_records) < required_total:
        reasons.append(
            f"need {required_total} eligible dates but found {len(daily_records)}"
        )
    dates = [record.utc_date for record in daily_records]
    ready = len(daily_records) >= required_total and missing_weather == 0
    report = ReadinessReport(
        source_interval_rows=len(readings),
        source_dates=len(groups),
        complete_verified_dates=complete_dates,
        incomplete_dates=incomplete_dates,
        complete_dates_missing_weather=missing_weather,
        eligible_daily_records=len(daily_records),
        earliest_eligible_date=min(dates) if dates else None,
        latest_eligible_date=max(dates) if dates else None,
        required_training_dates=required_training_dates,
        required_confirmation_dates=required_confirmation_dates,
        ready_for_frozen_confirmation=ready,
        reasons=tuple(reasons),
    )
    return daily_records, report


def write_daily_records(records: list[PreparedDailyRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(PreparedDailyRecord.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("supplier_csv", type=Path)
    parser.add_argument("weather_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--venue-id", required=True)
    parser.add_argument("--venue-type", required=True)
    parser.add_argument("--timestamp-column", default="timestamp")
    parser.add_argument("--energy-column", default="electricity_kwh")
    parser.add_argument("--energy-unit", choices=sorted(SUPPORTED_ENERGY_UNITS), default="kwh")
    parser.add_argument("--quality-column")
    args = parser.parse_args()
    readings = import_supplier_intervals(
        args.supplier_csv,
        args.venue_id,
        args.timestamp_column,
        args.energy_column,
        args.energy_unit,
        args.quality_column,
    )
    records, report = prepare_daily_records(
        readings, load_daily_weather(args.weather_csv), args.venue_type
    )
    write_daily_records(records, args.output_csv)
    print(f"Supplier interval rows: {report.source_interval_rows:,}")
    print(f"Complete verified dates: {report.complete_verified_dates:,}")
    print(f"Eligible daily records: {report.eligible_daily_records:,}")
    print(
        "Ready for frozen confirmation: "
        + ("yes" if report.ready_for_frozen_confirmation else "no")
    )
    for reason in report.reasons:
        print(f"  - {reason}")


if __name__ == "__main__":
    main()
