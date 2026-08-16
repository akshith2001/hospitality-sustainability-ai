# Completely unseen-venue evaluation

## Research question

Can a venue-independent linear model predict daily electricity use for a food-service
building and a hotel that are completely absent from its training data more accurately
than a same-type historical-mean baseline?

## Decisions fixed before evaluation

- Test exactly two venues: one food-service building and one hotel.
- Select the venue with the most available daily records in each type; break ties
  alphabetically.
- Locked venues: `Fox_food_Francesco` and `Mouse_lodging_Vicente`.
- Exclude daily totals below 1 kWh using the existing near-zero meter-state rule.
- Do not include venue identity in the model features.
- Use venue type, floor area, outdoor temperature, weekday and annual seasonality.
- Compare against the mean daily kWh of same-type training venues.
- Declare success only if the model beats the baseline for both venues separately.

These choices were recorded before the two venue scores were calculated to reduce the
risk of selecting favourable outcomes after inspection.

## Method

Each locked venue is evaluated independently. All of its eligible records are assigned to
the test set, while eligible records from every other venue form the training set. The
ordinary least-squares model is refitted for each held-out venue. The primary metric is
mean absolute error (MAE), where lower is better.

This is a cross-building transfer test, not a future-time forecast. Training venues may
contain observations from the same dates as the held-out venue. The experiment therefore
asks whether relationships learned from other buildings transfer to a new building; it
does not test whether the model predicts a later period.

## Results

| Held-out venue | Type | Training rows | Test rows | Baseline MAE | Model MAE | Improvement |
|---|---|---:|---:|---:|---:|---:|
| Fox_food_Francesco | food service | 4,426 | 731 | 726.13 kWh/day | 327.85 kWh/day | 54.8% |
| Mouse_lodging_Vicente | hotel | 4,495 | 662 | 1,001.15 kWh/day | 676.23 kWh/day | 32.5% |

The model beat the same-type baseline for both locked venues, so the predefined success
criterion was met.

## Interpretation and limitations

The result is evidence that venue type, floor area, temperature, weekday and seasonal
features can transfer useful predictive information to these two unseen buildings. It is
not evidence that the model will generalise to all hospitality venues.

- Only two buildings were selected for this predefined experiment.
- The hotel is compared with training data from only one other hotel.
- BDG2 lacks customer counts, opening hours, kitchen-equipment counts and intervention
  outcomes.
- The evaluation does not reserve a future period, so it does not test temporal transfer.
- Prediction accuracy does not prove waste, causality or achievable energy savings.

The next stronger experiment should hold out both an entire venue and its future period,
and should compare against persistence, rolling-mean and seasonal-naive baselines.
