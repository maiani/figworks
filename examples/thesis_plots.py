#!/usr/bin/env python3
"""
Reproducible demo figures built with the figforge figure registry.

This is a self-contained example of `figforge.FigureCollection`: register
every figure exactly once, share one style sheet and one output directory,
and regenerate the whole set (or a single figure) from a single command.

Each figure is a plain Matplotlib `Figure`, so the collection can save it to
PDF (vector, for LaTeX), SVG (vector, for editing), and PNG (raster, for
slides) without the builder knowing anything about file paths.  The figforge
`Figure` assembly shown below is exported through the same path.

Running

    python examples/thesis_plots.py --all

regenerates every registered figure into `examples/output_plots/`.  See the
module-level `FigureCollection` docstring for the full usage contract.

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

from figforge import Figure, FigureCollection

HERE = Path(__file__).resolve().parent

# This example's collection: everything specific to this figure set lives here.
# The style sheet and the output directory are the two things the collection
# owns; the physics and the figure builders stay out of the machinery.
DEMO = FigureCollection(
    name="thesis_plots.py",
    style_file=HERE / "thesis_styles.mplstyle",
    outdir=HERE / "output_plots",
)
figure = DEMO.figure


def _demo_lorentzian(energy: np.ndarray, eps: float, width: float) -> np.ndarray:
    return width / np.pi / ((energy - eps) ** 2 + width**2)


def _figforge_as_matplotlib(canvas: Figure) -> plt.Figure:
    """Wrap a figforge `Figure` so the collection can save it.

    A figforge `Figure` exports through its own `save`, which needs a file
    path with an extension; the collection hands Matplotlib `Figure`s to
    `pyplot.savefig`.  PNG through a temporary file is the natural bridge.
    """
    import tempfile

    import matplotlib.image as mpimg

    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "canvas.png"
        canvas.save(png, dpi=150)
        image = mpimg.imread(png)

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.imshow(image, aspect="auto", interpolation="nearest")
    ax.axis("off")
    fig.tight_layout()
    return fig


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
def demo_two_panel_figure():
    """A figforge-assembled two-panel figure: one inside a `Figure` canvas.

    The left panel is a Matplotlib plot embedded with `panel.add(...)`; the
    right panel holds native figforge elements (a label, text, and an arrow).
    Both are wrapped in a figforge `Figure`, exported to PNG, and handed back
    as a Matplotlib figure so the collection manages it like any other.
    """
    x = np.linspace(0, 2 * np.pi, 200)
    curve, ax = plt.subplots(figsize=(3, 2))
    ax.plot(x, np.sin(x), gid="sine-line")
    ax.set_title("panel a")

    canvas = Figure(width="140mm", height="70mm", theme="paper")
    left = canvas.panel("left", x="5mm", y="5mm", w="60mm", h="55mm")
    right = canvas.panel("right", x="75mm", y="5mm", w="60mm", h="55mm")
    left.add(curve, id="sine")
    canvas.label("a", anchor=left.nw)
    canvas.label("b", anchor=right.nw)
    canvas.text("native text", x="80mm", y="30mm", id="caption")
    canvas.arrow(id="callout", start=("52mm", "30mm"), end=("70mm", "30mm"))

    return _figforge_as_matplotlib(canvas)


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
