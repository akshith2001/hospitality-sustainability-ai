"""Generate transparent synthetic hospitality electricity data.

The formula is intentionally visible. Synthetic data are useful for learning and
software verification, but they are not evidence of real-world model accuracy.
"""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path


VENUE_BASE_KWH = {
    "restaurant": 45.0,
    "hotel": 80.0,
    "bar": 35.0,
    "event_venue": 55.0,
}


@dataclass(frozen=True)
class DailyVenueRecord:
    date: str
    day_of_week: str
    venue_id: str
    venue_type: str
    customers: int
    opening_hours: float
    outside_temperature_c: float
    floor_area_m2: float
    kitchen_equipment_count: int
    electricity_kwh: float
    is_injected_anomaly: int


def expected_electricity_kwh(
    venue_type: str,
    customers: int,
    opening_hours: float,
    outside_temperature_c: float,
    floor_area_m2: float,
    kitchen_equipment_count: int,
) -> float:
    """Return the noise-free electricity value used by the generator."""
    if venue_type not in VENUE_BASE_KWH:
        raise ValueError(f"Unknown venue type: {venue_type}")
    if min(customers, opening_hours, floor_area_m2, kitchen_equipment_count) < 0:
        raise ValueError("Operational inputs cannot be negative")

    # Heating/cooling demand grows when temperature moves away from 18 C.
    temperature_effect = 0.32 * (outside_temperature_c - 18.0) ** 2
    return (
        VENUE_BASE_KWH[venue_type]
        + 0.38 * customers
        + 4.8 * opening_hours
        + 0.11 * floor_area_m2
        + 5.5 * kitchen_equipment_count
        + temperature_effect
    )


def generate_records(
    row_count: int = 1_000,
    seed: int = 2026,
    anomaly_rate: float = 0.05,
    start_date: date = date(2026, 1, 1),
) -> list[DailyVenueRecord]:
    """Generate reproducible daily records with a small set of injected anomalies."""
    if row_count < 1:
        raise ValueError("row_count must be positive")
    if not 0 <= anomaly_rate <= 1:
        raise ValueError("anomaly_rate must be between 0 and 1")

    rng = random.Random(seed)
    records = []
    venue_types = tuple(VENUE_BASE_KWH)
    for day_index in range(row_count):
        observation_date = start_date + timedelta(days=day_index)
        venue_type = rng.choice(venue_types)
        customers = rng.randint(20, 450)
        opening_hours = rng.uniform(6.0, 18.0)
        outside_temperature_c = rng.uniform(-2.0, 34.0)
        floor_area_m2 = rng.uniform(60.0, 850.0)
        kitchen_equipment_count = rng.randint(4, 35)
        expected = expected_electricity_kwh(
            venue_type,
            customers,
            opening_hours,
            outside_temperature_c,
            floor_area_m2,
            kitchen_equipment_count,
        )
        ordinary_noise = rng.gauss(0.0, max(5.0, expected * 0.04))
        is_anomaly = int(rng.random() < anomaly_rate)
        excess_use = rng.uniform(0.25, 0.60) * expected if is_anomaly else 0.0
        electricity_kwh = max(0.0, expected + ordinary_noise + excess_use)
        records.append(
            DailyVenueRecord(
                date=observation_date.isoformat(),
                day_of_week=observation_date.strftime("%A"),
                venue_id=f"VENUE-{venue_types.index(venue_type) * 5 + day_index % 5 + 1:03d}",
                venue_type=venue_type,
                customers=customers,
                opening_hours=round(opening_hours, 2),
                outside_temperature_c=round(outside_temperature_c, 2),
                floor_area_m2=round(floor_area_m2, 1),
                kitchen_equipment_count=kitchen_equipment_count,
                electricity_kwh=round(electricity_kwh, 2),
                is_injected_anomaly=is_anomaly,
            )
        )
    return records


def write_csv(records: list[DailyVenueRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(DailyVenueRecord.__annotations__))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic hospitality data")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--anomaly-rate", type=float, default=0.05)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/hospitality_daily.csv"),
    )
    args = parser.parse_args()
    records = generate_records(args.rows, args.seed, args.anomaly_rate)
    write_csv(records, args.output)
    anomaly_count = sum(record.is_injected_anomaly for record in records)
    print(f"Wrote {len(records):,} synthetic rows to {args.output}")
    print(f"Injected anomalies: {anomaly_count} ({anomaly_count / len(records):.1%})")


if __name__ == "__main__":
    main()
