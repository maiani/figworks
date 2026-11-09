"""A vacuum triode in the style of an engineering handbook.

A plate of three figures drawn the way a mid-century tube manual drew them,
all from one model of a medium-mu triode: FIG. 1 the electrode assembly with
its front quarter cut away, inked as a technical drawing (a VecView scene of
solids turned on a lathe, sections blacked in or hatched, seams and hidden
edges left out); FIG. 2 the average plate characteristics on graph paper,
with a load line through the operating point; FIG. 3 the mutual
characteristics, with the transconductance constructed graphically there.

The look is `vintage_style.md` beside this script: one warm ink on cream paper,
template lettering, graph-paper rules instead of ticks, curves labelled where
they run. Nothing in the script picks a font, a weight, or a panel-letter
format; the style does.

The model is Child's three-halves-power law, I_b = K (E_b + mu E_c)^(3/2) while
E_b + mu E_c > 0, with amplification factor mu = 20 and perveance
K = 1.05e-5 A/V^1.5, close to a common receiving triode. The load line runs
through the rated point E_b = 250 V, E_c = -8 V. The points marked as measured
in FIG. 3 are simulated: the model with 2 % scatter, seeded.

Usage:
    python examples/vacuum_triode.py     # requires vecview
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import svg
import vecview
from matplotlib.ticker import MultipleLocator
from vecview import outlines

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

THEME = load_theme(Path(__file__).with_name("vintage_style.md"))
plt.rcParams.update(theme_rc(THEME))

INK, PAPER, RULE, NEUTRAL = (THEME.color[name] for name in ("ink", "paper", "rule", "neutral"))
PEN = dict(stroke=INK, stroke_width=THEME.px("line.data"), stroke_linejoin="round")
FINE = dict(stroke=INK, stroke_width=THEME.px("line.hairline"))
LETTERING = THEME.vecview_text("label")

MU = 20.0  # amplification factor
K = 1.05e-5  # perveance, A/V^1.5
E_C_Q, E_B_Q = -8.0, 250.0  # the rated operating point
R_L = 10e3  # load resistance, ohms
P_MAX = 2.5  # rated plate dissipation, W
SEED = 1950


# --- the model ------------------------------------------------------------------


def plate_current(e_b: np.ndarray | float, e_c: np.ndarray | float) -> np.ndarray:
    """Child's law in amperes: zero below cutoff, where the grid wins."""
    return K * np.clip(np.asarray(e_b) + MU * np.asarray(e_c), 0.0, None) ** 1.5


I_Q = float(plate_current(E_B_Q, E_C_Q))
E_BB = E_B_Q + I_Q * R_L  # the supply that puts the load line through the rated point
G_M = 1.5 * K * MU * np.sqrt(E_B_Q + MU * E_C_Q)  # dI_b/dE_c at the operating point, A/V


# --- FIG. 1: the electrode assembly ------------------------------------------------

CAMERA = vecview.OrthographicCamera(azim_deg=-55.0, elev_deg=18.0, scale=4.0)
CUT = (CAMERA.azim_deg + 40.0, CAMERA.azim_deg + 310.0)  # the quarter facing us is cut away
OPEN = CAMERA.azim_deg - 5.0  # the middle of the opening


def dome(r_out: float, r_in: float, z0: float, n: int = 24) -> np.ndarray:
    """The (r, z) profile of a bulb wall: straight from z = 0, then a hemisphere."""
    t = np.radians(np.linspace(0.0, 90.0, n))
    outer = np.column_stack([r_out * np.cos(t), z0 + r_out * np.sin(t)])
    inner = np.column_stack([r_in * np.cos(t), z0 + r_in * np.sin(t)])[::-1]
    return np.vstack([[(r_in, 0.0), (r_out, 0.0)], outer, inner])


def turned(scene: vecview.Scene, name: str, profile, section: str) -> None:
    """A part turned on a lathe with its front quarter cut away: surface, section, outline."""
    body = vecview.revolve(profile, sweep_deg=CUT)
    cut = [face for face in body if face.name in ("start", "end")]
    surface = [face for face in body if face.name not in ("start", "end")]
    scene.faces(20, surface, fill=PAPER, id=f"{name}-surface")
    scene.faces(20, cut, fill=section, id=f"{name}-section")
    scene.line_art(20, body, id=name, class_="outline", **PEN)


def at_angle(r: float, deg: float, z: float) -> tuple[float, float, float]:
    t = np.radians(deg)
    return (r * float(np.cos(t)), r * float(np.sin(t)), z)


