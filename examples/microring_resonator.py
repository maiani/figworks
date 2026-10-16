"""An all-pass silicon-nitride microring resonator as a Nature double-column figure.

A VecView scene of the device -- a ring beside a bus waveguide, drawn at
critical coupling, so the light that enters builds up in the ring and almost
none reaches the through port -- meets three Matplotlib panels computed from
the exact all-pass transmission

    T = (a^2 - 2 r a cos(phi) + r^2) / (1 - 2 a r cos(phi) + (r a)^2),

with r the self-coupling of the bus and a the round-trip amplitude of the ring.
The parameters are realistic for a 50 um SiN ring at 1550 nm; the coupling's
mild growth with wavelength (the evanescent tail lengthens) is a model
assumption. Every curve is computed here; nothing is measured. The labels are
VecTeX fragments in the theme's sans-serif math, pinned into the 3D scene.

Usage:
    python examples/microring_resonator.py     # requires vecview and TeX
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vectex
import vecview
from matplotlib.ticker import FuncFormatter
from vecview import outlines

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

THEME = load_theme("nature")
plt.rcParams.update(theme_rc(THEME))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})

INK = "#262626"
UNDER, CRITICAL, OVER = "#0072b2", "#d55e00", "#009e73"  # Okabe-Ito
LIGHT = CRITICAL  # the device is drawn critically coupled
NITRIDE = dict(top="#dfe4ea", side="#a9b3c0")
OXIDE = dict(top="#f4f6f8", side="#dde2e8")
EDGE = "#8b96a6"

LAMBDA0 = 1550.0  # nm
RADIUS = 50e3  # nm
N_GROUP = 2.1
LOSS_DB_CM = 1.0
LENGTH = 2 * np.pi * RADIUS  # nm
MODE = 385  # azimuthal order resonant at LAMBDA0, so n_eff = MODE LAMBDA0 / LENGTH ~ 1.90
N_EFF = MODE * LAMBDA0 / LENGTH
COUPLING_SCALE = 15.0  # nm: kappa^2 grows by e over this span of wavelength


# --- physics --------------------------------------------------------------------


def round_trip(loss_db_cm: float | np.ndarray) -> np.ndarray:
    """Round-trip field amplitude a of the ring for a propagation loss in dB/cm."""
    return 10 ** (-np.asarray(loss_db_cm) * LENGTH * 1e-7 / 20)


A = round_trip(LOSS_DB_CM)
KAPPA2_CRIT = 1 - A**2  # power coupling at which r = a
REGIMES = {"under": 0.4 * KAPPA2_CRIT, "critical": KAPPA2_CRIT, "over": 2.5 * KAPPA2_CRIT}
COLORS = {"under": UNDER, "critical": CRITICAL, "over": OVER}


def round_trip_phase(wavelength: np.ndarray) -> np.ndarray:
    """phi = 2 pi n_eff(lambda) L / lambda, with n_eff dispersed to give the group index."""
    n_eff = N_EFF + (N_EFF - N_GROUP) * (wavelength - LAMBDA0) / LAMBDA0
    return 2 * np.pi * n_eff * LENGTH / wavelength


def transmission(phi: np.ndarray, r: float | np.ndarray, a: float | np.ndarray) -> np.ndarray:
    """Through-port power transmission of an all-pass ring."""
    return (a**2 - 2 * r * a * np.cos(phi) + r**2) / (1 - 2 * a * r * np.cos(phi) + (r * a) ** 2)


def self_coupling(kappa2: float | np.ndarray) -> np.ndarray:
    return np.sqrt(1 - np.asarray(kappa2))


def buildup(r: float | np.ndarray, a: float) -> np.ndarray:
    """Ring power over input power on resonance, (1 - r^2) / (1 - r a)^2."""
    return (1 - r**2) / (1 - r * a) ** 2


def loaded_q(r: float | np.ndarray, a: float) -> np.ndarray:
    """Loaded quality factor, from the resonance's full width at half depth."""
    return np.pi * N_GROUP * LENGTH * np.sqrt(r * a) / (LAMBDA0 * (1 - r * a))


FSR = LAMBDA0**2 / (N_GROUP * LENGTH)  # nm


# --- panel a: the device --------------------------------------------------------

R, W, H, G = 3.0, 0.42, 0.34, 0.30  # scene units: ring radius, width, height, gap
BUS_Y = -(R + W + G)
CHIP = ((-4.3, -4.7), (4.3, 3.6))
UP = (0.0, 0.0, 1.0)


