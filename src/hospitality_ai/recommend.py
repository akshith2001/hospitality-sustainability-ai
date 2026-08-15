"""Transparent multi-criteria sustainability intervention recommender."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Intervention:
    name: str
    electricity_reduction_pct: float
    implementation_cost_gbp: float
    practicality_score: float
    rationale: str


@dataclass(frozen=True)
class ScoredIntervention:
    name: str
    annual_kwh_saved: float
    annual_emissions_saved_kg_co2e: float
    annual_cost_saved_gbp: float
    implementation_cost_gbp: float
    payback_years: float
    emissions_score: float
    financial_score: float
    practicality_score: float
    overall_score: float
    rationale: str


DEFAULT_INTERVENTIONS = (
    Intervention(
        "Refrigeration maintenance and control review",
        electricity_reduction_pct=8.0,
        implementation_cost_gbp=900.0,
        practicality_score=82.0,
        rationale="Inspect seals, temperatures, condenser condition and control schedules.",
    ),
    Intervention(
        "Kitchen equipment shutdown controls",
        electricity_reduction_pct=6.0,
        implementation_cost_gbp=450.0,
        practicality_score=88.0,
        rationale="Reduce avoidable standby and out-of-service electricity consumption.",
    ),
    Intervention(
        "LED lighting and occupancy controls",
        electricity_reduction_pct=4.0,
        implementation_cost_gbp=1_200.0,
        practicality_score=92.0,
        rationale="Reduce lighting demand with limited disruption to service.",
    ),
    Intervention(
        "HVAC maintenance and set-point review",
        electricity_reduction_pct=10.0,
        implementation_cost_gbp=1_800.0,
        practicality_score=70.0,
        rationale="Review schedules, filters, controls and temperature set points.",
    ),
)


def _benefit_score(values: list[float]) -> list[float]:
    """Scale non-negative benefits relative to the best candidate, from 0 to 100."""
    maximum = max(values, default=0.0)
    return [100.0 * value / maximum if maximum else 0.0 for value in values]


def rank_interventions(
    predicted_daily_kwh: float,
    budget_gbp: float,
    operating_days_per_year: int = 300,
    electricity_price_gbp_per_kwh: float = 0.25,
    electricity_factor_kg_co2e_per_kwh: float = 0.20,
    emissions_weight: float = 0.40,
    financial_weight: float = 0.35,
    practicality_weight: float = 0.25,
    interventions: tuple[Intervention, ...] = DEFAULT_INTERVENTIONS,
) -> list[ScoredIntervention]:
    """Rank feasible interventions under transparent illustrative assumptions."""
    if predicted_daily_kwh < 0 or budget_gbp < 0 or operating_days_per_year <= 0:
        raise ValueError("Consumption and budget cannot be negative; days must be positive")
    weights = (emissions_weight, financial_weight, practicality_weight)
    if any(weight < 0 for weight in weights) or abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError("Non-negative decision weights must sum to 1")
    feasible = [item for item in interventions if item.implementation_cost_gbp <= budget_gbp]
    if not feasible:
        return []

    annual_use = predicted_daily_kwh * operating_days_per_year
    kwh_savings = [annual_use * item.electricity_reduction_pct / 100 for item in feasible]
    annual_cost_savings = [value * electricity_price_gbp_per_kwh for value in kwh_savings]
    # Financial benefit is annual saving divided by upfront cost. A higher value
    # indicates faster recovery of the investment.
    financial_benefits = [
        saving / item.implementation_cost_gbp if item.implementation_cost_gbp else saving
        for saving, item in zip(annual_cost_savings, feasible)
    ]
    emissions_scores = _benefit_score(kwh_savings)
    financial_scores = _benefit_score(financial_benefits)

    ranked = []
    for item, saved_kwh, saved_cost, emissions_score, financial_score in zip(
        feasible,
        kwh_savings,
        annual_cost_savings,
        emissions_scores,
        financial_scores,
    ):
        payback = item.implementation_cost_gbp / saved_cost if saved_cost else float("inf")
        overall = (
            emissions_score * emissions_weight
            + financial_score * financial_weight
            + item.practicality_score * practicality_weight
        )
        ranked.append(
            ScoredIntervention(
                name=item.name,
                annual_kwh_saved=saved_kwh,
                annual_emissions_saved_kg_co2e=saved_kwh * electricity_factor_kg_co2e_per_kwh,
                annual_cost_saved_gbp=saved_cost,
                implementation_cost_gbp=item.implementation_cost_gbp,
                payback_years=payback,
                emissions_score=emissions_score,
                financial_score=financial_score,
                practicality_score=item.practicality_score,
                overall_score=overall,
                rationale=item.rationale,
            )
        )
    return sorted(ranked, key=lambda result: result.overall_score, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank electricity interventions")
    parser.add_argument("--predicted-daily-kwh", type=float, default=416.05)
    parser.add_argument("--budget-gbp", type=float, default=1_500.0)
    args = parser.parse_args()
    ranked = rank_interventions(args.predicted_daily_kwh, args.budget_gbp)
    if not ranked:
        print("No intervention fits the selected budget.")
        return
    print("Explainable intervention ranking")
    for position, item in enumerate(ranked, start=1):
        print(
            f"{position}. {item.name}: score {item.overall_score:.1f}; "
            f"saving {item.annual_kwh_saved:,.0f} kWh/year; "
            f"payback {item.payback_years:.2f} years"
        )
    best = ranked[0]
    print(f"Recommended: {best.name}")
    print(best.rationale)
    print("All prices, savings rates and emission factors are illustrative assumptions.")


if __name__ == "__main__":
    main()