def kept(deg: float) -> bool:
    """Whether an angle about the axis lies in the part that is not cut away."""
    return (deg - CUT[0]) % 360.0 <= CUT[1] - CUT[0]


def triode_drawing() -> vecview.Scene:
    """The mount of a triode: cathode, grid, plate, mica spacers, bulb, and base.

    Dimensions in millimetres, drawn larger than life. Thin metal sections are
    blacked in, as a draughtsman does below a pen width; the thick base is
    hatched.
    """
    scene = vecview.Scene(CAMERA, pad=2.0)
    scene.add_def(
        svg.Pattern(
            id="hatch",
            width=2.2,
            height=2.2,
            patternUnits="userSpaceOnUse",
            patternTransform=[svg.Rotate(45)],
            elements=[
                svg.Rect(width=2.2, height=2.2, fill=PAPER),
                svg.Line(x1=0, y1=0, x2=0, y2=2.2, **FINE),
            ],
        )
    )

    turned(scene, "base", [(0, -11), (11.6, -11), (13.2, -9.4), (13.2, 0), (0, 0)], "url(#hatch)")
    # Glass, whole and clear: only its outline, so everything inside shows through.
    bulb = vecview.revolve(dome(12.8, 12.2, 42.0))
    scene.line_art(20, bulb, id="bulb", class_="outline", **PEN)
    for name, z in (("lower-mica", 6.0), ("upper-mica", 34.0)):
        turned(scene, name, outlines.rect((0.0, z), (10.4, z + 0.6)), INK)
    turned(scene, "plate", outlines.rect((5.0, 8.5), (5.35, 31.5)), INK)
    turned(scene, "cathode", outlines.rect((0.8, 4.0), (1.05, 37.0)), INK)

    # The heater, a folded wire inside the cathode sleeve.
    heater = [at_angle(0.35, OPEN - 90, 3.0), at_angle(0.35, OPEN - 90, 35.5)]
    heater += [at_angle(0.35, OPEN + 90, 35.5), at_angle(0.35, OPEN + 90, 3.0)]
    scene.tube(
        20, heater, 0.12, fill=PAPER, stroke=INK, stroke_width=FINE["stroke_width"], id="heater"
    )

    # The grid: a helix wound on two side rods, cut where the quarter is.
    for deg in (CUT[0] + 60.0, CUT[0] + 240.0):
        foot, top = at_angle(2.7, deg, 5.0), at_angle(2.7, deg, 35.0)
        scene.cylinder(20, foot, top, 0.22, fill=PAPER, id=f"grid-rod-{deg:.0f}", **PEN)
    helix = vecview.helix((0, 0, 8.5), (0, 0, 1), 2.7, 1.3, 23.0 / 1.3, n_per_turn=36)
    inside = np.array([kept(a) for a in np.degrees(np.arctan2(helix[:, 1], helix[:, 0]))])
    breaks = np.flatnonzero(np.diff(inside.astype(int))) + 1
    turns = [
        run
        for run, keep in zip(np.split(helix, breaks), np.split(inside, breaks), strict=True)
        if keep[0] and len(run) > 1
    ]
    for k, run in enumerate(turns):
        scene.tube(
            20, run, 0.1, fill=PAPER, stroke=INK, stroke_width=FINE["stroke_width"], id=f"grid-{k}"
        )

    # The base pins and the keyed centre post, whole: they are not sectioned.
    for k, deg in enumerate(CAMERA.azim_deg + np.array([-110.0, -40.0, 40.0, 110.0])):
        scene.cylinder(
            20,
            at_angle(8.0, deg, -11),
            at_angle(8.0, deg, -18),
            0.9,
            fill=PAPER,
            id=f"pin-{k}",
            **PEN,
        )
    scene.cylinder(20, (0, 0, -11), (0, 0, -16), 2.6, fill=PAPER, id="key", **PEN)
    scene.sort_by_depth(20)

    scene.polyline(30, [(0, 0, -21), (0, 0, 58)], id="axis", stroke_dasharray="9 2 1.5 2", **FINE)
    callouts(scene)
    return scene


