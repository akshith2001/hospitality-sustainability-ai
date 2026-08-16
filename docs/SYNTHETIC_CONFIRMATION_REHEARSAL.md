# Synthetic confirmation rehearsal

The rehearsal exercises the complete venue-data workflow before a real supplier export
arrives. It generates deterministic fake half-hourly readings and weather, then uses the
same importer, readiness checks, daily aggregation, frozen evaluator and JSON report
writer used for future venue data.

```bash
run-synthetic-confirmation-demo
```

The default files are written under `outputs/synthetic_confirmation_demo/`, which is
excluded from Git because it is generated output. Use `--output-directory`, `--days` and
`--seed` to choose a different location, duration or reproducible random seed.

Every result is labelled:

> SYNTHETIC DEMONSTRATION - NOT REAL-WORLD EVIDENCE

The generated pass/fail result tests software behavior only. It must not be reported as
external validation, evidence about a venue, or support for energy-saving claims. Running
the rehearsal does not change the frozen model, data-quality rules, comparators or success
criterion.

The rehearsal writes:

- a supplier-style interval export in Wh;
- a matching daily weather file;
- the prepared daily evaluation CSV;
- synthetic provenance metadata;
- the complete frozen comparison report;
- a compact machine-readable summary; and
- a warning file explaining the evidence boundary.

When real data becomes available, use
[`VENUE_DATA_READINESS.md`](VENUE_DATA_READINESS.md) instead. Do not copy synthetic values
or synthetic provenance into a real confirmation package.
