# Unseen-venue and future-period evaluation

## Research question

Can a venue-independent linear model predict the newest 60 eligible dates for two
completely unseen hospitality buildings more accurately than a same-type historical-mean
baseline, without using observations from the future test period?

## Decisions fixed before evaluation

- Reuse the previously locked venues: `Fox_food_Francesco` and
  `Mouse_lodging_Vicente`.
- Test the newest 60 eligible dates for each venue.
- Remove the held-out venue completely from training.
- Remove all records on or after the held-out venue's test start date from training.
- Apply the existing 1 kWh near-zero meter-state rule unchanged.
- Use venue type, floor area, outdoor temperature, weekday and annual seasonality, but no
  venue identity.
- Compare against the mean kWh of same-type training venues using earlier dates only.
- Declare success only if the model beats the baseline for both venues separately.

## Method

The model is refitted independently for each held-out venue. Its training set contains
eligible records from other venues with dates strictly earlier than the held-out venue's
test start. The test set contains only the held-out venue's newest 60 eligible dates. Mean
absolute error (MAE) is the primary metric, where lower is better.

## Results

| Held-out venue | Training period ends | Future test period | Training rows | Test rows | Baseline MAE | Model MAE | Improvement |
|---|---|---|---:|---:|---:|---:|---:|
| Fox_food_Francesco | 2017-11-01 | 2017-11-02 to 2017-12-31 | 4,220 | 60 | 658.50 | 389.82 | 40.8% |
| Mouse_lodging_Vicente | 2017-08-24 | 2017-08-25 to 2017-10-23 | 3,910 | 60 | 1,019.06 | 506.20 | 50.3% |

The model beat the type-based earlier-period baseline for both venues, so the predefined
success criterion was met.

## Interpretation and limitations

This experiment is stronger than either the chronological or cross-building experiment
alone because it prevents both held-out-building and future-period leakage. It provides
evidence of useful transfer under the fixed design for these two buildings.

The hotel test period ends on 2017-10-23 rather than at the end of the dataset because
later near-zero readings were excluded by the quality rule fixed before this experiment.
The newest 60 dates therefore means the newest 60 eligible dates, not the final 60
calendar dates in the raw source.

- Only two buildings are tested.
- The hotel relies on limited same-type training diversity.
- Results do not establish causality, waste or intervention savings.
- Operational variables important to hospitality are unavailable in BDG2.
- Repeating the design across more buildings and independent datasets is necessary before
  making a broad generalisation claim.
