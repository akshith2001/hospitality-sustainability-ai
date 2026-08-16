# Train-only rolling-validation results

## Purpose

The newest 60-date test period has already been observed and must not be used for further
model tuning. This experiment compares the fixed candidate methods only on dates before
that boundary. It provides a safer basis for future model selection while preserving the
final test result as an honest historical record.

## Method

- Source and data-quality rules: unchanged from the BDG2 real-data evaluation
- Reserved final test period: all eligible dates from 2017-11-02 onward
- Development folds: four consecutive 30-date validation windows
- Training design: expanding history; every fold trains only on dates before its window
- Time-series design: each validation date is predicted before that date's actual values
  are added to history
- Metric: pooled mean absolute error (MAE) across every validation row; lower is better
- Candidates: per-venue mean, previous day, seven-day rolling mean, same weekday one week
  earlier, seasonal linear model and lag-feature linear model

The four validation periods are:

1. 2017-07-05 to 2017-08-03
2. 2017-08-04 to 2017-09-02
3. 2017-09-03 to 2017-10-02
4. 2017-10-03 to 2017-11-01

## Overall results

| Candidate | Pooled MAE (kWh/day) |
|---|---:|
| Lag-feature linear model | 111.87 |
| Previous day | 134.89 |
| Seven-day rolling mean | 161.01 |
| Same weekday one week earlier | 185.98 |
| Seasonal linear model | 342.43 |
| Per-venue training mean | 422.64 |

The lag-feature model has the lowest pooled validation MAE, improving on the previous-day
candidate by **17.1%** within these train-only folds.

## Per-venue result

| Venue | Validation rows | Lowest-MAE candidate | MAE (kWh/day) |
|---|---:|---|---:|
| Eagle_food_Jennifer | 95 | Previous day | 169.66 |
| Eagle_food_Kay | 119 | Lag-feature model | 211.26 |
| Fox_food_Francesco | 120 | Lag-feature model | 90.19 |
| Fox_food_Scott | 120 | Lag-feature model | 84.03 |
| Hog_food_Morgan | 120 | Lag-feature model | 68.61 |
| Lamb_food_Sylvia | 43 | Same weekday one week earlier | 18.92 |
| Lamb_lodging_Harley | 44 | Seven-day rolling mean | 12.86 |
| Mouse_lodging_Vicente | 111 | Lag-feature model | 67.33 |

The lag-feature model leads for five of eight venues, not all eight. Sparse validation
coverage for several venues remains an important limitation.

## Interpretation

Rolling validation favors the lag-feature model, while the already-observed final test
period favored the previous-day baseline by 0.09 kWh/day. This disagreement shows that
performance changes across time windows. It is evidence for cautious, repeated temporal
validation—not a reason to tune the model against the final test period.

A future candidate should be specified using only these development folds, then frozen
and evaluated on genuinely new data. The 2017-11-02 test boundary remains unchanged.