def callouts(scene: vecview.Scene) -> None:
    """Leaders from a dot on each part to lettering in a column either side."""
    right = np.asarray(CAMERA.screen_basis()[0])  # the world direction across the page
    up = np.array([0.0, 0.0, 1.0])
    parts = [  # (lettering, a point on the part, side: -1 left, +1 right, height of the lettering)
        ("BULB", at_angle(12.8, CAMERA.azim_deg + 90, 36.0), 1, 50.0),  # its outline
        ("GRID", at_angle(2.7, CUT[0] + 60, 30.0), 1, 40.0),
        ("HEATER", at_angle(0.35, OPEN + 90, 33.0), 1, 30.0),
        ("BASE", at_angle(13.2, CUT[0] - 10, -4.0), 1, -2.0),
        ("PIN", at_angle(8.0, CAMERA.azim_deg + 40.0, -16.0), 1, -14.0),
        ("CATHODE", at_angle(1.05, CUT[1] - 20, 36.6), -1, 44.0),
        ("PLATE", at_angle(5.35, CUT[1] - 25, 22.0), -1, 28.0),
        ("MICA SPACER", at_angle(9.0, CUT[1] - 10, 6.6), -1, 10.0),
    ]
    for name, point, side, height in parts:
        end = side * 19.0 * right + height * up
        knee = end - side * 3.0 * right
        slug = name.lower().replace(" ", "-")
        scene.sphere(30, point, 0.45, fill=INK, id=f"dot-{slug}")
        scene.polyline(30, [point, knee, end], id=f"leader-{slug}", **FINE)
        anchor = "start" if side > 0 else "end"
        scene.text(
            30,
            end,
            name,
            dx=side * 2.0,
            dy=0.35 * LETTERING["size"],
            text_anchor=anchor,
            id=f"callout-{slug}",
            **LETTERING,
        )


# --- FIG. 2 and FIG. 3: the characteristics --------------------------------------


def graph_paper(
    ax: plt.Axes, x: tuple[float, float, float, float], y: tuple[float, float, float, float]
) -> None:
    """Limits and rules: ``(low, high, major, minor)`` along each axis."""
    for axis, (low, high, major, minor), limit in (
        (ax.xaxis, x, ax.set_xlim),
        (ax.yaxis, y, ax.set_ylim),
    ):
        limit(low, high)
        axis.set_major_locator(MultipleLocator(major))
        axis.set_minor_locator(MultipleLocator(minor))
    ax.grid(which="minor", lw=THEME.line.hairline)


def on_curve(ax: plt.Axes, x: float, y: float, text: str, **kwargs) -> None:
    """Lettering set on a curve, the paper showing round it so the line breaks for it."""
    box = dict(boxstyle="square,pad=0.15", facecolor=PAPER, edgecolor="none")
    ax.text(x, y, text, ha="center", va="center", bbox=box, **kwargs)


def plot_plate_characteristics(ax: plt.Axes) -> None:
    """Plate current against plate voltage, a curve per grid voltage, with the load line."""
    e_b = np.linspace(0.0, 400.0, 801)
    for e_c in range(0, -20, -2):
        i_b = 1e3 * plate_current(e_b, e_c)
        ax.plot(e_b, i_b, color=INK, gid=f"plate-curve-{-e_c}")
        # Letter the curve where it crosses 17 mA, or near its end if it stays below.
        crossing = (0.017 / K) ** (2 / 3) - MU * e_c
        x = crossing if crossing < 380 else 384.0
        on_curve(
            ax,
            x,
            1e3 * float(plate_current(x, e_c)),
            "$E_c = 0$" if e_c == 0 else f"\N{MINUS SIGN}{-e_c}",
        )

    ax.plot(
        [0, E_BB],
        [1e3 * E_BB / R_L, 0],
        color=INK,
        lw=THEME.line.hairline * 2.5,
        ls=(0, (6, 2)),
        gid="load-line",
    )
    slope = np.degrees(np.arctan2(-1e3 * E_BB / R_L, E_BB))
    on_curve(
        ax,
        295,  # below Q, where the line runs clear
        1e3 * (E_BB - 295) / R_L,
        rf"$R_L$ = {R_L / 1e3:.0f} k$\Omega$",
        rotation=slope,
        transform_rotates_text=True,
        rotation_mode="anchor",
    )
    e = np.linspace(130.0, 400.0, 200)
    ax.plot(
        e,
        1e3 * P_MAX / e,
        color=NEUTRAL,
        lw=THEME.line.hairline * 2.5,
        ls=(0, (1, 1.6)),
        gid="dissipation",
    )
    on_curve(ax, 352, 1e3 * P_MAX / 352, f"{P_MAX:g} W", color=NEUTRAL)
    ax.plot(E_B_Q, 1e3 * I_Q, "o", mfc=PAPER, mec=INK, mew=THEME.line.data, gid="operating-point")
    ax.annotate(
        "Q", (E_B_Q, 1e3 * I_Q), xytext=(-4, 1), textcoords="offset points", ha="right", va="center"
    )

    graph_paper(ax, (0, 400, 50, 10), (0, 20, 2, 0.5))
    ax.set_xlabel(r"PLATE VOLTAGE $E_b$ — VOLTS")
    ax.set_ylabel(r"PLATE CURRENT $I_b$ — MILLIAMPERES")


