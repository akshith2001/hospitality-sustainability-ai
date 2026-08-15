# Hospitality Sustainability AI

An educational, research-oriented project for building an explainable AI system that predicts resource consumption, detects unusual usage and recommends practical sustainability interventions for hospitality venues.

## Research question

Can explainable machine learning use operational data to identify abnormal resource consumption and recommend an environmentally effective, financially sensible and operationally practical intervention for an individual hospitality venue?

## Stage 1: understand and generate the data

The first model will predict daily electricity consumption in kilowatt-hours.

| Field | Role | Type | Meaning |
|---|---|---|---|
| `date` | identifier | ISO date | date of the daily observation |
| `day_of_week` | feature | categorical | weekday derived from the date |
| `venue_id` | identifier | pseudonymous category | random-style research identifier, excluded from model features |
| `venue_type` | feature | categorical | restaurant, hotel, bar or event venue |
| `customers` | feature | numerical count | customers served that day |
| `opening_hours` | feature | numerical continuous | hours open that day |
| `outside_temperature_c` | feature | numerical continuous | daily outside temperature |
| `floor_area_m2` | feature | numerical continuous | venue floor area |
| `kitchen_equipment_count` | feature | numerical count | major powered kitchen appliances |
| `electricity_kwh` | target | numerical continuous | actual daily electricity use |
| `is_injected_anomaly` | evaluation label | binary category | whether artificial excess use was added |

`electricity_kwh` is the target because it is the number the regression model will learn to predict. The anomaly label is used only to evaluate anomaly detection in this synthetic demonstration.

## Synthetic-data limitation

The generated data are not measurements from real businesses. They are created from a documented equation plus random variation. This makes the software reproducible and testable, but it cannot demonstrate real-world accuracy. Real deployment would require calibrated meters, suitable permissions, privacy safeguards and validation across independent venues.

## Generate the learning dataset

```bash
python -m hospitality_ai.synthetic_data --rows 1000 --seed 2026
```

The fixed seed ensures that another researcher can reproduce the same dataset.

## Establish the non-AI baseline

The dataset is shuffled reproducibly and divided into 80% training data and 20%
unseen test data. The baseline learns only the mean electricity consumption in the
training set and predicts that value for every test row:

```bash
python -m hospitality_ai.baseline --rows 1000 --seed 2026
```

Performance is measured using mean absolute error (MAE). A later machine-learning
model must beat this baseline on the same unseen test set to demonstrate useful
predictive information.

## Evaluation chart

Generate an actual-versus-predicted chart for the unseen test set:

```bash
python -m hospitality_ai.evaluation_chart
```

![Actual versus predicted electricity use](figures/actual_vs_predicted.svg)

Ordinary observations close to the dashed diagonal indicate accurate predictions.
Red crosses are artificial excess-use cases included only to test the workflow.

## Chronological validation

Random splitting is useful for an initial software experiment, but operational
deployment must test whether a model trained on the past can predict the future. The
chronological evaluation reserves the newest 30 daily observations as an untouched
test period:

```bash
python -m hospitality_ai.temporal_validation --rows 365 --test-days 30
```

The training period always ends before the test period begins, preventing future
readings from leaking into model training.

## Unseen-venue validation

To test whether the method generalises beyond venues represented during training,
one pseudonymous venue can be excluded completely and used only for testing:

```bash
python -m hospitality_ai.venue_validation --venue-id VENUE-001
```

The held-out venue ID never enters training and venue IDs are identifiers, not model
features. Real research should repeat this process across multiple venues rather than
relying on one favourable result.

## Proposed real-world data collection

A real study should collect automatic 30-minute smart-meter readings plus verified
daily totals for at least one full year. Venue names and full addresses should not
appear in model-training files. Each venue should use a random research ID, while any
re-identification key is stored separately with restricted access. Daily operational
context may include customers, opening hours, weather, special events and documented
equipment changes.

## Train the first regression model

The first learning model is multivariable linear regression implemented with the
Python standard library. It learns coefficients from the training set only and is
then evaluated on the untouched test set:

```bash
python -m hospitality_ai.linear_model --rows 1000 --seed 2026
```

Categorical venue type and day of the week are represented using one-hot indicator features. The model
also receives squared distance from 18 C so that both unusually cold and unusually
hot weather can increase predicted consumption. The date identifies the observation
but is not itself used as a numerical feature. The injected anomaly label is never used
as a prediction feature.

## Detect unexpected excess consumption

The anomaly stage calculates a residual for each day:

`residual = actual electricity - predicted electricity`

## Report uncertainty and low confidence

The software reports a central electricity prediction together with an empirical
range estimated from training residuals:

```bash
python -m hospitality_ai.uncertainty --rows 1000 --seed 2026
```

It warns that confidence is low when there are fewer than 100 training observations
or when a venue input falls outside the ranges represented in the training data. The
range is a transparent model-based estimate, not a guarantee or a calibrated claim
of real-world coverage.

## Anonymous, human-reviewed feedback

Staff can classify an alert as confirmed waste, equipment fault, special event,
incorrect data, normal operation or unknown. The feedback record contains a random
ID, alert ID, venue ID, timestamp, category, action and optional notes. It does not
contain an employee name, employee number, email address, IP address or device ID.

New feedback has `pending` status and is not eligible for model training. It requires
unanimous approval from an operations manager, a sustainability reviewer and a
research reviewer. A missing decision or any rejection keeps it out of training.
Managers should receive the operational information required to investigate an alert
but must not be given a way to identify the employee who submitted anonymous feedback.

A robust threshold is learned from the median and median absolute deviation (MAD) of
training residuals. A large positive residual creates an investigation alert:

```bash
python -m hospitality_ai.anomaly --rows 1000 --seed 2026
```

An alert is not proof of waste. It may reflect a special event, missing feature,
sensor problem or genuine operational change. The synthetic anomaly label is used
only after prediction to calculate precision and recall.

## Explain a prediction

The explanation command selects the largest positive test residual and reports the
predicted value, actual value, alert threshold and contribution of every feature:

```bash
python -m hospitality_ai.explain --rows 1000 --seed 2026
```

For linear regression, each contribution is exactly `input value x learned
coefficient`, and the contributions sum to the prediction. The explanation describes
association within this model, not causation in a real venue.

## Recommend a feasible intervention

The decision-support stage ranks interventions that fit a selected budget using fixed
weights for emissions benefit (40%), financial benefit (35%) and operational
practicality (25%):

```bash
python -m hospitality_ai.recommend --predicted-daily-kwh 416.05 --budget-gbp 1500
```

The highest-scoring feasible option is recommended, with its estimated electricity,
emissions, cost and payback effects. Current prices, reduction percentages, emission
factors and practicality ratings are illustrative; they must be replaced and validated
before real decisions are made.

## Test recommendation robustness

The default 40/35/25 weights are a judgement, not an objective truth. Weight
sensitivity enumerates alternative emissions, financial and practicality weights that
sum to one and reports how often each intervention wins:

```bash
python -m hospitality_ai.decision_sensitivity --step 0.05
```

A recommendation that wins under many plausible combinations is more robust. A low
winner share means the decision is strongly dependent on stakeholder priorities and
should be presented with alternatives.

## Planned stages

1. Transparent non-AI baseline
2. Regression model and evaluation
3. Residual-based anomaly detection
4. Explainable feature contributions
5. Intervention ranking across emissions, cost and practicality
6. Uncertainty analysis and dashboard
