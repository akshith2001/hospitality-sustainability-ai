import unittest
from dataclasses import replace

from hospitality_ai.meter_data import DailyMeterSummary
from hospitality_ai.operational_context import DailyOperationalContext
from hospitality_ai.research_dataset import (
    build_data_quality_report,
    build_venue_quality_reports,
    join_daily_data,
    primary_evaluation_records,
)


def meter_summary(date: str = "2026-01-01") -> DailyMeterSummary:
    return DailyMeterSummary(
        venue_id="VENUE-0001",
        utc_date=date,
        available_kwh=600.0,
        verified_intervals=48,
        estimated_intervals=0,
        unavailable_intervals=0,
        coverage_pct=100.0,
        quality_status="complete_verified",
    )


def context(date: str = "2026-01-01") -> DailyOperationalContext:
    return DailyOperationalContext(
        venue_id="VENUE-0001",
        utc_date=date,
        customers=180,
        customers_quality="verified",
        opening_hours=12.0,
        outside_temperature_c=8.5,
        weather_station_id="WX-LONDON-01",
        special_event_category="none",
        event_guest_count=0,
        event_guest_count_quality="not_applicable",
        equipment_change=False,
    )


class ResearchDatasetTests(unittest.TestCase):
    def test_matching_venue_and_date_are_joined(self) -> None:
        result = join_daily_data([meter_summary()], [context()])
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0].electricity_kwh, 600.0)

    def test_unmatched_rows_are_reported(self) -> None:
        result = join_daily_data([meter_summary()], [context("2026-01-02")])
        self.assertEqual(result.records, ())
        self.assertEqual(result.unmatched_meter_keys, (("VENUE-0001", "2026-01-01"),))
        self.assertEqual(result.unmatched_context_keys, (("VENUE-0001", "2026-01-02"),))

    def test_primary_evaluation_requires_verified_inputs(self) -> None:
        verified = join_daily_data([meter_summary()], [context()])
        self.assertEqual(len(primary_evaluation_records(verified)), 1)
        estimated_context = replace(context(), customers_quality="estimated")
        estimated = join_daily_data([meter_summary()], [estimated_context])
        self.assertEqual(primary_evaluation_records(estimated), ())

    def test_duplicate_meter_summary_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            join_daily_data([meter_summary(), meter_summary()], [context()])

    def test_quality_report_counts_exclusions_and_missing_context(self) -> None:
        summaries = [meter_summary(), meter_summary("2026-01-02")]
        estimated = replace(context(), customers_quality="estimated")
        result = join_daily_data(summaries, [estimated])
        report = build_data_quality_report(result, len(summaries), 1)
        reasons = dict(report.exclusion_reasons)
        self.assertEqual(report.primary_evaluation_count, 0)
        self.assertEqual(report.unmatched_meter_count, 1)
        self.assertEqual(reasons["customers_not_verified"], 1)
        self.assertEqual(reasons["operational_context_missing"], 1)

    def test_venue_quality_report_exposes_uneven_missingness(self) -> None:
        second_venue = replace(
            meter_summary("2026-01-01"), venue_id="VENUE-0002"
        )
        summaries = [meter_summary(), second_venue]
        contexts = [context()]
        result = join_daily_data(summaries, contexts)
        reports = {
            report.venue_id: report
            for report in build_venue_quality_reports(result, summaries, contexts)
        }
        self.assertEqual(reports["VENUE-0001"].primary_evaluation_count, 1)
        self.assertEqual(reports["VENUE-0002"].unmatched_meter_count, 1)
        self.assertEqual(reports["VENUE-0002"].primary_evaluation_count, 0)


if __name__ == "__main__":
    unittest.main()
