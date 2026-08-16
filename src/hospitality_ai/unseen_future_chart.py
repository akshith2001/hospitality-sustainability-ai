"""Create an accessible SVG for the unseen-venue future-period results."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

from .unseen_future_evaluation import evaluate_unseen_future
from .unseen_venue_evaluation import load_unseen_venue_records


def write_unseen_future_chart(data_path: Path, output_path: Path) -> None:
    evaluation = evaluate_unseen_future(load_unseen_venue_records(data_path))
    results = evaluation.results
    maximum = max(
        value
        for result in results
        for value in (result.baseline_mae_kwh, result.model_mae_kwh)
    )
    width, height = 1080, 620
    left, right, top, bottom = 100, 55, 125, 120
    plot_width = width - left - right
    plot_height = height - top - bottom
    axis_max = maximum * 1.12

    def y(value: float) -> float:
        return top + plot_height - value / axis_max * plot_height

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Unseen hospitality venues tested on future periods</title>',
        '<desc id="desc">Grouped bars compare a same-type earlier-period mean baseline '
        'with a venue-independent seasonal linear model. Lower mean absolute error is better.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="540" y="38" text-anchor="middle" font-family="Arial" font-size="24" '
        'font-weight="bold" fill="#17324d">Unseen venues + future periods</text>',
        '<text x="540" y="66" text-anchor="middle" font-family="Arial" font-size="14" '
        'fill="#5f6b73">Newest 60 eligible dates; no held-out-building or future-period leakage</text>',
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" '
        'fill="#f8fafc" stroke="#b7c2cc"/>',
    ]
    for index in range(6):
        value = index * axis_max / 5
        py = y(value)
        elements.extend([
            f'<line x1="{left}" y1="{py:.1f}" x2="{left + plot_width}" y2="{py:.1f}" stroke="#dfe4ea"/>',
            f'<text x="{left - 12}" y="{py + 4:.1f}" text-anchor="end" font-family="Arial" '
            f'font-size="12" fill="#48566a">{value:.0f}</text>',
        ])

    group_width = plot_width / len(results)
    bar_width = 105
    for index, result in enumerate(results):
        centre = left + group_width * (index + 0.5)
        for x_pos, value, colour in (
            (centre - bar_width - 8, result.baseline_mae_kwh, "#788896"),
            (centre + 8, result.model_mae_kwh, "#138a8a"),
        ):
            top_y = y(value)
            elements.extend([
                f'<rect x="{x_pos:.1f}" y="{top_y:.1f}" width="{bar_width}" '
                f'height="{top + plot_height - top_y:.1f}" fill="{colour}"/>',
                f'<text x="{x_pos + bar_width / 2:.1f}" y="{top_y - 8:.1f}" text-anchor="middle" '
                f'font-family="Arial" font-size="13" font-weight="bold" fill="#17324d">{value:.2f}</text>',
            ])
        label = "Food-service venue" if result.venue_type == "food_service" else "Hotel"
        elements.extend([
            f'<text x="{centre:.1f}" y="{top + plot_height + 28}" text-anchor="middle" '
            f'font-family="Arial" font-size="15" font-weight="bold" fill="#17324d">{escape(label)}</text>',
            f'<text x="{centre:.1f}" y="{top + plot_height + 51}" text-anchor="middle" '
            f'font-family="Arial" font-size="13" fill="#138a8a">{result.improvement_pct:.1f}% lower MAE</text>',
        ])
    elements.extend([
        '<rect x="355" y="88" width="17" height="17" fill="#788896"/>',
        '<text x="382" y="102" font-family="Arial" font-size="14" fill="#17324d">Same-type baseline</text>',
        '<rect x="565" y="88" width="17" height="17" fill="#138a8a"/>',
        '<text x="592" y="102" font-family="Arial" font-size="14" fill="#17324d">Linear model</text>',
        f'<text x="27" y="{top + plot_height / 2}" text-anchor="middle" '
        f'transform="rotate(-90 27 {top + plot_height / 2})" font-family="Arial" '
        'font-size="15" fill="#17324d">MAE (kWh/day; lower is better)</text>',
        '<text x="540" y="596" text-anchor="middle" font-family="Arial" font-size="12" '
        'fill="#5f6b73">Source: BDG2 v1.0. Results are predictive, not verified energy savings.</text>',
        '</svg>',
    ])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(elements), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/bdg2_hospitality_daily.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("figures/unseen_future_mae.svg"),
    )
    args = parser.parse_args()
    write_unseen_future_chart(args.data, args.output)
    print(f"Chart written to {args.output}")


if __name__ == "__main__":
    main()