def device_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """Ring and bus on an oxide chip; the light enters left and circulates in the ring."""
    cam = vecview.OrthographicCamera(azim_deg=-62.0, elev_deg=36.0, scale=40.0)
    scene = vecview.Scene(cam, pad=2.0)

    def block(layer: int, footprint: np.ndarray, z0: float, z1: float, id: str, colors) -> None:
        faces = vecview.prism_faces(footprint, z0, z1)
        style = dict(stroke=EDGE, stroke_width=1.0, stroke_linejoin="round", id=id)
        walls = [f for f in faces if f.name != "+z"]
        scene.faces(layer, walls, cull=True, fill=colors["side"], **style)
        scene.faces(layer + 1, [f for f in faces if f.name == "+z"], fill=colors["top"], **style)

    block(10, outlines.rect(*CHIP), -0.6, 0.0, "chip", OXIDE)
    bus = outlines.rect((CHIP[0][0], BUS_Y - W / 2), (CHIP[1][0], BUS_Y + W / 2))
    block(30, bus, 0.0, H, "bus", NITRIDE)

    # The ring is one footprint with a hole: seamless walls, outside and in the
    # hole, under a cap whose stroke draws both rims.
    ring = vecview.annulus((0, 0), R - W / 2, R + W / 2, n=192)
    scene.prism_walls(20, ring, 0.0, H, fill=NITRIDE["side"], id="ring-walls")
    top = outlines.to_plane(ring, origin=(0, 0, H))
    scene.polygon(21, top, fill=NITRIDE["top"], stroke=EDGE, stroke_width=1.0, id="ring")

    # The radius, on the chip inside the ring.
    tip = (R - W / 2) * np.array([np.cos(-0.35), np.sin(-0.35), 0.0])
    scene.polyline(15, [(0, 0, 0), tip], stroke=INK, stroke_width=1.0, id="radius")
    scene.sphere(15, (0, 0, 0), 0.07, fill=INK, id="ring-centre")

    # Light: a soft halo under a bright core along the top of each guide.
    def glow(layer: int, pts: np.ndarray, strength: float, id: str) -> None:
        for width, opacity in ((16.0, 0.08), (8.0, 0.16), (2.2, 1.0)):
            line = dict(stroke=LIGHT, stroke_width=width, stroke_opacity=opacity * strength)
            scene.polyline(layer, pts, stroke_linecap="round", id=f"{id}-{width:g}", **line)

    z, left, right = H + 0.01, CHIP[0][0], CHIP[1][0]
    ring_line = vecview.arc_shape((0, 0, z), (1, 0, 0), (0, 1, 0), R, 0, 360, n=192)
    glow(40, ring_line, 1.0, "ring-field")
    glow(41, np.array([[left, BUS_Y, z], [0.0, BUS_Y, z]]), 0.7, "input-field")
    glow(41, np.array([[0.0, BUS_Y, z], [right, BUS_Y, z]]), 0.12, "through-field")

    # At critical coupling almost nothing reaches the through port.
    arrow = dict(normal=UP, shaft_w=0.12, head_w=0.42, head_len=0.45, fill=LIGHT)
    scene.arrow(45, (left - 1.9, BUS_Y, z), (1, 0, 0), 1.6, id="input-arrow", **arrow)
    scene.arrow(
        45, (right + 0.3, BUS_Y, z), (1, 0, 0), 1.6, id="through-arrow", fill_opacity=0.3, **arrow
    )
    # Light coupled in at the bottom of the ring travels on in +x: counter-clockwise.
    flow = vecview.arc_shape((0, 0, 0), (1, 0, 0), (0, 1, 0), R - 1.0, 45, 135, n=24)
    scene.polyline(16, flow, stroke=LIGHT, stroke_width=2.0, id="circulation")
    head = dict(normal=UP, shaft_w=0.0, head_w=0.4, head_len=0.45, fill=LIGHT)
    tangent = (-np.sin(np.radians(135)), np.cos(np.radians(135)), 0)
    scene.arrow(16, flow[-1], tangent, 0.45, pivot="tip", id="circulation-head", **head)

    # A callout from in front of the bus points g at the coupling gap.
    leader = [(0.0, BUS_Y + W / 2 + G / 2, H), (0.0, BUS_Y - 1.3, H)]
    scene.polyline(46, leader, stroke=INK, stroke_width=1.0, id="gap-leader")
    anchors = {
        "input": ((left - 1.1, BUS_Y, z), "south", 0, -7),
        "through": ((right + 1.1, BUS_Y, z), "south", 0, -7),
        "R": (0.5 * tip, "south", 0, -3),
        "g": (leader[1], "north", 0, 1),
    }
    for name, (at, align, dx, dy) in anchors.items():
        label = labels[name]
        w, h = label.width_px, label.height_px
        pin = dict(align=align, dx=dx, dy=dy, id=f"label-{name}")
        scene.slot(50, at, w, h, content=label.to_svg_py(), **pin)
    return scene


# --- panels b-d: the plots ------------------------------------------------------


