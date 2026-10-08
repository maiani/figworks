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

    circuit.label("C", (left - 10, (top + bottom) / 2), id="label-C", anchor="rc")
    circuit.label("JJ", (right + 7, (top + bottom) / 2), id="label-JJ", anchor="lc")
    circuit.label("φ", "phi", offset=(0, -3), id="label-phi", anchor="cb")
    return circuit


def plot_potential(ax: plt.Axes) -> None:
    """The junction's cosine potential, the curve the schematic stands for."""
    phi = np.linspace(-2 * np.pi, 2 * np.pi, 400)
    ax.plot(phi / np.pi, 1 - np.cos(phi), color=JUNCTION)
    ax.set_xlabel(r"$\varphi / \pi$")
    ax.set_ylabel(r"$U / E_J$")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    fig = Figure(width="140mm", height="66mm")
    # Panels start below and right of the margin so `label`'s default offset
    # leaves the panel letters on the canvas.
    # The circuit is drawn in pt, so placed at its own size its labels print at
    # 8 pt; the plot's axes frame is its panel, so its text keeps its size too.
    schematic = fig.panel("schematic", x="12mm", y="10mm", w="30mm", h="44mm")
    schematic.add(build_circuit(), id="transmon-circuit", fit="none")

    potential = fig.panel("potential", x="58mm", y="10mm", w="76mm", h="42mm")
    mpl_fig, ax = potential.subplots()
    plot_potential(ax)
    potential.add(mpl_fig, id="potential-plot", fit="axes")

    fig.label("a", anchor=schematic.nw)
    fig.label("b", anchor=potential.nw)

    # Ids given inside the circuit survive placement, so restyling reaches through.
    fig.select("#label-JJ").set_style(fill=JUNCTION)

    for suffix in (".svg", ".png"):
        fig.save(OUT / f"vecwire_panel{suffix}")
    print(f"wrote {OUT / 'vecwire_panel.svg'} and PNG")


if __name__ == "__main__":
    main()
