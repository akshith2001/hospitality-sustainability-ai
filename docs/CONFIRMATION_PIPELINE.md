# Frozen confirmation pipeline

This command applies the decision rule in the
[frozen evaluation specification](FROZEN_EVALUATION_SPECIFICATION.md) to genuinely new
daily observations. It is intentionally separate from model development: do not inspect
the confirmation outcomes and then change the model, dates, exclusions or success rule.

## Inputs

The daily CSV uses the same columns as the processed BDG2 data:

- `venue_id`
- `date` in `YYYY-MM-DD` format
- `venue_type`
- `floor_area_sqm`
- `outdoor_temperature_c`
- `observed_hour_count`
- `electricity_kwh`

Include earlier historical rows as well as the new confirmation period. Each test venue
must have earlier eligible history, and the confirmation period must contain at least 60
distinct dates. The existing quality rules are applied without modification.

Copy and complete
[`data/templates/confirmation_metadata.json`](../data/templates/confirmation_metadata.json).
The metadata records the dataset, source, licence, venue rule, fixed date window and a
declaration that the outcomes were unseen when the evaluation was frozen. The command
rejects the already-observed BDG2 v1.0 period as confirmation data.

## Run

```bash
confirm-new-hospitality-data NEW_DAILY_DATA.csv \
  COMPLETED_CONFIRMATION_METADATA.json
```

The equivalent module command is:

```bash
python -m hospitality_ai.confirmation_evaluation NEW_DAILY_DATA.csv \
  COMPLETED_CONFIRMATION_METADATA.json
```

Use `--output results/confirmation.json` to save the machine-readable report. The report
contains pooled and per-venue MAE for the frozen lag-feature model and every preserved
baseline, eligibility counts, validation checks and the final pass/fail decision.

## Fixed decision rule

The candidate passes only when both conditions hold:

1. Its pooled MAE is at least 5% lower than the previous-day baseline.
2. It beats previous day for at least half of eligible venues (rounded up).

A failed confirmation remains useful evidence and must be reported as a failure rather
than used for post-hoc tuning. Any later model change should begin a separately declared
development cycle and a new unseen confirmation period.
