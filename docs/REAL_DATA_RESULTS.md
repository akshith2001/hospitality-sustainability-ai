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
- Model: ordinary least squares with venue identity, outdoor-temperature terms, weekday,
  annual seasonality and venue-specific annual seasonality
- Metric: mean absolute error (MAE), where lower is better

## Results

| Evaluation | Rows | MAE (kWh/day) |
|---|---:|---:|
| Per-venue historical-mean baseline | 266 | 651.73 |
| Seasonal linear model | 266 | 523.42 |

Overall MAE improved by **19.7%**. The model performed better than the baseline for four of
five eligible test venues and worse for `Fox_food_Scott`.

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

The result shows useful but uneven predictive value from weather, calendar and seasonal
features. It does not establish reliable performance for every building. The missing
test-period venues are an important data-availability limitation, not successful model
results. Reporting them prevents the stronger aggregate score from hiding selection bias.

The experiment does not demonstrate causality, verified waste, intervention savings or
generalisation to unseen venues. Customer counts, opening hours, equipment counts and
intervention outcomes are unavailable in BDG2. A next experiment should investigate
venue-specific failures and compare the model with stronger time-series baselines without
using future information.
