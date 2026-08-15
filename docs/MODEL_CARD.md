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

All current training and evaluation data are synthetic and generated with a fixed random
seed. Features represent venue type, customer count, opening hours, outside-temperature
distance from 18 C, floor area, kitchen-equipment count and day of week. The outcome is
daily `electricity_kwh`.

Artificial excess-use cases are injected for anomaly evaluation. Their labels are never
used as prediction inputs. Because the generator defines the relationships, strong model
performance is expected and does not demonstrate external validity.

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
- anomaly precision and recall against injected labels; and
- automated tests for modelling, data quality, governance and decision logic.

Current numerical results are reported in the main [README](../README.md). They apply only
to the included synthetic experiments.

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

The present linear model may miss nonlinear relationships and interactions. Synthetic
data cannot reproduce the diversity, behaviour, seasonality or sensor failures of real
venues. The model card should be updated whenever the data source, features, evaluation
design, decision rules or deployment status changes.
