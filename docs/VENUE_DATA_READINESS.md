# Venue data import and readiness

This tool converts one venue's supplier export into the daily format used by the frozen
confirmation pipeline. It checks preparation requirements but never fits, scores or
changes the frozen model.

## What to obtain

Ask the venue for at least 90 dates of half-hourly electricity readings: 30 or more for
earlier training history and 60 for the reserved confirmation period. More history is
preferable. Each row must contain:

- an ISO 8601 timestamp with its UTC offset;
- electricity consumed during that half hour, in kWh or Wh; and
- optionally, a quality value: `verified`, `estimated`, `missing` or `fault`.

Do not put the business name, address, meter number or account number in the project.
Assign a pseudonym matching `VENUE-0000`, such as `VENUE-0001`.

The separate weather file follows
[`data/templates/daily_weather.csv`](../data/templates/daily_weather.csv). It needs one
daily mean outdoor temperature for every complete meter date.

## Convert and check

Supplier column names vary, so pass their names explicitly:

```bash
prepare-venue-data supplier_export.csv daily_weather.csv prepared_daily.csv \
  --venue-id VENUE-0001 \
  --venue-type hotel \
  --timestamp-column "Reading time" \
  --energy-column "Consumption Wh" \
  --energy-unit wh \
  --quality-column "Quality"
```

Omit `--quality-column` only when every supplied value is a directly measured reading.
The defaults are `timestamp`, `electricity_kwh` and `kwh`.

The command:

1. converts timestamps to UTC and rejects timestamps that do not identify their offset;
2. converts Wh to kWh when requested;
3. rejects duplicate venue/timestamp pairs and invalid values;
4. sums only days with all 48 verified half-hour intervals;
5. joins temperature by UTC date;
6. reports incomplete dates and missing weather rather than filling them; and
7. writes a CSV that the frozen confirmation command can read.

`Ready for frozen confirmation: yes` means at least 90 eligible dates exist, including
the required 60-date confirmation reserve. It does not mean the model passed. Complete
the provenance metadata and run the confirmation command only after the outcome period
has been fixed and declared unseen, as described in
[`CONFIRMATION_PIPELINE.md`](CONFIRMATION_PIPELINE.md).
