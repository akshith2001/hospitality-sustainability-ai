# Hospitality Sustainability AI

An educational, research-oriented project for building an explainable AI system that predicts resource consumption, detects unusual usage and recommends practical sustainability interventions for hospitality venues.

## Research question

Can explainable machine learning use operational data to identify abnormal resource consumption and recommend an environmentally effective, financially sensible and operationally practical intervention for an individual hospitality venue?

## Stage 1: understand and generate the data

The first model will predict daily electricity consumption in kilowatt-hours.

| Field | Role | Type | Meaning |
|---|---|---|---|
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

## Planned stages

1. Transparent non-AI baseline
2. Regression model and evaluation
3. Residual-based anomaly detection
4. Explainable feature contributions
5. Intervention ranking across emissions, cost and practicality
6. Uncertainty analysis and dashboard

