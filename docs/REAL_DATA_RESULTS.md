# Real-data evaluation results

## Research question

Can a transparent seasonal linear model predict the newest 60 days of daily electricity
use more accurately than a per-venue historical-mean baseline for the eight
hospitality-related buildings selected from Building Data Genome 2?

## Method

- Source: BDG2 v1.0, DOI https://doi.org/10.5281/zenodo.3887306
- Records: 5,755 daily observations from six food-service buildings and two hotels
- Training: all eligible observations up to 2017-11-01
- Data-quality rule: daily totals below 1 kWh are excluded as zero/near-zero meter states
  for buildings larger than 1,500 square metres; the rule is applied before splitting
- Test: the newest 60 dates, beginning 2017-11-02
- Baseline: each venue's mean daily kWh calculated from training data only
- Time-series baselines: previous calendar day, mean of the seven most recent earlier
  observations, and the same weekday seven calendar days earlier
- Leakage control: predictions are made in date order. A test day's actual usage becomes
  available only after that whole date has been predicted, as in a daily rolling-origin
  backtest. Missing lags fall back to that venue's training-period mean.
- Model: ordinary least squares with venue identity, outdoor-temperature terms, weekday,
  annual seasonality and venue-specific annual seasonality
- Metric: mean absolute error (MAE), where lower is better

## Results

| Evaluation | Rows | MAE (kWh/day) |
|---|---:|---:|
| Per-venue historical-mean baseline | 266 | 651.73 |
| Previous-day baseline | 266 | 159.83 |
| Seven-day rolling-mean baseline | 266 | 271.92 |
| Same weekday one week earlier | 266 | 364.68 |
| Seasonal linear model | 266 | 523.42 |

Against the original per-venue mean, overall model MAE improved by **19.7%**. This retains
the project's existing evaluation rule and result. However, all three time-series
baselines were more accurate than the seasonal linear model; the previous-day baseline
was strongest at **159.83 kWh/day**. The model performed better than the original mean
baseline for four of five eligible test venues and worse for `Fox_food_Scott`.

Three source venues had no eligible test-period readings after the documented near-zero
meter-state rule: `Lamb_food_Sylvia`, `Lamb_lodging_Harley` and
`Mouse_lodging_Vicente`. `Eagle_food_Jennifer` had only 26 eligible test days rather than
60. These differences are reported because excluding poor-quality periods can introduce
selection bias.

The near-zero rule was introduced after the first diagnostic run exposed prolonged zero or
fixed tiny readings. It is therefore a post-diagnostic data-quality decision, not a
pre-registered choice. Future evaluations should retain this rule unchanged or justify any
revision before examining their test results.

![Real-data MAE for every held-out venue](../figures/bdg2_real_data_mae.svg)

## Interpretation

The added comparisons show that recent venue history is substantially more predictive in
this test period than the current weather, calendar and seasonal model. The original mean
comparison was too weak to establish that the model was operationally competitive. The missing
test-period venues are an important data-availability limitation, not successful model
results. Reporting them prevents the stronger aggregate score from hiding selection bias.

The experiment does not demonstrate causality, verified waste, intervention savings or
generalisation to unseen venues. Customer counts, opening hours, equipment counts and
intervention outcomes are unavailable in BDG2. A next experiment should test a model that
combines leakage-safe lag features with weather and calendar inputs, using the same locked
chronological boundary.
