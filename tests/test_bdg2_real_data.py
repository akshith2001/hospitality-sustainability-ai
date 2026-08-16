import csv
import tempfile
import unittest
from pathlib import Path

from hospitality_ai.bdg2_real_data import (
    build_daily_records,
    load_hospitality_buildings,
)


class Bdg2RealDataTests(unittest.TestCase):
    def test_selects_food_service_and_hotels_with_electricity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.csv"
            path.write_text(
                "building_id,site_id,primaryspaceusage,subindustry,sqm,electricity\n"
                "Food_1,Fox,Food sales and service,,100,Yes\n"
                "Hotel_1,Lamb,Lodging/residential,Hotel,200,Yes\n"
                "Office_1,Fox,Office,,300,Yes\n"
                "Food_no_meter,Fox,Food sales and service,,100,\n",
                encoding="utf-8",
            )
            buildings = load_hospitality_buildings(path)
            self.assertEqual([item.building_id for item in buildings], ["Food_1", "Hotel_1"])
            self.assertEqual([item.venue_type for item in buildings], ["food_service", "hotel"])

    def test_daily_aggregation_excludes_low_coverage_day(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = Path(directory) / "metadata.csv"
            metadata.write_text(
                "building_id,site_id,primaryspaceusage,subindustry,sqm,electricity\n"
                "Food_1,Fox,Food sales and service,,100,Yes\n",
                encoding="utf-8",
            )
            electricity = Path(directory) / "electricity.csv"
            with electricity.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["timestamp", "Food_1"])
                for hour in range(24):
                    writer.writerow([f"2016-01-01 {hour:02d}:00:00", "2.0"])
                for hour in range(19):
                    writer.writerow([f"2016-01-02 {hour:02d}:00:00", "3.0"])
            records = build_daily_records(
                electricity,
                load_hospitality_buildings(metadata),
                {("Fox", "2016-01-01"): 10.0},
            )
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["electricity_kwh"], "48.000")
            self.assertEqual(records[0]["observed_hours"], "24")


if __name__ == "__main__":
    unittest.main()
