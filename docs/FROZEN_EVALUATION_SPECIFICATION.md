# Frozen future-evaluation specification

**Status:** frozen on 2026-08-16 after the BDG2 rolling-validation and final-period
results were observed.

## Purpose

This document fixes the next evaluation before new outcomes are examined. It prevents
the already-observed BDG2 test period from being reused for tuning and makes the future
success rule explicit.

## Frozen candidate

The primary candidate is the current leakage-safe lag-feature linear model. Its inputs
are fixed as:

- previous calendar day's eligible electricity total;
- mean of the seven most recent earlier eligible observations;
- eligible electricity total from seven calendar days earlier;
- outdoor-temperature distance from 18°C and its square;
- weekday indicators;
- annual sine and cosine terms; and
- venue indicators.

The model-fitting code, regularisation value, missing-lag fallback, date ordering and
data-quality rules must remain unchanged for the confirmatory evaluation. Any change
creates a new candidate and requires a new specification before outcomes are viewed.

## Comparator

The primary comparator is the previous-day baseline. It predicts each venue from the
eligible reading one calendar day earlier and uses the venue's training-period mean when
that lag is unavailable. The existing per-venue mean, seven-day rolling mean, same-weekday
baseline and seasonal linear model remain secondary comparators and must all be reported.

## New-data requirement

The confirmatory dataset must contain a genuinely unobserved period or an independently
sourced hospitality-building dataset. The current BDG2 period beginning 2017-11-02 is
ineligible because its outcomes have already informed the research narrative.

Before outcomes are opened:

1. identify the source, licence and venue inclusion rule;
2. apply the existing minimum 1 kWh daily-quality threshold unchanged;
3. reserve at least 60 unique newest dates for confirmation;
4. verify that every evaluated venue has earlier eligible training history; and
5. record missing venues and incomplete periods rather than silently dropping them.

## Prediction protocol

- Fit model coefficients only on records dated before the confirmation boundary.
- Predict every venue for a date before revealing any target from that date.
- After a date is scored, its eligible actual readings may enter history for later dates.
- Never use future targets in lag construction, fallback values, preprocessing or model
  selection.

## Metrics and success rule

The primary metric is pooled mean absolute error in kWh/day across all eligible
confirmation rows. Per-venue MAE and row counts are mandatory secondary results.

The candidate succeeds only if both conditions hold without rounding:

1. its pooled MAE is at least **5% lower** than the previous-day baseline; and
2. its MAE is lower than the previous-day baseline for at least half of the eligible
   confirmation venues.

Anything else is a failed confirmatory result. The per-venue mean and all secondary
comparators must still be published, including unfavorable outcomes.

## Governance

Passing this predictive test does not demonstrate energy savings, causal effects or
verified waste. It does not authorize automated operational decisions. Any deployment
still requires data-quality review, human approval, monitoring and a separate prospective
intervention study.
