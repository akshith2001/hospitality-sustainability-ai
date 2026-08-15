"""Sensitivity analysis for multi-criteria recommendation weights."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass

from .recommend import rank_interventions


@dataclass(frozen=True)
class WeightSensitivityResult:
    combinations: int
    winner_counts: tuple[tuple[str, int], ...]
    default_winner: str
    default_winner_share: float


def analyse_weight_sensitivity(
    predicted_daily_kwh: float,
    budget_gbp: float,
    step: float = 0.05,
) -> WeightSensitivityResult:
    """Enumerate all non-negative weight combinations that sum to one."""
    if not 0 < step <= 1:
        raise ValueError("step must be above zero and at most one")
    divisions_float = 1 / step
    divisions = round(divisions_float)
    if abs(divisions - divisions_float) > 1e-9:
        raise ValueError("step must divide one exactly")

    default = rank_interventions(predicted_daily_kwh, budget_gbp)
    if not default:
        raise ValueError("No intervention fits the selected budget")
    winners: Counter[str] = Counter()
    for emissions_units in range(divisions + 1):
        for financial_units in range(divisions - emissions_units + 1):
            practicality_units = divisions - emissions_units - financial_units
            ranked = rank_interventions(
                predicted_daily_kwh,
                budget_gbp,
                emissions_weight=emissions_units / divisions,
                financial_weight=financial_units / divisions,
                practicality_weight=practicality_units / divisions,
            )
            winners[ranked[0].name] += 1

    combinations = sum(winners.values())
    default_winner = default[0].name
    return WeightSensitivityResult(
        combinations=combinations,
        winner_counts=tuple(winners.most_common()),
        default_winner=default_winner,
        default_winner_share=winners[default_winner] / combinations,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse recommendation weight sensitivity")
    parser.add_argument("--predicted-daily-kwh", type=float, default=416.05)
    parser.add_argument("--budget-gbp", type=float, default=1_500.0)
    parser.add_argument("--step", type=float, default=0.05)
    args = parser.parse_args()
    result = analyse_weight_sensitivity(
        args.predicted_daily_kwh, args.budget_gbp, args.step
    )
    print(f"Weight combinations tested: {result.combinations}")
    for name, count in result.winner_counts:
        print(f"{name}: {count} wins ({count / result.combinations:.1%})")
    print(
        f"Default recommendation '{result.default_winner}' wins "
        f"{result.default_winner_share:.1%} of tested combinations."
    )


if __name__ == "__main__":
    main()