def plot_mutual_characteristics(ax: plt.Axes) -> None:
    """Plate current against grid voltage at fixed plate voltages; g_m built at Q."""
    e_c = np.linspace(-24.0, 0.0, 481)
    for e_b in (100, 150, 200, 250, 300):
        ax.plot(e_c, 1e3 * plate_current(e_b, e_c), color=INK, gid=f"mutual-curve-{e_b}")
        # Letter the curve where it crosses 18.5 mA, or near its end if it stays below.
        crossing = ((0.0185 / K) ** (2 / 3) - e_b) / MU
        x = crossing if crossing < -0.8 else -0.8
        on_curve(ax, x, 1e3 * float(plate_current(e_b, x)), f"{e_b}")
        if e_b == 300:  # the family's heading, read on along the row of numbers
            ax.text(x - 0.9, 18.5, "$E_b$ =", ha="right", va="center")

    rng = np.random.default_rng(SEED)
    grid_volts = np.arange(-12.5, 0.0, 1.0)
    measured = (
        1e3 * plate_current(E_B_Q, grid_volts) * (1 + 0.02 * rng.standard_normal(grid_volts.size))
    )
    ax.plot(
        grid_volts, measured, "o", mfc=PAPER, mec=INK, mew=0.6 * THEME.line.data, gid="measured"
    )

    # The tangent at Q, and the triangle that reads its slope off the paper.
    dx, gm = 2.0, 1e3 * G_M  # volts, mA per volt
    i_q = 1e3 * I_Q
    ax.plot(
        [E_C_Q - 1.6 * dx, E_C_Q + 1.6 * dx],
        [i_q - 1.6 * dx * gm, i_q + 1.6 * dx * gm],
        color=NEUTRAL,
        lw=THEME.line.hairline * 2.5,
        gid="tangent",
    )
    corner = (E_C_Q + dx / 2, i_q - dx / 2 * gm)
    ax.plot(
        [E_C_Q - dx / 2, corner[0], corner[0]],
        [corner[1], corner[1], i_q + dx / 2 * gm],
        color=INK,
        lw=THEME.line.hairline * 2.5,
        gid="slope-triangle",
    )
    ax.text(E_C_Q, corner[1] - 0.5, r"$\Delta E_c$", ha="center", va="top")
    ax.text(corner[0] + 0.35, i_q, r"$\Delta I_b$", ha="left", va="center")
    ax.plot(E_C_Q, i_q, "o", mfc=PAPER, mec=INK, mew=THEME.line.data, gid="operating-point")
    ax.annotate(
        "Q", (E_C_Q, i_q), xytext=(-4, 1), textcoords="offset points", ha="right", va="center"
    )
    ax.text(-23, 17.6, rf"$g_m = \Delta I_b / \Delta E_c$ = {gm:.1f} mA/V", va="top")

    graph_paper(ax, (-24, 0, 4, 1), (0, 20, 2, 0.5))
    ax.set_xlabel(r"GRID VOLTAGE $E_c$ — VOLTS")
    ax.set_ylabel(r"PLATE CURRENT $I_b$ — MILLIAMPERES")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="120mm", theme=THEME, background=PAPER)
    panels = fig.grid(
        [["drawing", "plate"], ["drawing", "mutual"]],
        width_ratios=(1.0, 1.05),
        margins=("8mm", "4mm", "11mm", "4mm"),  # top, right, bottom, left
        gap=("17mm", "19mm"),  # between rows, between columns
    )
    panels["drawing"].add(triode_drawing(), id="triode-drawing", fit="none")
    for name, plot in (
        ("plate", plot_plate_characteristics),
        ("mutual", plot_mutual_characteristics),
    ):
        mpl_fig, ax = panels[name].subplots()
        plot(ax)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")
    for number, panel in zip("123", panels.values(), strict=True):
        fig.label(number, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"vacuum_triode{suffix}")
    print(f"wrote {OUT / 'vacuum_triode.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