def plot_spectrum(ax: plt.Axes) -> None:
    """Through-port transmission over three FSRs; the coupling grows with wavelength."""
    wavelength = np.linspace(LAMBDA0 - 5.6, LAMBDA0 + 5.6, 112001)
    kappa2 = KAPPA2_CRIT * np.exp((wavelength - LAMBDA0) / COUPLING_SCALE)
    t = transmission(round_trip_phase(wavelength), self_coupling(kappa2), A)
    db = 10 * np.log10(np.maximum(t, 1e-4))
    ax.plot(wavelength, db, color=INK)
    for name, dip, ha in (("under", -FSR, "right"), ("critical", 0, "left"), ("over", FSR, "left")):
        near = np.abs(wavelength - LAMBDA0 - dip) < 0.05
        pad = -0.12 if ha == "right" else 0.12
        ax.text(LAMBDA0 + dip + pad, db[near].min(), name, color=COLORS[name], ha=ha, va="center")
    y = -9
    ax.annotate(
        "",
        xy=(LAMBDA0 - FSR, y),
        xytext=(LAMBDA0, y),
        arrowprops=dict(arrowstyle="<->", lw=0.5, color=INK, shrinkA=1.5, shrinkB=1.5),
    )
    ax.text(LAMBDA0 - FSR / 2, y - 1.5, f"FSR = {FSR:.2f} nm", ha="center", va="top")
    ax.set_xlim(wavelength[0], wavelength[-1])
    ax.set_ylim(-43, 2)
    ax.set_yticks([-40, -30, -20, -10, 0])
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Through transmission (dB)")


def plot_resonance(ax: plt.Axes) -> None:
    """One resonance for three couplings: under, critical and over."""
    detuning = np.linspace(-20, 20, 801)  # pm
    phi = round_trip_phase(LAMBDA0 + detuning * 1e-3)
    for name, kappa2 in REGIMES.items():
        ax.plot(detuning, transmission(phi, self_coupling(kappa2), A), color=COLORS[name])
    for name, x, y in (("over", 9.0, 0.56), ("under", 3.2, 0.16), ("critical", 2.4, 0.02)):
        ax.text(x, y, name, color=COLORS[name], va="bottom")
    ax.set_xlim(-20, 20)
    ax.set_xticks([-20, -10, 0, 10, 20])
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Detuning (pm)")
    ax.set_ylabel("Through transmission")


def plot_buildup(ax: plt.Axes) -> None:
    """Intracavity power on resonance, which peaks at critical coupling, with each loaded Q."""
    kappa2 = np.logspace(-3.6, -1, 400)
    ax.plot(100 * kappa2, buildup(self_coupling(kappa2), A), color=INK)
    placement = {"under": (-5, 0, "right"), "critical": (0, 5, "center"), "over": (5, 0, "left")}
    for name, k in REGIMES.items():
        dx, dy, ha = placement[name]
        r, color = self_coupling(k), COLORS[name]
        ax.plot(100 * k, buildup(r, A), "o", color=color, mec="white", mew=0.5, ms=4.5)
        q = loaded_q(r, A)
        e = int(np.log10(q))
        text = rf"$Q_L = {q / 10**e:.1f}\times10^{e}$"
        where = dict(
            xytext=(dx, dy), textcoords="offset points", ha=ha, va="bottom" if dy else "center"
        )
        ax.annotate(text, (100 * k, buildup(r, A)), color=color, **where)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(100 * kappa2[0], 100 * kappa2[-1])
    ax.set_ylim(0, 170)
    ax.set_xlabel(r"Power coupling $\kappa^2$ (%)")
    ax.set_ylabel(r"Build-up $P_\mathrm{ring}/P_\mathrm{in}$")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="115mm", theme=THEME, background="white")
    panels = fig.grid(
        [["device", "spectrum"], ["resonance", "buildup"]],
        width_ratios=(1, 1.15),
        height_ratios=(0.9, 1),
        margins=("8mm", "4mm", "9mm", "12mm"),
        gap=("14mm", "16mm"),
    )

    tex = dict(input=r"$E_\mathrm{in}$", through=r"$E_\mathrm{t}$", R="$R$", g="$g$")
    labels = {name: vectex.render(src, **THEME.vectex()) for name, src in tex.items()}

    panels["device"].add(device_scene(labels), id="device-scene")
    equation = vectex.render(
        r"$T = \dfrac{a^2 - 2ra\cos\varphi + r^2}{1 - 2ar\cos\varphi + (ra)^2}$",
        **THEME.vectex(),
    )
    c = panels["resonance"]  # the equation sits in the free lower left of panel c
    box = dict(x=c.x + 0.03 * c.w, y=c.y + 0.6 * c.h, w=0.4 * c.w, h=0.36 * c.h)
    fig.add(equation, **box, fit="none", align="southwest", id="transmission-equation")

    plots = dict(spectrum=plot_spectrum, resonance=plot_resonance, buildup=plot_buildup)
    for name, plot in plots.items():
        mpl_fig, ax = panels[name].subplots()
        plot(ax)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    for letter, panel in zip("abcd", panels.values(), strict=True):
        fig.label(letter, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"microring_resonator{suffix}")
    print(f"wrote {OUT / 'microring_resonator.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
