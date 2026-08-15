"""Validated daily operational context for real hospitality meter data."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from .meter_data import VENUE_ID_PATTERN


DATA_QUALITY = frozenset({"verified", "estimated"})
EVENT_COUNT_QUALITY = frozenset({"verified", "estimated", "missing", "not_applicable"})
EVENT_CATEGORIES = frozenset(
    {"none", "wedding", "conference", "private_event", "holiday", "other"}
)


@dataclass(frozen=True)
class DailyOperationalContext:
    venue_id: str
    utc_date: str
    customers: int
    customers_quality: str
    opening_hours: float
    outside_temperature_c: float
    weather_station_id: str
    special_event_category: str
    event_guest_count: int | None
    event_guest_count_quality: str
    equipment_change: bool


def validate_context(context: DailyOperationalContext) -> tuple[str, ...]:
    errors = []
    if not VENUE_ID_PATTERN.fullmatch(context.venue_id):
        errors.append("venue_id must match VENUE-0000")
    try:
        date.fromisoformat(context.utc_date)
    except ValueError:
        errors.append("utc_date must be a valid ISO date")
    if context.customers < 0:
        errors.append("customers cannot be negative")
    if context.customers_quality not in DATA_QUALITY:
        errors.append("customers_quality must be verified or estimated")
    if not 0 <= context.opening_hours <= 24:
        errors.append("opening_hours must be between 0 and 24")
    if not -60 <= context.outside_temperature_c <= 60:
        errors.append("outside_temperature_c is outside the accepted range")
    if not context.weather_station_id.strip():
        errors.append("weather_station_id is required")
    if context.special_event_category not in EVENT_CATEGORIES:
        errors.append("special_event_category is invalid")
    if context.event_guest_count_quality not in EVENT_COUNT_QUALITY:
        errors.append("event_guest_count_quality is invalid")
    if context.special_event_category == "none":
        if context.event_guest_count != 0:
            errors.append("no event requires event_guest_count of 0")
        if context.event_guest_count_quality != "not_applicable":
            errors.append("no event requires not_applicable guest-count quality")
    elif context.event_guest_count_quality == "missing":
        if context.event_guest_count is not None:
            errors.append("missing event guest count must have a blank value")
    elif context.event_guest_count_quality in {"verified", "estimated"}:
        if context.event_guest_count is None or context.event_guest_count < 0:
            errors.append("known event guest count must be non-negative")
    elif context.event_guest_count_quality == "not_applicable":
        errors.append("an event cannot have not_applicable guest-count quality")
    if not isinstance(context.equipment_change, bool):
        errors.append("equipment_change must be boolean")
    return tuple(errors)


def validate_context_dataset(
    contexts: list[DailyOperationalContext],
) -> tuple[str, ...]:
    errors = []
    seen = set()
    for row_number, context in enumerate(contexts, start=2):
        errors.extend(f"row {row_number}: {error}" for error in validate_context(context))
        key = (context.venue_id, context.utc_date)
        if key in seen:
            errors.append(f"row {row_number}: duplicate venue and date")
        seen.add(key)
    return tuple(errors)


def write_context_csv(
    contexts: list[DailyOperationalContext], output_path: Path
) -> None:
    errors = validate_context_dataset(contexts)
    if errors:
        raise ValueError("Invalid operational context: " + "; ".join(errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(DailyOperationalContext.__annotations__)
        )
        writer.writeheader()
        writer.writerows(asdict(context) for context in contexts)
