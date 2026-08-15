# Hospitality Sustainability AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-80%20passing-2ea44f)](tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Data: Synthetic](https://img.shields.io/badge/data-synthetic-orange)](#synthetic-learning-data)

An educational research prototype for predicting hospitality electricity consumption,
detecting unusual excess use and ranking practical sustainability interventions. The
project emphasises explainability, honest evaluation, data quality, privacy and human
oversight.

> **Important:** all current performance results use transparent synthetic data. They
> demonstrate the software and research method, not proven accuracy or savings in real
> hospitality venues.

![Actual versus predicted electricity use](figures/actual_vs_predicted.svg)

![Baseline and model MAE across evaluation designs](figures/generalisation_mae.svg)

## Two-minute project tour

1. Read the [research question](#research-question) and the synthetic-data warning above.
2. Review the [current results](#current-results) and evaluation figure.
3. Inspect the [model card](docs/MODEL_CARD.md) for intended use, risks and safeguards.
4. Read the [real-world study protocol](docs/REAL_WORLD_STUDY_PROTOCOL.md) to see how the
   prototype could be evaluated with genuine venue data.
5. Run the test suite and experiments using the [quick-start commands](#quick-start).

The central contribution is not a claim that synthetic results will transfer directly to
real venues. It is a transparent, testable research pipeline connecting prediction,
explanation, anomaly investigation, intervention comparison and human approval.

## Research question

Can explainable machine learning use hospitality operational data to identify abnormal
resource consumption and recommend an environmentally effective, financially sensible
and operationally practical intervention for an individual venue?

## Current results

| Evaluation | Baseline MAE | Model MAE | Improvement |
|---|---:|---:|---:|
| Reproducible random 80/20 split | 77.27 kWh | 21.73 kWh | 71.9% |
| Newest 30-day chronological test | 105.93 kWh | 30.89 kWh | 70.8% |
| Mean across 20 held-out venues | 76.39 kWh | 21.80 kWh | 71.4% mean |

The held-out venue analysis reports all 20 venues rather than selecting the best result.
Current anomaly evaluation achieved 81.8% precision and 100% recall on deliberately
injected synthetic excess-use cases. These figures are not real-world claims.

## What the project includes

- Reproducible synthetic hospitality data with documented assumptions
- A mean-prediction baseline and dependency-free multivariable linear regression
- Random, chronological and leave-one-venue-out evaluation
- Residual-based anomaly alerts with precision and recall
- Exact feature-contribution explanations
- Empirical prediction ranges and low-confidence warnings
- Intervention ranking across emissions, finances and operational practicality
- Weight-sensitivity analysis that presents strong alternatives
- Anonymous staff feedback requiring multidisciplinary review
- Human approval gates, degradation monitoring and recommendation pausing
- Validated 30-minute smart-meter and daily operational-context formats
- Daily coverage, reconciliation, joining and exclusion reporting
- Venue-level data-quality reporting to expose selection bias

## Quick start

Requires Python 3.10 or newer. The project uses only the Python standard library.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Generate data and run the core evaluations:

```bash
python -m hospitality_ai.synthetic_data --rows 1000 --seed 2026
python -m hospitality_ai.baseline --rows 1000 --seed 2026
python -m hospitality_ai.linear_model --rows 1000 --seed 2026
python -m hospitality_ai.temporal_validation --rows 365 --test-days 30
python -m hospitality_ai.venue_validation --rows 2000 --all-venues
python -m hospitality_ai.anomaly --rows 1000 --seed 2026
python -m hospitality_ai.uncertainty --rows 1000 --seed 2026
python -m hospitality_ai.evaluation_chart
python -m hospitality_ai.generalisation_chart
```

Explain an alert and compare feasible interventions:

```bash
python -m hospitality_ai.explain --rows 1000 --seed 2026
python -m hospitality_ai.recommend --predicted-daily-kwh 416.05 --budget-gbp 1500
python -m hospitality_ai.decision_sensitivity --step 0.05
```

## Synthetic learning data

The daily regression target is `electricity_kwh`. Model features include venue type,
customers, opening hours, temperature distance from 18 C, floor area, kitchen-equipment
count and day of week. `venue_id` is only a pseudonymous identifier. The injected anomaly
label is used only after prediction for evaluation and never as an input feature.

Synthetic electricity is generated from a visible equation plus random variation and
occasional artificial excess use. A fixed seed makes experiments reproducible. Because
the generator defines the relationships, strong results are expected and cannot establish
external validity.

## Evaluation design

- **Baseline:** training-set mean predicted for every test record.
- **Primary error metric:** mean absolute error (MAE); lower is better.
- **Random split:** initial reproducible 80/20 software experiment.
- **Chronological split:** train on the past and reserve the newest month.
- **Venue validation:** exclude each venue completely, report every result, and summarise
  mean, best and worst performance.
- **Anomaly evaluation:** calculate precision and recall against injected labels.

An alert is evidence for investigation, not proof of waste. High consumption can reflect
a special event, missing feature, sensor problem or genuine operational change.

## Explainability, uncertainty and recommendations

For linear regression, every explanation is `input value x learned coefficient`, and the
contributions sum exactly to the prediction. This describes model association, not
real-world causation.

Prediction ranges use the robust spread of training residuals. Low confidence is reported
for insufficient training data or inputs outside represented ranges. The range is a
model-based estimate, not a guarantee or a calibrated real-world coverage claim.

Interventions are ranked using editable weights for emissions, financial benefit and
practicality. Prices, reduction rates, emissions factors and practicality values are
illustrative. Weight sensitivity reports how often each option wins so the leading result
is presented with alternatives rather than as an objective truth.

## Proposed real-world data workflow

The detailed design is in the [real-world study protocol](docs/REAL_WORLD_STUDY_PROTOCOL.md).
It proposes one year of calibrated 30-minute smart-meter readings, verified daily totals,
pseudonymous venue IDs, separate venue permission and voluntary staff consent.

Data templates:

- [30-minute smart-meter readings](data/templates/smart_meter_readings.csv)
- [Daily operational context](data/templates/daily_operational_context.csv)

Meter quality is labelled `verified`, `estimated`, `missing` or `fault`. Primary evaluation
uses only verified readings; estimated values may appear in a separately labelled
sensitivity analysis. A UTC day expects 48 half-hour intervals. Partial days are retained
as incomplete with their coverage percentage and are never described as full daily totals.

Complete interval sums are compared with independently verified daily totals using an
illustrative 1% rounding tolerance. Mismatches are investigated, never silently corrected.
Meter and operational records join only on `venue_id` and `utc_date`; unmatched records and
all exclusion reasons are reported overall and by venue.

## Privacy and governance

- No employee, customer, event-client or wedding-couple names are required.
- Business names and full addresses stay outside model-training files.
- Anonymous feedback cannot enter training without approval from operations,
  sustainability and research reviewers.
- Candidate models must improve overall MAE without worsening the poorest venue result.
- Deployment requires authorised human approval and retains the previous model for rollback.
- Material performance degradation pauses recommendations and triggers human review.
- Verified meter readings and AI recommendation status are controlled separately.
- Important state changes require an append-only audit trail and approved retention schedule.

The protocol must receive institutional ethics and data-protection approval before any
real participants are recruited or monitoring equipment is installed.

For a structured account of intended use, evaluation boundaries, foreseeable risks and
release criteria, see the [model card](docs/MODEL_CARD.md).

## Repository structure

```text
data/templates/       Example real-data formats
docs/                 Model card and proposed study protocol
figures/              Reproducible evaluation chart
src/hospitality_ai/   Modelling, validation and governance modules
tests/                Automated unit tests
```

## Limitations

- No real venue data have been collected or analysed.
- The linear model is intentionally interpretable and may not capture complex real patterns.
- Synthetic observations do not reproduce every venue, behaviour, season or sensor failure.
- Prediction ranges are empirical demonstrations, not formal calibrated intervals.
- Intervention assumptions require current, location-specific evidence before use.
- The prototype is decision support, not an autonomous enforcement or compliance system.

## Author and licence

Developed by **Akshith Moharampudi** as a learning and research portfolio project.
Released under the MIT License. See [LICENSE](LICENSE).
