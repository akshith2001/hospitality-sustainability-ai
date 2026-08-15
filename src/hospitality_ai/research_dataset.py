"""Join reconciled meter summaries with daily operational context."""

from __future__ import annotations

from dataclasses import dataclass

from .meter_data import DailyMeterSummary
from .operational_context import DailyOperationalContext, validate_context_dataset


@dataclass(frozen=True)
class JoinedDailyRecord:
    venue_id: str
    utc_date: str
    electricity_kwh: float
    meter_quality_status: str
    meter_coverage_pct: float
    customers: int
    customers_quality: str
    opening_hours: float
    outside_temperature_c: float
    weather_station_id: str
    special_event_category: str
    event_guest_count: int | None
    event_guest_count_quality: str
    equipment_change: bool

    @property
    def eligible_for_primary_evaluation(self) -> bool:
        return (
            self.meter_quality_status == "complete_verified"
            and self.customers_quality == "verified"
            and self.event_guest_count_quality in {"verified", "not_applicable"}
        )


@dataclass(frozen=True)
class DatasetJoinResult:
    records: tuple[JoinedDailyRecord, ...]
    unmatched_meter_keys: tuple[tuple[str, str], ...]
    unmatched_context_keys: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class DataQualityReport:
    meter_summary_count: int
    context_count: int
    joined_count: int
    primary_evaluation_count: int
    unmatched_meter_count: int
    unmatched_context_count: int
    exclusion_reasons: tuple[tuple[str, int], ...]


def join_daily_data(
    meter_summaries: list[DailyMeterSummary],
    contexts: list[DailyOperationalContext],
) -> DatasetJoinResult:
    """Join by pseudonymous venue and UTC date while reporting all unmatched rows."""
    context_errors = validate_context_dataset(contexts)
    if context_errors:
        raise ValueError("Invalid operational context: " + "; ".join(context_errors))
    meter_by_key = {}
    for summary in meter_summaries:
        key = (summary.venue_id, summary.utc_date)
        if key in meter_by_key:
            raise ValueError(f"Duplicate meter summary for {key}")
        meter_by_key[key] = summary
    context_by_key = {(context.venue_id, context.utc_date): context for context in contexts}
    shared_keys = sorted(meter_by_key.keys() & context_by_key.keys())
    joined = []
    for key in shared_keys:
        meter = meter_by_key[key]
        context = context_by_key[key]
        joined.append(
            JoinedDailyRecord(
                venue_id=meter.venue_id,
                utc_date=meter.utc_date,
                electricity_kwh=meter.available_kwh,
                meter_quality_status=meter.quality_status,
                meter_coverage_pct=meter.coverage_pct,
                customers=context.customers,
                customers_quality=context.customers_quality,
                opening_hours=context.opening_hours,
                outside_temperature_c=context.outside_temperature_c,
                weather_station_id=context.weather_station_id,
                special_event_category=context.special_event_category,
                event_guest_count=context.event_guest_count,
                event_guest_count_quality=context.event_guest_count_quality,
                equipment_change=context.equipment_change,
            )
        )
    return DatasetJoinResult(
        records=tuple(joined),
        unmatched_meter_keys=tuple(sorted(meter_by_key.keys() - context_by_key.keys())),
        unmatched_context_keys=tuple(sorted(context_by_key.keys() - meter_by_key.keys())),
    )


def primary_evaluation_records(
    result: DatasetJoinResult,
) -> tuple[JoinedDailyRecord, ...]:
    return tuple(record for record in result.records if record.eligible_for_primary_evaluation)


def build_data_quality_report(
    result: DatasetJoinResult,
    meter_summary_count: int,
    context_count: int,
) -> DataQualityReport:
    """Count every primary-evaluation exclusion without hiding overlapping reasons."""
    reasons = {
        "meter_not_complete_verified": 0,
        "customers_not_verified": 0,
        "event_guest_count_not_verified": 0,
        "operational_context_missing": len(result.unmatched_meter_keys),
        "meter_summary_missing": len(result.unmatched_context_keys),
    }
    for record in result.records:
        if record.meter_quality_status != "complete_verified":
            reasons["meter_not_complete_verified"] += 1
        if record.customers_quality != "verified":
            reasons["customers_not_verified"] += 1
        if record.event_guest_count_quality not in {"verified", "not_applicable"}:
            reasons["event_guest_count_not_verified"] += 1
    return DataQualityReport(
        meter_summary_count=meter_summary_count,
        context_count=context_count,
        joined_count=len(result.records),
        primary_evaluation_count=len(primary_evaluation_records(result)),
        unmatched_meter_count=len(result.unmatched_meter_keys),
        unmatched_context_count=len(result.unmatched_context_keys),
        exclusion_reasons=tuple(sorted(reasons.items())),
    )
