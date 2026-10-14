"""The action potential: the Hodgkin-Huxley model of the squid giant axon.

A VecView scene of the membrane -- a lipid bilayer pierced by a sodium and a
potassium channel, with the ion fluxes they carry -- sits beside Matplotlib
panels computed here from the model with Hodgkin and Huxley's 1952 parameters
(resting potential -65 mV, 6.3 degC), integrated with a hand-written RK4: a
spike train under a current step, one action potential with the two
conductances that make it, the firing-rate curve with its abrupt onset (type II
excitability), and the spike's orbit in the V-n phase plane. Nothing is
measured data; every curve is simulated. The labels in the scene are VecTeX
fragments, pinned upright at 7 pt, and the model's equations beside it are
Matplotlib text; sodium and potassium keep one colour each across the scene,
the equations, and the plots.

Usage:
    python examples/hodgkin_huxley.py     # requires vecview and TeX
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vectex
import vecview

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

THEME = load_theme("nature")
plt.rcParams.update(theme_rc(THEME))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})

INK = "#1a1a1a"
GREY = "#8c8c8c"
NA = "#d55e00"  # Okabe-Ito vermillion
K = "#0072b2"  # Okabe-Ito blue
NA_SOLID = dict(fill="#e4844f", highlight="#f9dccb", stroke="#8a3a0c")
K_SOLID = dict(fill="#3d8dc4", highlight="#d3e6f5", stroke="#0b4166")
HEAD = dict(fill="#c9c2b5", highlight="#f7f4ee", stroke="#8d8576")
CORE = dict(fill="#f2e7c9", stroke="#b9ab86")

# Hodgkin-Huxley parameters: mV, ms, uF/cm^2, mS/cm^2, uA/cm^2.
C_M = 1.0
G_NA, G_K, G_L = 120.0, 36.0, 0.3
E_NA, E_K, E_L = 50.0, -77.0, -54.387
DT = 0.025

# Ions in the scene: Na+ abundant outside the axon, K+ inside.
# fmt: off
IONS = {
    "na-out": [(-3.2, 1.2, 1.8), (-0.5, 1.2, 2.4), (0.6, -1.2, 2.7), (2.9, 1.0, 2.2),
               (3.4, -1.0, 2.3), (-2.6, 0.2, 2.8)],
    "k-out": [(3.8, 0.6, 2.9)],
    "na-in": [(-1.6, -2.1, -2.3)],
    "k-in": [(-2.8, -2.0, -2.0), (-0.6, -2.2, -1.8), (0.6, -1.8, -2.4), (2.4, -2.2, -1.9),
             (3.6, -1.6, -2.3)],
}
# fmt: on

# The model, one line per (left side, right side, colour), aligned on "=".
EQUATIONS = (
    (r"$C_\mathrm{m}\,dV/dt$", r"$I - I_\mathrm{Na} - I_\mathrm{K} - I_\mathrm{L}$", INK),
    (r"$I_\mathrm{Na}$", r"$\bar{g}_\mathrm{Na}\,m^3h\,(V - E_\mathrm{Na})$", NA),
    (r"$I_\mathrm{K}$", r"$\bar{g}_\mathrm{K}\,n^4\,(V - E_\mathrm{K})$", K),
    (r"$I_\mathrm{L}$", r"$\bar{g}_\mathrm{L}\,(V - E_\mathrm{L})$", INK),
    (r"$dx/dt$", r"$\alpha_x(1 - x) - \beta_x x$", INK),
)


# --- physics --------------------------------------------------------------------


def _exprel(x: np.ndarray) -> np.ndarray:
    """x / (1 - exp(-x)), finite at x = 0 where the opening rates are 0/0."""
    x = np.asarray(x, dtype=float)
    small = np.abs(x) < 1e-6
    return np.where(small, 1 + x / 2, x / -np.expm1(-np.where(small, 1.0, x)))


def rates(v: np.ndarray) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    """Opening and closing rates (1/ms) of the gates m, h, n at voltage v (mV)."""
    return (
        (_exprel((v + 40) / 10), 4 * np.exp(-(v + 65) / 18)),
        (0.07 * np.exp(-(v + 65) / 20), 1 / (1 + np.exp(-(v + 35) / 10))),
        (0.1 * _exprel((v + 55) / 10), 0.125 * np.exp(-(v + 65) / 80)),
    )


def steady(v: np.ndarray) -> np.ndarray:
    """The gates' steady-state open probabilities m, h, n at voltage v."""
    return np.array([a / (a + b) for a, b in rates(v)])


