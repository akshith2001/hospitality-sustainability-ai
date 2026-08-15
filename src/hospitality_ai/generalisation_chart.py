"""Generate an accessible SVG comparing model and baseline generalisation error."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .linear_model import evaluate_linear_model
from .synthetic_data import generate_records
from .temporal_validation import evaluate_newest_days
from .venue_validation import evaluate_all_venues


@dataclass(frozen=True)
class EvaluationPair:
    label: str
    baseline_mae_kwh: float
    model_mae_kwh: float


def collect_evaluation_pairs(seed: int = 2026) -> tuple[EvaluationPair, ...]:
    """Run the three documented evaluations using reproducible synthetic data."""
    random_records = generate_records(1_000, seed)
    _, random_result = evaluate_linear_model(random_records, seed=seed)

    temporal_result = evaluate_newest_days(
        generate_records(365, seed), test_days=30
    )

    venue_result = evaluate_all_venues(generate_records(2_000, seed))
    mean_venue_baseline = sum(
        result.baseline_mae_kwh for result in venue_result.results
    ) / len(venue_result.results)

    return (
        EvaluationPair(
            "Random 80/20 split",
            random_result.baseline_mae_kwh,
            random_result.model_mae_kwh,
        ),
        EvaluationPair(
            "Newest 30 days",
            temporal_result.baseline_mae_kwh,
            temporal_result.model_mae_kwh,
        ),
        EvaluationPair(
            "Held-out venue mean",
            mean_venue_baseline,
            venue_result.mean_model_mae_kwh,
        ),
    )


def write_generalisation_chart(output_path: Path, seed: int = 2026) -> None:
    """Write a dependency-free grouped bar chart of MAE on unseen synthetic data."""
    pairs = collect_evaluation_pairs(seed)
    maximum = max(
        value
        for pair in pairs
        for value in (pair.baseline_mae_kwh, pair.model_mae_kwh)
    )
    axis_max = max(10.0, maximum * 1.15)

    width, height = 900, 610
    left, right, top, bottom = 100, 45, 110, 115
    plot_width = width - left - right
    plot_height = height - top - bottom

    def y(value: float) -> float:
        return top + plot_height - value / axis_max * plot_height

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Baseline and regression MAE across evaluation designs</title>',
        '<desc id="desc">For each unseen-data evaluation, the blue regression-model bar '
        'is lower than the grey mean-baseline bar. All results use synthetic data.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="450" y="34" text-anchor="middle" font-family="Arial" font-size="22" '
        'font-weight="bold" fill="#172033">Generalisation error across evaluation designs</text>',
        '<text x="450" y="58" text-anchor="middle" font-family="Arial" font-size="13" '
        'fill="#536078">Lower MAE is better; reproducible synthetic learning data</text>',
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" '
        'fill="#f8fafc" stroke="#aab4c3"/>',
    ]

    tick_count = 6
    for index in range(tick_count):
        value = index * axis_max / (tick_count - 1)
        py = y(value)
        elements.extend(
            [
                f'<line x1="{left}" y1="{py:.1f}" x2="{left + plot_width}" '
                f'y2="{py:.1f}" stroke="#dfe4ea"/>',
                f'<text x="{left - 12}" y="{py + 4:.1f}" text-anchor="end" '
                f'font-family="Arial" font-size="12" fill="#48566a">{value:.0f}</text>',
            ]
        )

    group_width = plot_width / len(pairs)
    bar_width = 62
    for index, pair in enumerate(pairs):
        centre = left + group_width * (index + 0.5)
        baseline_x = centre - bar_width - 5
        model_x = centre + 5
        for x_pos, value, colour in (
            (baseline_x, pair.baseline_mae_kwh, "#7b8794"),
            (model_x, pair.model_mae_kwh, "#2672b8"),
        ):
            top_y = y(value)
            elements.extend(
                [
                    f'<rect x="{x_pos:.1f}" y="{top_y:.1f}" width="{bar_width}" '
                    f'height="{top + plot_height - top_y:.1f}" fill="{colour}"/>',
                    f'<text x="{x_pos + bar_width / 2:.1f}" y="{top_y - 8:.1f}" '
                    f'text-anchor="middle" font-family="Arial" font-size="12" '
                    f'font-weight="bold" fill="#172033">{value:.1f}</text>',
                ]
            )
        elements.append(
            f'<text x="{centre:.1f}" y="{top + plot_height + 28}" text-anchor="middle" '
            f'font-family="Arial" font-size="13" fill="#172033">{pair.label}</text>'
        )

    elements.extend(
        [
            f'<text x="24" y="{top + plot_height / 2}" text-anchor="middle" '
            f'transform="rotate(-90 24 {top + plot_height / 2})" '
            'font-family="Arial" font-size="15" fill="#172033">MAE (kWh/day)</text>',
            '<rect x="305" y="80" width="16" height="16" fill="#7b8794"/>',
            '<text x="330" y="93" font-family="Arial" font-size="13" '
            'fill="#172033">Mean baseline</text>',
            '<rect x="470" y="80" width="16" height="16" fill="#2672b8"/>',
            '<text x="495" y="93" font-family="Arial" font-size="13" '
            'fill="#172033">Linear regression</text>',
            '<text x="450" y="574" text-anchor="middle" font-family="Arial" '
            'font-size="12" fill="#536078">Results demonstrate the pipeline, not real-world accuracy.</text>',
            '</svg>',
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(elements), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the generalisation MAE chart")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output", type=Path, default=Path("figures/generalisation_mae.svg")
    )
    args = parser.parse_args()
    write_generalisation_chart(args.output, args.seed)
    print(f"Chart written to {args.output}")


if __name__ == "__main__":
    main()
