"""A transmon qubit as a journal figure: device, circuit, potential, and spectrum.

Four producers meet in one Physical Review two-column figure, each through
`Panel.add`: a VecView scene of the device, a VecWire circuit, and two
Matplotlib panels whose axes frames sit exactly on the grid. The TeX labels are
VecTeX fragments; those pinned into the 3D scene keep their 8 pt size however
the scene was scaled to fit its panel.

Usage:
    python examples/transmon_figure.py     # requires vecview and vecwire
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vectex
import vecview
from vecview import outlines
from vecwire import Circuit

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

STYLE = "aps"
plt.rcParams.update(theme_rc(STYLE))

INK = "#262626"
JUNCTION = "#c2185b"
METAL = dict(top="#d5dbe3", side="#9aa5b4")
SUBSTRATE = dict(top="#f1f3f6", side="#d8dde5")
EDGE = "#8b96a6"
LEVELS = ("#173f74", "#2f7fc1", "#62aee0")

EJ_OVER_EC = 30.0


# --- physics --------------------------------------------------------------------


def transmon_levels(ej_over_ec: float, ng: float | np.ndarray, count: int = 3) -> np.ndarray:
    """Lowest eigenenergies of H = 4 E_C (n - n_g)^2 - E_J cos(phi), in units of E_C.

    Diagonalized in the charge basis, where cos(phi) couples neighbouring n.
    Returns an array of shape ``(len(ng), count)``.
    """
    n = np.arange(-20, 21)
    hopping = -ej_over_ec / 2 * (np.eye(n.size, k=1) + np.eye(n.size, k=-1))
    return np.array(
        [np.linalg.eigvalsh(np.diag(4 * (n - g) ** 2) + hopping)[:count] for g in np.atleast_1d(ng)]
    )


# --- panel a: the device --------------------------------------------------------


def device_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """Two capacitor pads joined by a junction, a gap away from a meander resonator.

    Each `slot` reserves an upright anchor, the size of its label, that the
    figure fills with that label.
    """
    cam = vecview.OrthographicCamera(azim_deg=30.0, elev_deg=32.0, scale=40.0)
    scene = vecview.Scene(cam, pad=2.0)

    def film(layer: int, footprint: np.ndarray, z: float, id: str, colors: dict) -> None:
        """A footprint extruded from 0 to ``z``: its visible walls, then its top."""
        faces = vecview.prism_faces(footprint, 0.0 if z > 0 else z, max(z, 0.0))
        style = dict(stroke=EDGE, stroke_width=0.8, stroke_linejoin="round", id=id)
        walls = [f for f in faces if f.name != "+z"]
        scene.faces(layer, walls, cull=True, fill=colors["side"], **style)
        scene.faces(layer + 1, [f for f in faces if f.name == "+z"], fill=colors["top"], **style)

    film(10, outlines.rect((-3.2, -7.4), (3.2, 11.0)), -0.6, "substrate", SUBSTRATE)
    film(20, outlines.rect((-1.8, -6.2), (1.8, -1.0)), 0.12, "pad-left", METAL)
    film(20, outlines.rect((-1.8, 1.0), (1.8, 6.2)), 0.12, "pad-right", METAL)
    film(20, outlines.rect((-0.12, -1.0), (0.12, -0.16)), 0.12, "lead-left", METAL)
    film(20, outlines.rect((-0.12, 0.16), (0.12, 1.0)), 0.12, "lead-right", METAL)

    # The resonator: a claw facing the right pad across the coupling gap, then a meander.
    w = 0.12
    strips = [outlines.rect((-1.4, 6.8), (1.4, 7.2)), outlines.rect((-w, 7.2), (w, 7.9))]
    legs = (7.9, 8.6, 9.3, 10.0)
    for i, y in enumerate(legs):
        strips.append(outlines.rect((-2.2, y - w), (2.2, y + w)))
        if i + 1 < len(legs):
            x = 2.2 if i % 2 == 0 else -2.2
            strips.append(outlines.rect((x - w, y), (x + w, legs[i + 1])))
    (resonator,) = outlines.union(*strips)
    film(20, resonator, 0.12, "resonator", METAL)

    junction = dict(top=JUNCTION, side="#8e1243")
    film(30, outlines.rect((-0.2, -0.16), (0.2, 0.16)), 0.22, "junction", junction)

    for name, at in (
        ("EJ", (0.0, 0.0, 0.22)),
        ("CB", (-1.8, -3.6, 0.12)),
        ("Cg", (-1.4, 6.6, 0.12)),
        ("res", (-2.2, 10.0, 0.12)),
    ):
        label = labels[name]
        scene.slot(
            40, at, label.width_px, label.height_px, align="south", dy=-5, id=f"label-{name}"
        )
    return scene


# --- panel b: the circuit -------------------------------------------------------


def circuit_diagram(labels: dict[str, vectex.VectexFragment]) -> Circuit:
    """The junction shunted by C_B, coupled through C_g to an L_r C_r resonator."""
    circuit = Circuit(134, 104, stroke=INK)
    top, bottom = 16, 64
    circuit.row(top, jj_top=16, phi=32, cb_top=48, cr_top=86, lr_top=114, dots={"phi"})
    circuit.row(bottom, jj_bot=16, cb_bot=48, gnd=67, cr_bot=86, lr_bot=114)

    circuit.wire("jj_top", "phi", "cb_top", id="transmon-rail")
    circuit.wire("cr_top", "lr_top", id="resonator-rail")
    circuit.wire("jj_bot", "cb_bot", "gnd", "cr_bot", "lr_bot", id="ground-rail")
    circuit.junction("jj_top", "jj_bot", id="JJ", color=JUNCTION, lead_color=INK)
    circuit.capacitor("cb_top", "cb_bot", id="CB")
    circuit.capacitor("cb_top", "cr_top", id="Cg")
    circuit.capacitor("cr_top", "cr_bot", id="Cr")
    circuit.inductor("lr_top", "lr_bot", id="Lr")
    circuit.ground("gnd", id="ground")

    middle = (top + bottom) / 2
    circuit.label(labels["EJ"], (8, middle), anchor="rc", id="circuit-EJ")
    circuit.label(labels["CB"], (58, middle), anchor="lc", id="circuit-CB")
    circuit.label(labels["Cg"], (67, top - 9), anchor="cb", id="circuit-Cg")
    circuit.label(labels["Cr"], (96, middle), anchor="lc", id="circuit-Cr")
    circuit.label(labels["Lr"], (123, middle), anchor="lc", id="circuit-Lr")
    circuit.label(labels["phi"], "phi", offset=(0, -3), anchor="cb", id="circuit-phi")
    circuit.label(labels["H"], (67, 88), anchor="cc", id="hamiltonian")
    return circuit


# --- panels c and d: the plots --------------------------------------------------


def plot_potential(ax: plt.Axes) -> None:
    """The cosine well and its lowest levels, each drawn between its turning points."""
    phi = np.linspace(-np.pi, np.pi, 400)
    ax.plot(phi / np.pi, -EJ_OVER_EC * np.cos(phi), color=INK)
    for m, (energy, color) in enumerate(
        zip(transmon_levels(EJ_OVER_EC, 0.0)[0], LEVELS, strict=True)
    ):
        turn = np.arccos(-energy / EJ_OVER_EC) / np.pi
        ax.plot([-turn, turn], [energy, energy], color=color)
        ax.text(0, energy + 1.2, rf"$E_{m}$", ha="center", va="bottom", color=color)
    ax.set_xlim(-1, 1)
    ax.set_xticks([-1, 0, 1])
    ax.set_ylim(-EJ_OVER_EC * 1.05, EJ_OVER_EC * 1.05)
    ax.set_xlabel(r"$\varphi/\pi$")
    ax.set_ylabel(r"$U/E_C$")


def plot_bands(axes: np.ndarray) -> None:
    """Charge dispersion: the levels flatten as E_J/E_C grows, which is the transmon."""
    ng = np.linspace(-1, 1, 301)
    for ax, ratio in zip(axes, (1.0, EJ_OVER_EC), strict=True):
        levels = transmon_levels(ratio, ng)
        sweet = transmon_levels(ratio, 0.5)[0]
        for m, color in enumerate(LEVELS):
            ax.plot(ng, (levels[:, m] - sweet[0]) / (sweet[1] - sweet[0]), color=color)
        ax.set_title(rf"$E_J/E_C = {ratio:g}$")
        ax.set_xlabel(r"$n_g$")
        ax.set_xlim(-1, 1)
        ax.set_xticks([-1, 0, 1])
    axes[0].set_ylabel(r"$(E_m - E_0)/E_{01}$")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    theme = load_theme(STYLE)
    fig = Figure(width=theme.page["double"], height="104mm", theme=theme)
    panels = fig.grid(
        [["device", "device", "circuit"], ["potential", "bands", "bands"]],
        height_ratios=(1.1, 1),
        margins=("6mm", "3mm", "10mm", "12mm"),  # top, right, bottom, left
        gap=("13mm", "14mm"),  # between rows, between columns
    )

    tex = {
        "EJ": r"$E_J$",
        "CB": r"$C_B$",
        "Cg": r"$C_g$",
        "Cr": r"$C_r$",
        "Lr": r"$L_r$",
        "res": r"$L_r, C_r$",
        "phi": r"$\varphi$",
        "H": r"$H = 4E_C(\hat n - n_g)^2 - E_J \cos\hat\varphi$",
    }
    labels = {name: vectex.render(source, size_pt=8) for name, source in tex.items()}
    labels["EJ"] = vectex.render(tex["EJ"], size_pt=8, color=JUNCTION)

    panels["device"].add(device_scene(labels), id="device-scene")
    for name in ("EJ", "CB", "Cg", "res"):
        fig.fill_slot(f"label-{name}", labels[name])

    panels["circuit"].add(circuit_diagram(labels), id="circuit")

    mpl_fig, ax = panels["potential"].subplots()
    plot_potential(ax)
    panels["potential"].add(mpl_fig, id="potential-plot", fit="axes")

    mpl_fig, axes = panels["bands"].subplots(1, 2, sharey=True, gridspec_kw=dict(wspace=0.12))
    plot_bands(axes)
    panels["bands"].add(mpl_fig, id="bands-plot", fit="axes")

    for letter, panel in zip("abcd", panels.values(), strict=True):
        fig.label(letter, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"transmon_figure{suffix}")
    print(f"wrote {OUT / 'transmon_figure.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