def conductances(state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _, m, h, n = state
    return G_NA * m**3 * h, G_K * n**4


def derivative(state: np.ndarray, current: np.ndarray | float) -> np.ndarray:
    v, *gates = state
    g_na, g_k = conductances(state)
    ionic = g_na * (v - E_NA) + g_k * (v - E_K) + G_L * (v - E_L)
    flow = [a * (1 - x) - b * x for x, (a, b) in zip(gates, rates(v), strict=True)]
    return np.array([(current - ionic) / C_M, *flow])


def simulate(t: np.ndarray, current, state: np.ndarray) -> np.ndarray:
    """RK4 from ``state`` over the time grid ``t``; ``current(t)`` in uA/cm^2."""
    out = np.empty((t.size, *state.shape))
    out[0] = state
    for k in range(1, t.size):
        t0 = t[k - 1]
        k1 = derivative(state, current(t0))
        k2 = derivative(state + DT / 2 * k1, current(t0 + DT / 2))
        k3 = derivative(state + DT / 2 * k2, current(t0 + DT / 2))
        k4 = derivative(state + DT * k3, current(t0 + DT))
        state = state + DT / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out[k] = state
    return np.moveaxis(out, 1, 0)  # (variable, time, ...)


REST = np.array([-65.0, *steady(np.array(-65.0))])


def step(on: float, off: float, amplitude: float):
    return lambda t: amplitude * (on <= t < off)


def firing_rate(currents: np.ndarray, settle: float = 150.0, total: float = 450.0) -> np.ndarray:
    """Steady firing rate (Hz) for constant currents, all integrated at once."""
    t = np.arange(0, total, DT)
    v = simulate(t, lambda _: currents, np.repeat(REST[:, None], currents.size, axis=1))[0]
    rate = np.zeros(currents.size)
    for j in range(currents.size):
        up = np.flatnonzero((v[:-1, j] < 0) & (v[1:, j] >= 0) & (t[1:] > settle))
        if up.size > 2:
            rate[j] = 1000 / np.diff(t[up]).mean()
    return rate


# --- panel a: the membrane ------------------------------------------------------


def membrane_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """A bilayer patch pierced by a Na+ and a K+ channel, each a ring of four subunits.

    Outside, Na+ is the abundant ion and K+ inside, as in the axon; each channel
    carries its ion down that gradient.
    """
    cam = vecview.OrthographicCamera(azim_deg=-60.0, elev_deg=22.0, scale=40.0)
    scene = vecview.Scene(cam, pad=4.0)
    scene.sort_by_depth(10)
    edge = dict(stroke_width=1.0)
    half_x, half_y, head_z = 4.2, 1.6, 0.72
    channels = {"na": ((-1.6, 0.0), NA_SOLID), "k": ((1.6, 0.0), K_SOLID)}

    core = vecview.box_faces((0, 0, 0), (2 * half_x, 2 * half_y, 2 * head_z - 0.3))
    scene.faces(10, core, cull=True, id="bilayer-core", **CORE, **edge)
    spacing = 0.4
    for side, z in (("outer", head_z), ("inner", -head_z)):
        for i, x in enumerate(np.arange(-half_x + spacing / 2, half_x, spacing)):
            for j, y in enumerate(np.arange(-half_y + spacing / 2, half_y, spacing)):
                if min(np.hypot(x - c[0], y - c[1]) for c, _ in channels.values()) < 0.95:
                    continue  # room for the channels
                scene.sphere(
                    10, (x, y, z), 0.19, id=f"head-{side}-{i}-{j}", **HEAD, stroke_width=0.7
                )

    for name, ((cx, cy), solid) in channels.items():
        for s in range(4):
            phi = np.pi / 4 + s * np.pi / 2
            x, y = cx + 0.46 * np.cos(phi), cy + 0.46 * np.sin(phi)
            scene.cylinder(
                10,
                (x, y, -1.4),
                (x, y, 1.4),
                0.34,
                end_style={"fill": solid["highlight"]},
                id=f"{name}-channel-{s}",
                class_=f"{name}-channel",
                **solid,
                **edge,
            )

    for name, places in IONS.items():
        radius, solid = (0.17, NA_SOLID) if name.startswith("na") else (0.23, K_SOLID)
        for q, at in enumerate(places):
            scene.sphere(10, at, radius, id=f"{name}-{q}", class_="ion", **solid, **edge)

    for name, z, direction in (("na", 3.3, (0, 0, -1)), ("k", 1.6, (0, 0, 1))):
        (cx, cy), solid = channels[name]
        arrow = dict(shaft_r=0.08, head_r=0.22, head_len=0.45, **solid, **edge)
        scene.arrow3d(10, (cx, cy, z), direction, 1.5, id=f"{name}-flux", **arrow)

    for name, at, align, dx in (
        ("na", (*channels["na"][0], 2.6), "west", 12),
        ("k", (*channels["k"][0], 2.3), "west", 12),
        ("out", (-half_x, -half_y, 1.0), "southeast", -6),
        ("in", (-half_x, -half_y, -1.0), "northeast", -6),
    ):
        label = labels[name]
        scene.slot(20, at, label.width_px, label.height_px, align=align, dx=dx, id=f"label-{name}")
    return scene


def equations() -> plt.Figure:
    """The model's equations as Matplotlib text, at 7 pt in the theme's font."""
    eq = plt.figure(figsize=(2.0, 1.0))
    for row, (left, right, color) in enumerate(EQUATIONS):
        y = 0.95 - 0.9 * row / (len(EQUATIONS) - 1)  # baselines evenly spaced
        for x, text, ha in ((0.28, left, "right"), (0.3, "=", "center"), (0.32, right, "left")):
            eq.text(x, y, text, ha=ha, va="baseline", color=color)
    return eq


# --- panels b-e: the model ------------------------------------------------------


def voltage_axis(ax: plt.Axes) -> None:
    """The membrane potential above a trace that shares, and labels, its time axis."""
    ax.set_ylabel("$V$ (mV)")
    ax.set_ylim(-85, 50)
    ax.set_yticks([-80, -40, 0, 40])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", bottom=False)


def plot_train(axes: np.ndarray) -> None:
    """Repetitive firing for as long as a 10 uA/cm² step lasts."""
    t = np.arange(0, 120, DT)
    current = step(10, 100, 10.0)
    ax, stim = axes
    ax.plot(t, simulate(t, current, REST)[0], color=INK)
    voltage_axis(ax)
    stim.plot(t, [current(s) for s in t], color=GREY)
    stim.text(55, 12, "10 µA/cm²", ha="center", va="bottom", color=GREY, fontsize=6)
    stim.set_ylim(-1, 22)
    stim.set_yticks([])
    stim.spines["left"].set_visible(False)
    stim.set_xlim(0, 120)
    stim.set_xticks([0, 40, 80, 120])
    stim.set_xlabel("Time (ms)")


def plot_spike(axes: np.ndarray) -> None:
    """One action potential: g_Na opens fast and inactivates, g_K follows slowly."""
    t = np.arange(0, 12, DT)
    state = simulate(t, step(1, 2, 20.0), REST)
    g_na, g_k = conductances(state)
    ax, g = axes
    ax.plot(t, state[0], color=INK)
    voltage_axis(ax)
    g.plot(t, g_na, color=NA)
    g.plot(t, g_k, color=K)
    g.text(2.3, 28, r"$g_\mathrm{Na}$", color=NA, ha="right", va="center")
    g.text(5.6, 11, r"$g_\mathrm{K}$", color=K, va="bottom")
    g.set_ylim(0, 40)
    g.set_yticks([0, 20, 40])
    g.set_ylabel("$g$ (mS/cm²)")
    g.set_xlim(0, 12)
    g.set_xticks([0, 4, 8, 12])
    g.set_xlabel("Time (ms)")


def plot_rate(ax: plt.Axes) -> None:
    """Firing starts at a finite rate: the hallmark of type II excitability."""
    currents = np.linspace(0, 20, 81)
    rate = firing_rate(currents)
    fires = rate > 0
    onset, jump = currents[fires][0], rate[fires][0]
    ax.plot(currents[~fires], rate[~fires], color=INK)
    ax.plot(currents[fires], rate[fires], color=INK)
    ax.plot([onset, onset], [0, jump], color=INK, linestyle=(0, (1, 1.5)))
    ax.text(onset + 0.5, jump - 3, f"onset at {jump:.0f} Hz", va="top", fontsize=6)
    ax.set_xlabel("$I$ (µA/cm²)")
    ax.set_ylabel("Firing rate (Hz)")
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 100)


