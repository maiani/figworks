"""Place a VecWire schematic beside a Matplotlib plot in one composed figure.

As with VecView, no adapter is involved: `vecwire.Circuit` exposes
`to_svg_document()`, which is the whole protocol `Panel.add` needs.

Usage:
    python examples/vecwire_panel.py     # requires VecWire from a checkout
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from vecwire import Circuit

from figworks import Figure
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

# Plots use the figure's typeface, words and math alike.
plt.rcParams.update(theme_rc())

INK = "#262626"
JUNCTION = "#c2185b"


def build_circuit() -> Circuit:
    """A capacitively shunted Josephson junction, grounded at the bottom.

    Every component gets an id, so it stays selectable after placement.
    """
    circuit = Circuit(70, 96, stroke=INK, linecap="round", linejoin="round")
    left, right, top, bottom = 18, 52, 14, 78
    circuit.row(top, top_left=left, phi=(left + right) / 2, top_right=right, dots={"phi"})
    circuit.row(bottom, bottom_left=left, ground_node=(left + right) / 2, bottom_right=right)

    circuit.wire("top_left", "phi", "top_right", id="upper-rail")
    circuit.wire("bottom_left", "ground_node", "bottom_right", id="lower-rail")
    circuit.capacitor("top_left", "bottom_left", id="C")
    circuit.junction("top_right", "bottom_right", id="JJ", color=JUNCTION, lead_color=INK)
    circuit.ground("ground_node", id="ground")

    circuit.label("C", (left - 7, (top + bottom) / 2), id="label-C", anchor="rc")
    circuit.label("JJ", (right + 7, (top + bottom) / 2), id="label-JJ", anchor="lc")
    circuit.label("φ", "phi", offset=(0, -3), id="label-phi", anchor="cb")
    return circuit


def build_plot() -> plt.Figure:
    """The junction's cosine potential, the curve the schematic stands for."""
    phi = np.linspace(-2 * np.pi, 2 * np.pi, 400)
    mpl_fig, ax = plt.subplots(figsize=(3.0, 2.4))
    ax.plot(phi / np.pi, 1 - np.cos(phi), color=JUNCTION)
    ax.set_xlabel(r"$\varphi / \pi$")
    ax.set_ylabel(r"$U / E_J$")
    mpl_fig.tight_layout()
    return mpl_fig


def main() -> None:
    OUT.mkdir(exist_ok=True)

    fig = Figure(width="140mm", height="66mm")
    # Panels start below and right of the margin so `label`'s default offset
    # leaves the panel letters on the canvas.
    schematic = fig.panel("schematic", x="12mm", y="10mm", w="42mm", h="50mm")
    schematic.add(build_circuit(), id="transmon-circuit")

    potential = fig.panel("potential", x="62mm", y="10mm", w="72mm", h="50mm")
    potential.add(build_plot(), id="potential-plot")

    fig.label("a", anchor=schematic.nw)
    fig.label("b", anchor=potential.nw)

    # Ids given inside the circuit survive placement, so restyling reaches through.
    # A label's group sets the fill its text inherits; a symbol's strokes are set
    # on its children, so restyling a symbol group would not show.
    fig.select("#label-JJ").set_style(fill=JUNCTION)

    for suffix in (".svg", ".png"):
        fig.save(OUT / f"vecwire_panel{suffix}")
    print(f"wrote {OUT / 'vecwire_panel.svg'} and PNG")


if __name__ == "__main__":
    main()
