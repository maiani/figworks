"""Portable FigWorks starter using an illustrative model, not measured data.

The model is a decaying amplitude exp(-rate*time) and its normalized spectral
power rate**2/(detuning**2 + rate**2), in dimensionless coordinates.
Replace it with the research project's inputs and definitions.

Run: python figure.py --outdir figures/demo
Style/layout: python figure.py --theme style.md --width 183mm --height 80mm
Needs FigWorks 0.10+, Matplotlib, NumPy, Cairo, and the selected system fonts.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from figworks import Figure, load_theme


def build_figure(
    style: str = "paper",
    *,
    width: str = "178mm",
    height: str = "75mm",
    margins: tuple[str, str, str, str] = ("12mm", "5mm", "16mm", "18mm"),
    gap: str = "24mm",
) -> tuple[Figure, list[tuple[str, float, float, float]]]:
    """Return the composed demo and the exact plotted points for each panel."""
    theme = load_theme(style)
    figure = Figure(width, height, theme=theme, background="white")
    panels = figure.grid([["decay", "spectrum"]], margins=margins, gap=gap)
    rates = (0.5, 1.0)
    source_data: list[tuple[str, float, float, float]] = []

    with plt.rc_context(theme.rc()):
        for letter, (name, panel) in zip("ab", panels.items(), strict=True):
            plot, ax = panel.subplots()
            x = np.linspace(0, 5, 301) if name == "decay" else np.linspace(-3, 3, 301)
            try:
                for rate in rates:
                    y = np.exp(-rate * x) if name == "decay" else rate**2 / (x**2 + rate**2)
                    (curve,) = ax.plot(x, y, label=f"rate = {rate:g}")
                    curve.set_gid(f"{name}-rate-{rate:g}")
                    source_data.extend(
                        (name, rate, float(xi), float(yi)) for xi, yi in zip(x, y, strict=True)
                    )
                ax.set(xlim=(x[0], x[-1]), ylim=(0, 1.05))
                ax.set_xlabel("Time (normalized)" if name == "decay" else "Detuning (normalized)")
                ax.set_ylabel("Amplitude" if name == "decay" else "Normalized power")
                ax.legend(loc="upper right")
                panel.add(plot, id=f"{name}-plot", fit="axes")
            finally:
                plt.close(plot)
            figure.label(letter, panel.nw, id=f"{name}-letter")
    return figure, source_data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", default="paper", help="Built-in name or project style.md path")
    parser.add_argument("--width", default="178mm")
    parser.add_argument("--height", default="75mm")
    parser.add_argument("--margins", nargs=4, default=("12mm", "5mm", "16mm", "18mm"))
    parser.add_argument("--gap", default="24mm")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent / "figures")
    args = parser.parse_args()
    figure, source_data = build_figure(
        args.theme,
        width=args.width,
        height=args.height,
        margins=tuple(args.margins),
        gap=args.gap,
    )
    args.outdir.mkdir(parents=True, exist_ok=True)
    with (args.outdir / "source-data.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("panel", "rate", "x", "y"))
        writer.writerows(source_data)
    reports = {target: figure.check(target=target) for target in ("svg", "pdf", "png")}
    (args.outdir / "preflight.json").write_text(
        json.dumps({target: asdict(report) for target, report in reports.items()}, indent=2) + "\n",
        encoding="utf-8",
    )
    for target, report in reports.items():
        print(f"{target}: {report.summary()}")
        for issue in report.issues:
            print(f"  {issue.severity}: {issue.code}: {issue.message}")
        for limitation in report.unchecked:
            print(f"  Not checked: {limitation}")
        report.raise_for_errors()
    for extension in reports:
        figure.save(args.outdir / f"figure.{extension}", dpi=300)
    print(f"Wrote illustrative model, source-data.csv, and preflight.json to {args.outdir}")


if __name__ == "__main__":
    main()
