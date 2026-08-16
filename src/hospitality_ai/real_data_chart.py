"""Create an accessible SVG of the real-data evaluation for every venue."""

from __future__ import annotations

import argparse
from pathlib import Path

from .real_data_evaluation import evaluate_real_data, load_real_daily_records


def write_real_data_chart(data_path: Path, output_path: Path, test_days: int = 60) -> None:
    result = evaluate_real_data(load_real_daily_records(data_path), test_days)
    venues = result.venue_results
    maximum = max(
        value
        for venue in venues
        for value in (venue.baseline_mae_kwh, venue.model_mae_kwh)
    )
    width, height = 1180, 650
    left, right, top, bottom = 90, 35, 105, 150
    plot_width = width - left - right
    plot_height = height - top - bottom
    axis_max = maximum * 1.12

    def y(value: float) -> float:
        return top + plot_height - value / axis_max * plot_height

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Real-data MAE for every eligible held-out hospitality-related building</title>',
        '<desc id="desc">Grouped bars compare a per-venue historical-mean baseline with '
        'a seasonal linear model on the newest 60 days of real BDG2 electricity data.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="590" y="32" text-anchor="middle" font-family="Arial" font-size="22" '
        'font-weight="bold" fill="#172033">Real BDG2 chronological evaluation</text>',
        f'<text x="590" y="57" text-anchor="middle" font-family="Arial" font-size="13" '
        f'fill="#536078">Newest {test_days} days; lower MAE is better; all eligible venues shown</text>',
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" '
        'fill="#f8fafc" stroke="#aab4c3"/>',
    ]
    for index in range(6):
        value = index * axis_max / 5
        py = y(value)
        elements.extend(
            [
                f'<line x1="{left}" y1="{py:.1f}" x2="{left + plot_width}" y2="{py:.1f}" '
                'stroke="#dfe4ea"/>',
                f'<text x="{left - 10}" y="{py + 4:.1f}" text-anchor="end" '
                f'font-family="Arial" font-size="11" fill="#48566a">{value:.0f}</text>',
            ]
        )
    group_width = plot_width / len(venues)
    bar_width = 42
    for index, venue in enumerate(venues):
        centre = left + group_width * (index + 0.5)
        for x_pos, value, colour in (
            (centre - bar_width - 3, venue.baseline_mae_kwh, "#7b8794"),
            (centre + 3, venue.model_mae_kwh, "#2672b8"),
        ):
            top_y = y(value)
            elements.append(
                f'<rect x="{x_pos:.1f}" y="{top_y:.1f}" width="{bar_width}" '
                f'height="{top + plot_height - top_y:.1f}" fill="{colour}"/>'
            )
        short_name = venue.venue_id.split("_", 1)[-1]
        elements.append(
            f'<text x="{centre:.1f}" y="{top + plot_height + 18}" text-anchor="end" '
            f'transform="rotate(-42 {centre:.1f} {top + plot_height + 18})" '
            f'font-family="Arial" font-size="11" fill="#172033">{short_name}</text>'
        )
    elements.extend(
        [
            '<rect x="385" y="76" width="15" height="15" fill="#7b8794"/>',
            '<text x="408" y="89" font-family="Arial" font-size="13" fill="#172033">Historical mean</text>',
            '<rect x="545" y="76" width="15" height="15" fill="#2672b8"/>',
            '<text x="568" y="89" font-family="Arial" font-size="13" fill="#172033">Seasonal linear model</text>',
            f'<text x="805" y="89" font-family="Arial" font-size="13" font-weight="bold" '
            f'fill="#172033">Overall improvement: {result.improvement_pct:.1f}%</text>',
            f'<text x="24" y="{top + plot_height / 2}" text-anchor="middle" '
            f'transform="rotate(-90 24 {top + plot_height / 2})" font-family="Arial" '
            'font-size="14" fill="#172033">MAE (kWh/day)</text>',
            '<text x="590" y="625" text-anchor="middle" font-family="Arial" font-size="11" '
            'fill="#536078">Source: BDG2 v1.0. Three venues lacked eligible test-period readings.</text>',
            '</svg>',
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(elements), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/processed/bdg2_hospitality_daily.csv"))
    parser.add_argument("--output", type=Path, default=Path("figures/bdg2_real_data_mae.svg"))
    parser.add_argument("--test-days", type=int, default=60)
    args = parser.parse_args()
    write_real_data_chart(args.data, args.output, args.test_days)
    print(f"Chart written to {args.output}")


if __name__ == "__main__":
    main()
