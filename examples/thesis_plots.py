#!/usr/bin/env python3
"""
Reproducible demo figures built with the FigWorks figure registry.

This is a self-contained example of `figworks.FigureCollection`: register
every figure exactly once, share one style sheet and one output directory,
and regenerate the whole set (or a single figure) from a single command.

A builder returns either a Matplotlib figure or a composed FigWorks `Figure`;
the collection saves both to PDF (vector, for LaTeX), SVG (vector, for
editing), and PNG (raster, for slides), byte-identically from run to run,
without the builder knowing anything about file paths.  Every plot uses the
theme's typeface; the style sheet adds the cosmetics.

Running

    python examples/thesis_plots.py --all

regenerates every registered figure into `examples/out/thesis/`.

Usage
-----
    python examples/thesis_plots.py --list                  # show registered figures
    python examples/thesis_plots.py --all                   # regenerate everything
    python examples/thesis_plots.py demo_ldos_curves        # regenerate one figure
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from figworks import Figure, FigureCollection

HERE = Path(__file__).resolve().parent

# This example's collection: everything specific to this figure set lives here.
# The style sheet and the output directory are the two things the collection
# owns; the physics and the figure builders stay out of the machinery.
DEMO = FigureCollection(
    outdir=HERE / "out" / "thesis",
    theme="paper",
    style_file=HERE / "thesis_styles.mplstyle",
)
figure = DEMO.figure


def _demo_lorentzian(energy: np.ndarray, eps: float, width: float) -> np.ndarray:
    return width / np.pi / ((energy - eps) ** 2 + width**2)


@figure("demo_ldos_curves")
def demo_ldos_curves():
    """A two-state level model resolved as an energy-resolved density.

    Two lorentzians around `+/- eps` with a shared width: the kind of
    subgap-pole result a self-consistent calculation would produce.  Draws
    nothing but the curves and a legend; the caption belongs in the document
    that includes the figure.
    """
    energy = np.linspace(-2.0, 2.0, 2001)
    eps, width = 0.6, 0.08

    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    ax.plot(
        energy,
        _demo_lorentzian(energy, -eps, width),
        label=r"level $-\varepsilon$",
    )
    ax.plot(
        energy,
        _demo_lorentzian(energy, eps, width),
        label=r"level $+\varepsilon$",
    )
    ax.set_xlabel(r"energy $E$")
    ax.set_ylabel(r"density $\rho(E)$")
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(bottom=0.0)
    ax.legend()
    fig.tight_layout()
    return fig


@figure("demo_two_panel_figure")
def demo_two_panel_figure() -> Figure:
    """A composed two-panel figure, saved as a vector figure like any plot.

    The left panel is a Matplotlib plot made to the panel's size and placed by
    its axes frame; the right panel holds native FigWorks elements (a label,
    text, and an arrow).  The builder returns the FigWorks `Figure` itself.
    """
    canvas = Figure(width="140mm", height="70mm", theme="paper")
    left = canvas.panel("left", x="14mm", y="8mm", w="50mm", h="48mm")
    right = canvas.panel("right", x="80mm", y="8mm", w="55mm", h="48mm")

    x = np.linspace(0, 2 * np.pi, 200)
    curve, ax = left.subplots()
    ax.plot(x, np.sin(x), gid="sine-line")
    ax.set_xlabel(r"$\theta$")
    left.add(curve, id="sine", fit="axes")

    canvas.label("a", anchor=left.nw)
    canvas.label("b", anchor=right.nw)
    canvas.text("native text", x="88mm", y="32mm", id="caption")
    canvas.arrow(id="callout", start=("66mm", "31mm"), end=("86mm", "31mm"))
    return canvas


@figure("demo_stacked_layout")
def demo_stacked_layout():
    """An approximate and a full treatment compared in one axes.

    Demonstrates redrawing the model's band edges as dotted verticals so the
    subgap window is easy to read, the pattern used to contrast an
    approximation and a full self-consistent result.
    """
    energy = np.linspace(-2.0, 2.0, 2001)
    width = 0.06

    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    ax.plot(
        energy,
        _demo_lorentzian(energy, -0.5, width),
        label="approximation",
        linestyle="--",
    )
    ax.plot(
        energy,
        _demo_lorentzian(energy, -0.5, 2 * width),
        label="full treatment",
    )
    for edge in (-1.0, 1.0):
        ax.axvline(edge, color="0.5", linewidth=0.8, linestyle=":")
    ax.set_xlabel(r"energy $E/\Delta$")
    ax.set_ylabel(r"density $\rho(E)$")
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(bottom=0.0)
    ax.legend()
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    DEMO.main()
