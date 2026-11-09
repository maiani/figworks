"""A transmon qubit as a journal figure: device, circuit, potential, and spectrum.

Four producers meet in one Physical Review two-column figure, each through
`Panel.add`: a VecView scene of the device, a VecWire circuit, and two
Matplotlib panels whose axes frames sit exactly on the grid. The TeX labels are
VecTeX fragments and all print at 8 pt: those pinned into the 3D scene however
the scene was scaled, and the circuit's because it is placed at its own size.

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

THEME = load_theme("aps")
plt.rcParams.update(theme_rc(THEME))

INK = "#262626"
JUNCTION = "#c2185b"
METAL = dict(top="#d5dbe3", side="#9aa5b4")
SUBSTRATE = dict(top="#f1f3f6", side="#d8dde5")
EDGE = "#8b96a6"
LEVELS = ("#173f74", "#2f7fc1", "#62aee0")

EJ_OVER_EC = 30.0
PSI_SCALE = 5.5  # wavefunction height in panel c, in E_C per unit amplitude


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


def transmon_states(ej_over_ec: float, phi: np.ndarray, count: int = 3):
    """The lowest levels at n_g = 0 and their wavefunctions psi_m(phi), normalized.

    psi(phi) = sum_n c_n exp(i n phi) / sqrt(2 pi) from the charge-basis eigenvectors.
    Parity makes each one real or purely imaginary; the outermost lobe on the right
    is taken positive.
    """
    n = np.arange(-20, 21)
    hopping = -ej_over_ec / 2 * (np.eye(n.size, k=1) + np.eye(n.size, k=-1))
    energies, vectors = np.linalg.eigh(np.diag(4.0 * n**2) + hopping)
    psi = np.exp(1j * np.outer(phi, n)) @ vectors[:, :count] / np.sqrt(2 * np.pi)
    psi = (psi.real + psi.imag).T
    turns = np.arccos(-energies[:count] / ej_over_ec)
    signs = [np.sign(np.interp(t, phi, p)) for t, p in zip(turns, psi, strict=True)]
    return energies[:count], psi * np.array(signs)[:, None]


# --- panel a: the device --------------------------------------------------------


def device_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """Two capacitor pads joined by a junction, a gap away from a meander resonator.

    Each `slot` pins its label upright, at the label's own size.
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
        w, h = label.width_px, label.height_px
        scene.slot(
            40, at, w, h, content=label.to_svg_py(), align="south", dy=-5, id=f"label-{name}"
        )
    return scene


# --- panel b: the circuit -------------------------------------------------------


def circuit_diagram(labels: dict[str, vectex.VectexFragment]) -> Circuit:
    """The junction shunted by C_B, coupled through C_g to an L_r C_r resonator."""
    circuit = Circuit(126, 104, stroke=INK)  # in pt; placed at this size
    top, bottom = 16, 64
    circuit.row(top, jj_top=14, phi=29, cb_top=44, cr_top=78, lr_top=104, dots={"phi"})
    circuit.row(bottom, jj_bot=14, cb_bot=44, gnd=61, cr_bot=78, lr_bot=104)

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
    circuit.label(labels["EJ"], (6, middle), anchor="rc", id="circuit-EJ")
    circuit.label(labels["CB"], (54, middle), anchor="lc", id="circuit-CB")
    circuit.label(labels["Cg"], (61, top - 9), anchor="cb", id="circuit-Cg")
    circuit.label(labels["Cr"], (88, middle), anchor="lc", id="circuit-Cr")
    circuit.label(labels["Lr"], (113, middle), anchor="lc", id="circuit-Lr")
    circuit.label(labels["phi"], "phi", offset=(0, -3), anchor="cb", id="circuit-phi")
    circuit.label(labels["H"], (63, 88), anchor="cc", id="hamiltonian")
    return circuit


# --- panels c to e: the plots -------------------------------------------------


def plot_potential(ax: plt.Axes) -> None:
    """The cosine well, its lowest levels between their turning points, and their states."""
    phi = np.linspace(-np.pi, np.pi, 601)
    x = phi / np.pi
    ax.plot(x, -EJ_OVER_EC * np.cos(phi), color=INK)
    energies, states = transmon_states(EJ_OVER_EC, phi)
    for m, (energy, psi, color) in enumerate(zip(energies, states, LEVELS, strict=True)):
        turn = np.arccos(-energy / EJ_OVER_EC) / np.pi
        ax.plot([-turn, turn], [energy, energy], color=color, lw=0.5)
        shown = np.abs(psi) > 0.2 * np.abs(psi).max()  # drop the flat tails
        span = slice(np.argmax(shown), len(shown) - np.argmax(shown[::-1]))
        wave = energy + PSI_SCALE * psi[span]
        ax.fill_between(x[span], energy, wave, color=color, alpha=0.25, lw=0)
        ax.plot(x[span], wave, color=color)
        ax.text(x[span][-1] + 0.04, energy, rf"$E_{m}$", va="center", color=color)
    ax.set_title(rf"$E_J/E_C = {EJ_OVER_EC:g}$")
    ax.set_xlim(-1, 1)
    ax.set_xticks([-1, 0, 1])
    ax.set_ylim(-EJ_OVER_EC * 1.05, EJ_OVER_EC * 1.05)
    ax.set_xlabel(r"$\varphi/\pi$")
    ax.set_ylabel(r"$U/E_C$")


def plot_dispersion(ax: plt.Axes, ej_over_ec: float) -> None:
    """Charge dispersion: the levels flatten as E_J/E_C grows, which is the transmon."""
    ng = np.linspace(-1, 1, 301)
    levels = transmon_levels(ej_over_ec, ng)
    sweet = transmon_levels(ej_over_ec, 0.5)[0]
    for m, color in enumerate(LEVELS):
        ax.plot(ng, (levels[:, m] - sweet[0]) / (sweet[1] - sweet[0]), color=color)
    ax.set_title(rf"$E_J/E_C = {ej_over_ec:g}$")
    ax.set_xlabel(r"$n_g$")
    ax.set_ylabel(r"$(E_m - E_0)/E_{01}$")
    ax.set_xlim(-1, 1)
    ax.set_xticks([-1, 0, 1])
    ax.set_ylim(-1, 9)  # shared by both regimes, so the flattening shows


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="104mm", theme=THEME, background="white")
    panels = fig.grid(
        [["device", "device", "circuit"], ["potential", "charge-regime", "transmon-regime"]],
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
    style = THEME.vectex()  # the plots' Times and size, so a symbol reads the same everywhere
    labels = {name: vectex.render(source, **style) for name, source in tex.items()}
    labels["EJ"] = vectex.render(tex["EJ"], **style | {"color": JUNCTION})

    panels["device"].add(device_scene(labels), id="device-scene")

    panels["circuit"].add(circuit_diagram(labels), id="circuit", fit="none")

    mpl_fig, ax = panels["potential"].subplots()
    plot_potential(ax)
    panels["potential"].add(mpl_fig, id="potential-plot", fit="axes")

    for name, ratio in (("charge-regime", 1.0), ("transmon-regime", EJ_OVER_EC)):
        mpl_fig, ax = panels[name].subplots()
        plot_dispersion(ax, ratio)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    for letter, panel in zip("abcde", panels.values(), strict=True):
        fig.label(letter, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"transmon_figure{suffix}")
    print(f"wrote {OUT / 'transmon_figure.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
