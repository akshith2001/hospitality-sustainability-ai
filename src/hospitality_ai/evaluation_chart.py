"""Generate an accessible SVG comparing actual and predicted electricity use."""

from __future__ import annotations

import argparse
from pathlib import Path

from .baseline import train_test_split
from .linear_model import fit_linear_model
from .synthetic_data import generate_records


def write_actual_vs_predicted_chart(
    output_path: Path, rows: int = 1_000, seed: int = 2026
) -> None:
    records = generate_records(rows, seed)
    training, test = train_test_split(records, seed=seed)
    model = fit_linear_model(training)
    points = [
        (model.predict(record), record.electricity_kwh, record.is_injected_anomaly)
        for record in test
    ]
    values = [value for predicted, actual, _ in points for value in (predicted, actual)]
    lower = max(0.0, min(values) - 20.0)
    upper = max(values) + 20.0

    width, height = 900, 650
    left, right, top, bottom = 90, 40, 105, 85
    plot_width = width - left - right
    plot_height = height - top - bottom

    def x(value: float) -> float:
        return left + (value - lower) / (upper - lower) * plot_width

    def y(value: float) -> float:
        return top + plot_height - (value - lower) / (upper - lower) * plot_height

    ticks = 6
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Actual versus predicted daily electricity use</title>',
        '<desc id="desc">Test-set predictions close to the diagonal indicate accuracy. '
        'Red crosses identify days with artificially injected excess electricity use.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="450" y="34" text-anchor="middle" font-family="Arial" font-size="22" '
        'font-weight="bold" fill="#172033">Actual vs predicted electricity use</text>',
        '<text x="450" y="56" text-anchor="middle" font-family="Arial" font-size="13" '
        'fill="#536078">Unseen 20% test set; synthetic learning data</text>',
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" '
        'fill="#f8fafc" stroke="#aab4c3"/>',
    ]
    for index in range(ticks):
        value = lower + index * (upper - lower) / (ticks - 1)
        px, py = x(value), y(value)
        elements.extend(
            [
                f'<line x1="{px:.1f}" y1="{top}" x2="{px:.1f}" y2="{top + plot_height}" '
                'stroke="#dfe4ea"/>',
                f'<line x1="{left}" y1="{py:.1f}" x2="{left + plot_width}" y2="{py:.1f}" '
                'stroke="#dfe4ea"/>',
                f'<text x="{px:.1f}" y="{top + plot_height + 24}" text-anchor="middle" '
                f'font-family="Arial" font-size="12" fill="#48566a">{value:.0f}</text>',
                f'<text x="{left - 12}" y="{py + 4:.1f}" text-anchor="end" '
                f'font-family="Arial" font-size="12" fill="#48566a">{value:.0f}</text>',
            ]
        )
    elements.append(
        f'<line x1="{x(lower):.1f}" y1="{y(lower):.1f}" '
        f'x2="{x(upper):.1f}" y2="{y(upper):.1f}" stroke="#26364a" '
        'stroke-width="2" stroke-dasharray="7 5"/>'
    )
    for predicted, actual, anomaly in points:
        px, py = x(predicted), y(actual)
        if anomaly:
            elements.extend(
                [
                    f'<line x1="{px - 5:.1f}" y1="{py - 5:.1f}" x2="{px + 5:.1f}" '
                    f'y2="{py + 5:.1f}" stroke="#c7362f" stroke-width="2.5"/>',
                    f'<line x1="{px - 5:.1f}" y1="{py + 5:.1f}" x2="{px + 5:.1f}" '
                    f'y2="{py - 5:.1f}" stroke="#c7362f" stroke-width="2.5"/>',
                ]
            )
        else:
            elements.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="#2672b8" '
                'fill-opacity="0.58"/>'
            )
    elements.extend(
        [
            f'<text x="{left + plot_width / 2}" y="{height - 25}" text-anchor="middle" '
            'font-family="Arial" font-size="15" fill="#172033">Predicted electricity (kWh/day)</text>',
            f'<text x="22" y="{top + plot_height / 2}" text-anchor="middle" '
            f'transform="rotate(-90 22 {top + plot_height / 2})" font-family="Arial" font-size="15" '
            'fill="#172033">Actual electricity (kWh/day)</text>',
            '<line x1="190" y1="79" x2="218" y2="79" stroke="#26364a" '
            'stroke-width="2" stroke-dasharray="7 5"/>',
            '<text x="226" y="83" font-family="Arial" font-size="12" fill="#172033">Perfect prediction</text>',
            '<circle cx="410" cy="79" r="4" fill="#2672b8" fill-opacity="0.7"/>',
            '<text x="422" y="83" font-family="Arial" font-size="12" fill="#172033">Ordinary day</text>',
            '<line x1="556" y1="75" x2="564" y2="83" stroke="#c7362f" stroke-width="2"/>',
            '<line x1="556" y1="83" x2="564" y2="75" stroke="#c7362f" stroke-width="2"/>',
            '<text x="572" y="83" font-family="Arial" font-size="12" fill="#172033">Injected anomaly</text>',
            '</svg>',
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(elements), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the model evaluation chart")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output", type=Path, default=Path("figures/actual_vs_predicted.svg")
    )
    args = parser.parse_args()
    write_actual_vs_predicted_chart(args.output, args.rows, args.seed)
    print(f"Chart written to {args.output}")


if __name__ == "__main__":
    main()
