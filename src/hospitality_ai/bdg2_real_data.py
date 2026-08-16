"""Prepare a small real hospitality-energy subset from Building Data Genome 2."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SOURCE_DOI = "https://doi.org/10.5281/zenodo.3887306"


@dataclass(frozen=True)
class HospitalityBuilding:
    building_id: str
    site_id: str
    venue_type: str
    floor_area_sqm: float


def load_hospitality_buildings(metadata_path: Path) -> tuple[HospitalityBuilding, ...]:
    """Select food-service buildings and records explicitly labelled as hotels."""
    selected = []
    with metadata_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            primary_use = (row.get("primaryspaceusage") or "").strip()
            subindustry = (row.get("subindustry") or "").strip()
            has_electricity = (row.get("electricity") or "").strip().lower() == "yes"
            is_hospitality = (
                primary_use.lower() == "food sales and service"
                or subindustry.lower() == "hotel"
            )
            if not (has_electricity and is_hospitality):
                continue
            selected.append(
                HospitalityBuilding(
                    building_id=row["building_id"],
                    site_id=row["site_id"],
                    venue_type="hotel" if subindustry.lower() == "hotel" else "food_service",
                    floor_area_sqm=float(row["sqm"]),
                )
            )
    return tuple(sorted(selected, key=lambda item: item.building_id))


def load_daily_weather(weather_path: Path, site_ids: set[str]) -> dict[tuple[str, str], float]:
    """Return daily mean air temperature for the selected sites."""
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    with weather_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            site_id = row["site_id"]
            temperature = (row.get("airTemperature") or "").strip()
            if site_id not in site_ids or not temperature:
                continue
            utc_date = datetime.fromisoformat(row["timestamp"]).date().isoformat()
            values[(site_id, utc_date)].append(float(temperature))
    return {
        key: sum(temperatures) / len(temperatures)
        for key, temperatures in values.items()
    }


def build_daily_records(
    electricity_path: Path,
    buildings: tuple[HospitalityBuilding, ...],
    daily_weather: dict[tuple[str, str], float],
    minimum_observed_hours: int = 20,
) -> list[dict[str, str]]:
    """Aggregate hourly kWh to complete-enough daily observations."""
    building_by_id = {building.building_id: building for building in buildings}
    totals: dict[tuple[str, str], float] = defaultdict(float)
    observed: dict[tuple[str, str], int] = defaultdict(int)
    with electricity_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing_columns = set(building_by_id) - set(reader.fieldnames or ())
        if missing_columns:
            raise ValueError(f"Electricity columns not found: {sorted(missing_columns)}")
        for row in reader:
            utc_date = datetime.fromisoformat(row["timestamp"]).date().isoformat()
            for building_id in building_by_id:
                reading = (row.get(building_id) or "").strip()
                if not reading:
                    continue
                key = (building_id, utc_date)
                totals[key] += float(reading)
                observed[key] += 1

    records = []
    for key in sorted(totals):
        building_id, utc_date = key
        hours = observed[key]
        if hours < minimum_observed_hours:
            continue
        building = building_by_id[building_id]
        temperature = daily_weather.get((building.site_id, utc_date))
        records.append(
            {
                "venue_id": building_id,
                "utc_date": utc_date,
                "venue_type": building.venue_type,
                "floor_area_sqm": f"{building.floor_area_sqm:.1f}",
                "outside_temperature_c": "" if temperature is None else f"{temperature:.2f}",
                "observed_hours": str(hours),
                "electricity_kwh": f"{totals[key]:.3f}",
                "data_source": "BDG2 v1.0",
            }
        )
    return records


def write_records(records: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "venue_id",
        "utc_date",
        "venue_type",
        "floor_area_sqm",
        "outside_temperature_c",
        "observed_hours",
        "electricity_kwh",
        "data_source",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def prepare_dataset(source_root: Path, output_path: Path) -> tuple[int, int]:
    metadata_path = source_root / "data" / "metadata" / "metadata.csv"
    electricity_path = source_root / "data" / "meters" / "cleaned" / "electricity_cleaned.csv"
    weather_path = source_root / "data" / "weather" / "weather.csv"
    buildings = load_hospitality_buildings(metadata_path)
    weather = load_daily_weather(weather_path, {building.site_id for building in buildings})
    records = build_daily_records(electricity_path, buildings, weather)
    write_records(records, output_path)
    return len(buildings), len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="Extracted BDG2 repository root")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/bdg2_hospitality_daily.csv"),
    )
    args = parser.parse_args()
    building_count, record_count = prepare_dataset(args.source_root, args.output)
    print(f"Wrote {record_count} daily records for {building_count} buildings to {args.output}")
    print(f"Source: {SOURCE_DOI}")


if __name__ == "__main__":
    main()