def plot_phase(ax: plt.Axes) -> None:
    """The spike as a loop in (V, n), round the nullclines of Rinzel's reduction."""
    t = np.arange(0, 60, DT)
    state = simulate(t, lambda _: 10.0, REST)
    late = t > 30
    vv, nn = np.meshgrid(np.linspace(-80, 45, 400), np.linspace(0.3, 0.8, 300))
    m_inf = steady(vv)[0]
    h = 0.89 - 1.1 * nn  # h slaved to n
    ionic = G_NA * m_inf**3 * h * (vv - E_NA) + G_K * nn**4 * (vv - E_K) + G_L * (vv - E_L)
    ax.contour(vv, nn, 10.0 - ionic, levels=[0], colors=GREY, linewidths=0.75)
    v = np.linspace(-80, 45, 300)
    ax.plot(v, steady(v)[2], color=K)
    ax.plot(state[0][late], state[3][late], color=INK)
    ax.text(30, 0.72, r"$\dot n = 0$", color=K, ha="center")
    ax.text(-52, 0.36, r"$\dot V = 0$", color=GREY)
    ax.set_xlabel("$V$ (mV)")
    ax.set_ylabel("$n$")
    ax.set_xlim(-80, 45)
    ax.set_ylim(0.3, 0.8)


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="120mm", theme=THEME)
    panels = fig.grid(
        [["membrane", "membrane", "train"], ["spike", "rate", "phase"]],
        margins=("7.5mm", "3mm", "9mm", "11mm"),  # top, right, bottom, left
        gap="13mm",
    )

    tex = THEME.vectex()
    labels = {
        "na": vectex.render(r"$\mathrm{Na}^+$", **tex | {"color": NA}),
        "k": vectex.render(r"$\mathrm{K}^+$", **tex | {"color": K}),
        "out": vectex.render("Extracellular", **tex | {"color": GREY}),
        "in": vectex.render("Cytoplasm", **tex | {"color": GREY}),
    }
    box = panels["membrane"]
    split = 0.62 * box.w
    fig.add(membrane_scene(labels), x=box.x, y=box.y, w=split, h=box.h, id="membrane-scene")
    eq_box = dict(x=box.x + split, y=box.y, w=box.w - split, h=box.h)
    fig.add(equations(), **eq_box, id="hh-equations", fit="none")
    for name, label in labels.items():
        fig.fill_slot(f"label-{name}", label)

    for name, plot, ratios in (("train", plot_train, (5.5, 1)), ("spike", plot_spike, (2.2, 1))):
        grid = dict(height_ratios=ratios, hspace=0.1)
        mpl_fig, axes = panels[name].subplots(2, sharex=True, gridspec_kw=grid)
        plot(axes)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")
    for name, plot in (("rate", plot_rate), ("phase", plot_phase)):
        mpl_fig, ax = panels[name].subplots()
        plot(ax)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    for letter, panel in zip("abcde", panels.values(), strict=True):
        fig.label(letter, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"hodgkin_huxley{suffix}")
    print(f"wrote {OUT / 'hodgkin_huxley.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
