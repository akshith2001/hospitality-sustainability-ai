# Real-data evaluation results

## Research question

Can a transparent seasonal linear model predict the newest 60 days of daily electricity
use more accurately than a per-venue historical-mean baseline for the eight
hospitality-related buildings selected from Building Data Genome 2?

## Method

- Source: BDG2 v1.0, DOI https://doi.org/10.5281/zenodo.3887306
- Records: 5,755 daily observations from six food-service buildings and two hotels
- Training: all eligible observations up to 2017-11-01
- Test: the newest 60 dates, beginning 2017-11-02
- Baseline: each venue's mean daily kWh calculated from training data only
- Model: ordinary least squares with venue identity, outdoor-temperature terms, weekday,
  annual seasonality and venue-specific annual seasonality
- Metric: mean absolute error (MAE), where lower is better

## Results

| Evaluation | Rows | MAE (kWh/day) |
|---|---:|---:|
| Per-venue historical-mean baseline | 480 | 683.62 |
| Seasonal linear model | 480 | 651.68 |

Overall MAE improved by **4.7%**. The model performed better than the baseline for four of
eight venues and worse for four. The largest improvement appeared for `Hog_food_Morgan`;
the clearest deterioration appeared for `Lamb_food_Sylvia` and `Lamb_lodging_Harley`.

![Real-data MAE for every held-out venue](../figures/bdg2_real_data_mae.svg)

## Interpretation

The result is modest and uneven. It shows that weather, calendar and seasonal features add
some predictive value overall, but they do not reliably improve every building. This is a
more credible research outcome than presenting only aggregate or favourable results.

The experiment does not demonstrate causality, verified waste, intervention savings or
generalisation to unseen venues. Customer counts, opening hours, equipment counts and
intervention outcomes are unavailable in BDG2. A next experiment should investigate
venue-specific failures and compare the model with stronger time-series baselines without
using future information.
