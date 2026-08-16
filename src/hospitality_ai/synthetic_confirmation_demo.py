"""Run a labelled synthetic rehearsal of the complete confirmation workflow."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .confirmation_evaluation import (
    ConfirmationMetadata,
    evaluate_frozen_confirmation,
    write_confirmation_report,
)
from .real_data_evaluation import load_real_daily_records
from .venue_data_readiness import (
    import_supplier_intervals,
    load_daily_weather,
    prepare_daily_records,
    write_daily_records,
)


DEMO_WARNING = "SYNTHETIC DEMONSTRATION - NOT REAL-WORLD EVIDENCE"


@dataclass(frozen=True)
class SyntheticDemoResult:
    warning: str
    seed: int
    supplier_interval_rows: int
    prepared_daily_rows: int
    ready_for_frozen_confirmation: bool
    confirmation_passed: bool
    output_directory: str


def _synthetic_days(days: int, seed: int) -> list[tuple[date, float, float]]:
    if days < 90:
        raise ValueError("The rehearsal requires at least 90 synthetic dates")
    random_generator = random.Random(seed)
    start = date(2026, 1, 1)
    rows = []
    previous = 430.0
    for offset in range(days):
        utc_date = start + timedelta(days=offset)
        annual_angle = 2 * math.pi * offset / 365.25
        temperature = 10.0 + 7.0 * math.sin(annual_angle) + random_generator.gauss(0, 1.2)
        weekday_effect = 28.0 if utc_date.weekday() in (4, 5) else 0.0
        target = (
            235.0
            + 0.48 * previous
            + 4.5 * abs(temperature - 18.0)
            + weekday_effect
            + random_generator.gauss(0, 9.0)
        )
        rows.append((utc_date, temperature, max(target, 48.0)))
        previous = target
    return rows


def _write_supplier_and_weather(
    rows: list[tuple[date, float, float]], supplier_path: Path, weather_path: Path
) -> None:
    supplier_path.parent.mkdir(parents=True, exist_ok=True)
    with supplier_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["reading_time", "consumption_wh", "quality"]
        )
        writer.writeheader()
        for utc_date, _, daily_kwh in rows:
            interval_wh = daily_kwh / 48.0 * 1000.0
            for interval in range(48):
                timestamp = datetime.combine(
                    utc_date,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                ) + timedelta(minutes=30 * interval)
                writer.writerow(
                    {
                        "reading_time": timestamp.isoformat().replace("+00:00", "Z"),
                        "consumption_wh": f"{interval_wh:.8f}",
                        "quality": "verified",
                    }
                )
    with weather_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["utc_date", "outside_temperature_c"]
        )
        writer.writeheader()
        for utc_date, temperature, _ in rows:
            writer.writerow(
                {
                    "utc_date": utc_date.isoformat(),
                    "outside_temperature_c": f"{temperature:.6f}",
                }
            )


def run_synthetic_confirmation_demo(
    output_directory: Path, days: int = 120, seed: int = 2026
) -> SyntheticDemoResult:
    """Exercise the production preparation and evaluation functions with fake data."""
    output_directory.mkdir(parents=True, exist_ok=True)
    supplier_path = output_directory / "synthetic_supplier_export.csv"
    weather_path = output_directory / "synthetic_daily_weather.csv"
    prepared_path = output_directory / "synthetic_prepared_daily.csv"
    metadata_path = output_directory / "synthetic_confirmation_metadata.json"
    report_path = output_directory / "synthetic_confirmation_report.json"
    summary_path = output_directory / "README.txt"

    synthetic_rows = _synthetic_days(days, seed)
    _write_supplier_and_weather(synthetic_rows, supplier_path, weather_path)
    readings = import_supplier_intervals(
        supplier_path,
        venue_id="VENUE-0001",
        timestamp_column="reading_time",
        energy_column="consumption_wh",
        energy_unit="wh",
        quality_column="quality",
    )
    daily_records, readiness = prepare_daily_records(
        readings, load_daily_weather(weather_path), venue_type="synthetic_hotel"
    )
    write_daily_records(daily_records, prepared_path)

    confirmation_start = synthetic_rows[-60][0].isoformat()
    confirmation_end = synthetic_rows[-1][0].isoformat()
    metadata = ConfirmationMetadata(
        dataset_id="synthetic-confirmation-demo-v1",
        dataset_title=DEMO_WARNING,
        source_url="generated-locally-by-synthetic-confirmation-demo",
        license="not-applicable-synthetic-data",
        venue_inclusion_rule="one generated synthetic hotel",
        confirmation_start_date=confirmation_start,
        confirmation_end_date=confirmation_end,
        outcomes_unseen_at_freeze=True,
    )
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2) + "\n", encoding="utf-8"
    )
    confirmation = evaluate_frozen_confirmation(
        load_real_daily_records(prepared_path), metadata
    )
    write_confirmation_report(confirmation, report_path)
    summary_path.write_text(
        f"{DEMO_WARNING}\n\n"
        "These files only rehearse the software workflow. They must not be cited as "
        "validation, external evidence or a real venue result.\n",
        encoding="utf-8",
    )
    result = SyntheticDemoResult(
        warning=DEMO_WARNING,
        seed=seed,
        supplier_interval_rows=len(readings),
        prepared_daily_rows=len(daily_records),
        ready_for_frozen_confirmation=readiness.ready_for_frozen_confirmation,
        confirmation_passed=confirmation.passed_frozen_success_rule,
        output_directory=str(output_directory),
    )
    (output_directory / "synthetic_demo_summary.json").write_text(
        json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("outputs/synthetic_confirmation_demo"),
    )
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    result = run_synthetic_confirmation_demo(
        args.output_directory, args.days, args.seed
    )
    print(result.warning)
    print(f"Supplier interval rows: {result.supplier_interval_rows:,}")
    print(f"Prepared daily rows: {result.prepared_daily_rows:,}")
    print(
        "Ready for frozen workflow: "
        + ("yes" if result.ready_for_frozen_confirmation else "no")
    )
    print(
        "Synthetic criterion result (not evidence): "
        + ("pass" if result.confirmation_passed else "fail")
    )
    print(f"Files written to: {result.output_directory}")


if __name__ == "__main__":
    main()
