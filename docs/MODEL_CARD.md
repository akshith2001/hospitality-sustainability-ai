# Model Card: Hospitality Sustainability AI

## Model details

**Version:** 0.1.0 research prototype  
**Developer:** Akshith Moharampudi  
**Model type:** Interpretable multivariable linear regression  
**Primary target:** Daily venue electricity consumption in kWh  
**Project status:** Educational prototype; not deployed

The model predicts daily electricity use from operational and contextual variables. A
residual-based component flags unusually high use, while separate decision-support code
compares possible interventions. Feature contributions provide a direct explanation of
each linear prediction.

## Intended use

The prototype is intended to:

- demonstrate a reproducible explainable-AI workflow for hospitality sustainability;
- support research into venue-level electricity prediction and anomaly investigation;
- help frame a future study using consented, quality-controlled real-world data; and
- provide decision support for trained human reviewers.

It is not intended to:

- prove that a venue, manager or employee has wasted energy;
- autonomously change equipment, penalise staff or enforce compliance;
- make real savings claims from the current synthetic evaluation; or
- replace engineering inspection, operational knowledge or human judgement.

## Data

The repository contains two distinct evidence streams. Synthetic experiments generated
with a fixed random seed use venue type, customer count, opening hours,
outside-temperature distance from 18 C, floor area, kitchen-equipment count and day of
week to predict daily `electricity_kwh`.

Artificial excess-use cases are injected for anomaly evaluation. Their labels are never
used as prediction inputs. Because the generator defines the relationships, strong model
performance is expected and does not demonstrate external validity.

The first real-building evaluation uses 5,755 derived daily observations from six
food-service buildings and two hotels selected from Building Data Genome 2. It includes
venue identity, floor area, outdoor temperature, calendar and seasonal terms, but it does
not include customer counts, opening hours, kitchen-equipment counts or intervention
outcomes. Daily totals below 1 kWh are excluded as zero/near-zero meter states for
buildings larger than 1,500 square metres. This post-diagnostic quality rule is disclosed
in the real-data result note.

The proposed real-data study uses pseudonymous venue identifiers, calibrated 30-minute
smart-meter readings and daily operational context. Its collection, verification,
exclusion and consent rules are described in
[REAL_WORLD_STUDY_PROTOCOL.md](REAL_WORLD_STUDY_PROTOCOL.md).

## Evaluation

The primary metric is mean absolute error (MAE), compared with a training-mean baseline.
The repository includes:

- a reproducible random 80/20 split;
- a chronological test on the newest 30 days;
- leave-one-venue-out evaluation reported for every venue;
- a locked two-venue real-data evaluation with venue identity removed;
- a stricter evaluation removing both venue identity and future-period observations;
- anomaly precision and recall against injected labels; and
- automated tests for modelling, data quality, governance and decision logic.

For the real-building evaluation, the model was trained on eligible observations through
2017-11-01 and tested on the newest 60 dates. The seasonal linear model achieved 523.42
kWh/day MAE versus 651.73 kWh/day for a per-venue historical-mean baseline, a 19.7%
improvement across 266 eligible test rows. It improved for four of five eligible venues
and worsened for one. Three additional source venues had no eligible test-period readings
and are reported as missing. These results measure prediction accuracy only.

In a separate completely unseen-venue experiment, `Fox_food_Francesco` and
`Mouse_lodging_Vicente` were locked before their scores were calculated. The model beat a
same-type training mean for both venues: MAE improved by 54.8% for the food-service venue
and 32.5% for the hotel. This tests cross-building transfer, not future-time forecasting,
because the remaining training venues include observations from the same date range.

The stricter combined evaluation holds out the same two venues and their newest 60
eligible dates. Training uses only other venues and only earlier dates. The model improved
MAE by 40.8% for `Fox_food_Francesco` and 50.3% for `Mouse_lodging_Vicente` against a
same-type, earlier-period training mean. The predefined requirement of improvement for
both venues was met. The hotel test period ends earlier because later near-zero readings
are excluded under the already documented quality rule.

Current synthetic and real-data numerical results are reported in the main
[README](../README.md), with the full real-data method in
[REAL_DATA_RESULTS.md](REAL_DATA_RESULTS.md).

## Explainability and uncertainty

Each linear feature contribution equals the input value multiplied by its learned
coefficient. Contributions sum to the prediction, making the calculation inspectable.
They describe model association rather than causal effect.

Prediction ranges use the robust spread of training residuals. The software reports low
confidence when data are insufficient or inputs fall outside represented ranges. These
ranges are illustrative model estimates, not calibrated real-world guarantees.

## Foreseeable risks

- **False alerts:** legitimate events, weather, equipment faults or missing variables may
  appear as abnormal consumption.
- **Unequal performance:** unusual or under-represented venues may receive poorer
  predictions.
- **Automation bias:** reviewers may give an AI recommendation more authority than the
  evidence supports.
- **Privacy leakage:** operational records could indirectly reveal sensitive business or
  staff information if identifiers and access are poorly controlled.
- **Misleading savings:** illustrative prices, emission factors and reduction rates may be
  mistaken for verified local values.
- **Concept drift:** seasonal, operational or equipment changes may reduce accuracy.

## Safeguards

- Alerts are framed as requests for investigation, not proof of waste.
- Recommendations require authorised human approval.
- Strong alternative interventions are shown alongside the highest-ranked option.
- Primary real-data evaluation would use verified readings only.
- Performance is reported overall and by venue to expose unequal outcomes.
- Material degradation pauses recommendations and triggers review.
- Anonymous staff feedback requires operations, sustainability and research review before
  any training use.
- Business names, full addresses and personal names are excluded from training files.

## Requirements before real-world use

Before a pilot or deployment, the project would require:

1. institutional ethics and data-protection approval;
2. venue permission and voluntary participant consent where applicable;
3. documented calibration and data-quality procedures;
4. prospective evaluation on unseen venues and time periods;
5. comparison with suitable non-AI baselines;
6. predefined performance, fairness and safety acceptance criteria;
7. current local evidence for tariffs, emission factors and intervention effects; and
8. named human owners for monitoring, approval, incident response and rollback.

## Limitations and maintenance

The present linear models may miss nonlinear relationships and interactions. Synthetic
data cannot reproduce the diversity, behaviour, seasonality or sensor failures of real
venues. The BDG2 evaluation is based on a small, third-party sample, lacks important
hospitality operational features and does not test intervention outcomes. The two-venue
transfer experiments are too small to establish broad generalisation, despite the combined
unseen-building and future-time holdout. The model card should be updated
whenever the data source, features, evaluation
design, decision rules or deployment status changes.
