"""Reaction pathways on the Müller-Brown potential-energy surface.

The Müller-Brown surface is the standard two-dimensional benchmark for
reaction-path methods: three minima joined by two saddle points. Everything
plotted is computed here from the analytic potential, read as kJ/mol over
coordinates in Å. The stationary points are found by Newton's method, the
minimum-energy path by the string method, and the rate constants by harmonic
transition-state theory for a particle of mass 1 u.

a, a VecView scene: the surface as energy-coloured quads, levelled off at
-20 kJ/mol so the wells read as depressions, over a Matplotlib contour map lying
in its floor plane; the path is drawn on both, with VecTeX labels pinned to the
stationary points. b, the same map from above, in the same colours. c, the
energy along the path, with the two forward barriers. d, Arrhenius plots of the
four rate constants.

Usage:
    python examples/energy_landscape.py     # requires vecview and TeX
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vectex
import vecview
from matplotlib.colors import LinearSegmentedColormap, Normalize

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

THEME = load_theme("nature")
plt.rcParams.update(theme_rc(THEME))

CAP = -20.0  # kJ/mol; the surface is drawn flat above this, a little over TS1
PALE = "#e9ecf0"
# Viridis, fading to pale over its top quarter so the high ground recedes.
CMAP = LinearSegmentedColormap.from_list(
    "pes",
    [
        *zip(np.linspace(0, 0.75, 8), plt.get_cmap("viridis")(np.linspace(0, 0.9, 8)), strict=True),
        (1, PALE),
    ],
).with_extremes(over=PALE)
NORM = Normalize(-150, CAP)  # kJ/mol; the colour scale shared by a and b
PATH = "#e4572e"  # the minimum-energy path, everywhere
INK = "#262626"
GREY = "#8c8c8c"

XLIM, YLIM = (-1.2, 1.0), (-0.3, 1.8)  # Å
AZIM, ELEV = -100.0, 40.0
NAMES = ("R", "TS1", "I", "TS2", "P")
# Label offsets in pt, and alignment, on the map and on the profile.
MAP_LABELS = dict(R=(4, 3, "left"), TS1=(-4, -4, "right"), I=(0, 6, "center"))
MAP_LABELS |= dict(TS2=(4, 3, "left"), P=(4, 3, "left"))
PROFILE_LABELS = dict(R=(4, -9, "left"), TS1=(0, 4, "center"), I=(0, -9, "center"))
PROFILE_LABELS |= dict(TS2=(0, 4, "center"), P=(-4, -9, "right"))
GUESSES = ((-0.56, 1.44), (-0.82, 0.62), (-0.05, 0.47), (0.21, 0.29), (0.62, 0.03))

# Müller-Brown: V = sum_k A_k exp(a_k dx^2 + b_k dx dy + c_k dy^2), dx = x - x0_k.
MB_A = np.array([-200.0, -100.0, -170.0, 15.0])
MB_a = np.array([-1.0, -1.0, -6.5, 0.7])
MB_b = np.array([0.0, 0.0, 11.0, 0.6])
MB_c = np.array([-10.0, -10.0, -6.5, 0.7])
MB_X0 = np.array([1.0, 0.0, -0.5, -1.0])
MB_Y0 = np.array([0.0, 0.5, 1.5, 1.0])

R_GAS = 8.314462618e-3  # kJ/(mol K)


# --- physics --------------------------------------------------------------------


def _terms(x, y):
    dx = np.asarray(x, float)[..., None] - MB_X0
    dy = np.asarray(y, float)[..., None] - MB_Y0
    return dx, dy, MB_A * np.exp(MB_a * dx**2 + MB_b * dx * dy + MB_c * dy**2)


def energy(x, y) -> np.ndarray:
    """The Müller-Brown potential, in kJ/mol."""
    return _terms(x, y)[2].sum(-1)


def gradient(x, y) -> np.ndarray:
    """Its analytic gradient, with the two components on the last axis."""
    dx, dy, t = _terms(x, y)
    return np.stack(
        [(t * (2 * MB_a * dx + MB_b * dy)).sum(-1), (t * (MB_b * dx + 2 * MB_c * dy)).sum(-1)], -1
    )


def hessian(p: np.ndarray, h: float = 1e-5) -> np.ndarray:
    """The Hessian at ``p`` by central differences of the analytic gradient."""
    cols = [(gradient(*(p + e)) - gradient(*(p - e))) / (2 * h) for e in np.eye(2) * h]
    hess = np.column_stack(cols)
    return (hess + hess.T) / 2


def stationary_point(guess) -> np.ndarray:
    """Newton's method on the gradient: converges to minima and saddles alike."""
    p = np.asarray(guess, float)
    for _ in range(30):
        p = p - np.linalg.solve(hessian(p), gradient(*p))
    return p


def arc_length(path: np.ndarray) -> np.ndarray:
    """Cumulative arc length along ``path``, from 0 at its start."""
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]


def string_method(start, end, images: int = 80, steps: int = 6000, dt: float = 1e-4):
    """The minimum-energy path from ``start`` to ``end`` (E, Ren, Vanden-Eijnden 2007).

    Each iteration moves every image downhill, then redistributes the images at
    equal arc length, which removes the force component along the string.
    """
    s = np.linspace(0, 1, images)[:, None]
    path = (1 - s) * np.asarray(start) + s * np.asarray(end)
    for _ in range(steps):
        path[1:-1] -= dt * gradient(path[1:-1, 0], path[1:-1, 1])
        arc = arc_length(path)
        target = np.linspace(0, arc[-1], images)
        path = np.column_stack([np.interp(target, arc, path[:, i]) for i in (0, 1)])
    return path


def htst_rate(minimum: np.ndarray, saddle: np.ndarray, temperature: np.ndarray, mass: float = 1.0):
    """Harmonic TST (Vineyard): k = prod(nu_min) / prod(nu_saddle, stable) exp(-dE/RT).

    Curvatures in kJ/mol/Å^2 over a mass in u give omega^2 in units of 1e26 s^-2.
    """

    def nu(curvature):
        return np.sqrt(np.abs(curvature) * 1e26 / mass) / (2 * np.pi)

    lam_min = np.linalg.eigvalsh(hessian(minimum))
    lam_ts = np.linalg.eigvalsh(hessian(saddle))
    prefactor = nu(lam_min).prod() / nu(lam_ts[1])
    barrier = energy(*saddle) - energy(*minimum)
    return prefactor * np.exp(-barrier / (R_GAS * temperature))


def solve_landscape() -> dict:
    """Stationary points, the path between R and P, and the energy along it."""
    points = dict(zip(NAMES, (stationary_point(g) for g in GUESSES), strict=True))
    path = string_method(points["R"], points["P"])
    arc = arc_length(path)
    return dict(points=points, path=path, s=arc / arc[-1], v=energy(*path.T))


# --- panel a: the surface -------------------------------------------------------

Z_SCALE = 0.003  # world units per kJ/mol
FLOOR = Z_SCALE * -150 - 0.35  # the contour map, a modest gap below the deepest well
MESH = dict(stroke=INK, stroke_width=0.4, stroke_opacity=0.3)


def height(v: np.ndarray, soft: float = 6.0) -> np.ndarray:
    """World height of energy ``v``, levelled off smoothly at CAP."""
    return Z_SCALE * (CAP - soft * np.logaddexp(0, (CAP - v) / soft))


def surface_color(v: float, normal: np.ndarray, light=(-0.3, -0.5, 0.8)) -> str:
    """The map's colour at ``v`` under a soft Lambertian light."""
    rgb = np.array(CMAP(NORM(v))[:3])
    rgb *= 0.7 + 0.3 * max(float(np.dot(normal, light)), 0.0)
    return "#" + "".join(f"{round(255 * c):02x}" for c in rgb)


def label_color(v: float) -> str:
    """Ink over the light end of the colour scale, white over the dark end."""
    r, g, b, _ = CMAP(NORM(v))
    return INK if 0.30 * r + 0.59 * g + 0.11 * b > 0.45 else "white"


def floor_map(land: dict) -> plt.Figure:
    """The filled contours alone, frameless and transparent, sized like the floor."""
    mpl_fig = plt.figure(figsize=(XLIM[1] - XLIM[0], YLIM[1] - YLIM[0]))
    ax = mpl_fig.add_axes((0, 0, 1, 1))
    contour_map(ax, land, annotate=False)
    ax.set_axis_off()
    mpl_fig.patch.set_alpha(0.0)
    return mpl_fig


def surface_scene(land: dict, labels: dict) -> vecview.Scene:
    """The surface, capped at CAP, above its own contour map; the path on both."""
    cam = vecview.OrthographicCamera(azim_deg=AZIM, elev_deg=ELEV, scale=110.0)
    scene = vecview.Scene(cam, pad=0.05)

    # The floor's content +x runs along world +x and its +y (down) along world -y,
    # both projecting right- and downward, so the map lies in it unmirrored.
    (x0, x1), (y0, y1) = XLIM, YLIM
    scene.plane(5, (x0, y1, FLOOR), (x1 - x0, 0, 0), (0, y0 - y1, 0), id="floor-map")
    floor_path = np.column_stack([land["path"], np.full(len(land["path"]), FLOOR)])
    scene.polyline(6, floor_path, stroke=PATH, stroke_width=1.0, id="mep-floor", class_="mep")

    gx, gy = np.meshgrid(np.linspace(*XLIM, 56), np.linspace(*YLIM, 53), indexing="ij")
    grid = np.stack([gx, gy, height(energy(gx, gy))], axis=-1)
    scene.sort_by_depth(10)
    for face in vecview.surface_faces(*grid.transpose(2, 0, 1)):
        fill = surface_color(face.points[:, 2].mean() / Z_SCALE, vecview.unit(face.normal))
        scene.polygon(10, face.points, fill=fill, stroke=fill, stroke_width=0.5, class_="pes")

    # A light mesh along every fifth grid line, drawn over the surface.
    lift = 0.005 * cam.view
    for k, line in enumerate([*grid[::5], *grid[:, ::5].transpose(1, 0, 2)]):
        scene.polyline(11, line + lift, id=f"mesh-{k}", class_="mesh", **MESH)
    ridge = np.column_stack([land["path"], height(land["v"])]) + 2 * lift
    scene.tube(12, ridge, 0.012, fill=PATH, chunk=2, id="mep-surface", class_="mep")

    for name, p in land["points"].items():
        at = np.r_[p, height(energy(*p))] + 2 * lift
        scene.sphere(12, at, 0.028, fill="white", stroke=INK, stroke_width=0.6, id=f"point-{name}")
        w, h = labels[name].width_px, labels[name].height_px
        scene.slot(20, at, w, h, align="south", dy=-4, id=f"label-{name}")
    return scene


# --- panels b, c and d: the plots -----------------------------------------------


def contour_map(ax: plt.Axes, land: dict, annotate: bool = True) -> None:
    """Filled contours every 10 kJ/mol; annotated with the path and stationary points."""
    gx, gy = np.meshgrid(np.linspace(*XLIM, 120), np.linspace(*YLIM, 115))
    v = energy(gx, gy)
    levels = np.arange(-150, CAP + 1, 10)
    ax.contourf(gx, gy, v, levels=levels, cmap=CMAP, norm=NORM, extend="max")
    ax.set(xlim=XLIM, ylim=YLIM)
    if not annotate:
        return
    ax.contour(
        gx, gy, v, levels=levels, colors="white", linewidths=0.3, linestyles="solid", alpha=0.6
    )
    ax.plot(*land["path"].T, color=PATH)
    for name, p in land["points"].items():
        ax.plot(*p, "o", ms=3.0, mfc="white", mec=INK, mew=0.5, zorder=3)
        dx, dy, ha = MAP_LABELS[name]
        ax.annotate(
            name,
            p,
            xytext=(dx, dy),
            textcoords="offset points",
            ha=ha,
            va="center",
            color=label_color(energy(*p)),
        )
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([0, 1])
    ax.set_xlabel(r"$x$ (Å)")
    ax.set_ylabel(r"$y$ (Å)")


def plot_profile(ax: plt.Axes, land: dict) -> None:
    """Energy along the path, with each forward barrier as a dimension arrow."""
    ax.plot(land["s"], land["v"], color=PATH)
    pts = land["points"]
    s = {n: land["s"][np.argmin(np.linalg.norm(land["path"] - p, axis=1))] for n, p in pts.items()}
    e = {n: energy(*p) for n, p in pts.items()}
    for name, (dx, dy, ha) in PROFILE_LABELS.items():
        ax.plot(s[name], e[name], "o", ms=3.0, mfc="white", mec=INK, mew=0.5, zorder=3)
        ax.annotate(name, (s[name], e[name]), (dx, dy), textcoords="offset points", ha=ha)
    for k, (lo, hi), x in ((1, ("R", "TS1"), 0.06), (2, ("I", "TS2"), 0.93)):
        ax.hlines([e[lo], e[hi]], [s[lo], s[hi]], x, color=GREY, lw=0.4, ls=(0, (1, 1.5)))
        arrow = dict(arrowstyle="<|-|>,head_length=0.25,head_width=0.12", lw=0.5, color=INK)
        ax.annotate("", (x, e[hi]), (x, e[lo]), arrowprops=dict(arrow, shrinkA=0, shrinkB=0))
        text = rf"$\Delta E^\ddagger_{k} = {e[hi] - e[lo]:.1f}$ kJ mol$^{{-1}}$"
        if k == 1:
            ax.text(x - 0.04, e[hi] + 5, text, va="bottom")
        else:
            ax.text(x + 0.06, e[hi] + 13, text, ha="right", va="bottom")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set(xlim=(0, 1), ylim=(-160, -20), xticks=[0, 0.5, 1], yticks=[-150, -100, -50])
    ax.set_xlabel("Reaction coordinate (normalized arc length)")
    ax.set_ylabel(r"$V$ (kJ mol$^{-1}$)")


def plot_rates(ax: plt.Axes, land: dict) -> None:
    """Harmonic-TST rate constants: R -> I limits the rate at every temperature."""
    pts = land["points"]
    kelvin = np.linspace(250, 1000, 200)
    steps = (  # label, from, saddle, colour, line style, label offset in pt
        ("1", "R", "TS1", INK, "-", -7),
        ("-1", "I", "TS1", INK, "--", -7),
        ("2", "I", "TS2", GREY, "-", 4),
        ("-2", "P", "TS2", GREY, "--", 7),
    )
    for name, start, saddle, color, ls, dy in steps:
        log_k = np.log10(htst_rate(pts[start], pts[saddle], kelvin))
        ax.plot(1000 / kelvin, log_k, color=color, ls=ls)
        at = np.argmin(np.abs(1000 / kelvin - 3.5))
        ax.annotate(
            rf"$k_{{{name}}}$",
            (3.5, log_k[at]),
            xytext=(0, dy),
            textcoords="offset points",
            ha="center",
            va="center",
            color=color,
        )
    ax.spines[["top", "right"]].set_visible(False)
    ax.set(xlim=(1, 4), xticks=[1, 2, 3, 4], yticks=[-5, 0, 5, 10])
    ax.set_xlabel(r"$1000/T$ (K$^{-1}$)")
    ax.set_ylabel(r"$\log_{10}\,k$ (s$^{-1}$)")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="128mm", theme=THEME)
    panels = fig.grid(
        [["surface", "surface", "map"], ["profile", "profile", "rates"]],
        width_ratios=(1, 1, 1.45),
        height_ratios=(1.5, 1),
        margins=("8mm", "5mm", "9mm", "13mm"),  # top, right, bottom, left
        gap=("16mm", "15mm"),  # between rows, between columns
    )
    land = solve_landscape()

    labels = {
        name: vectex.render(name, **THEME.vectex() | {"color": label_color(energy(*p))})
        for name, p in land["points"].items()
    }
    panels["surface"].add(surface_scene(land, labels), id="surface-scene")
    fig.fill_plane("floor-map", floor_map(land))
    for name in NAMES:
        fig.fill_slot(f"label-{name}", labels[name])

    for name, plot in (("map", contour_map), ("profile", plot_profile), ("rates", plot_rates)):
        mpl_fig, ax = panels[name].subplots()
        plot(ax, land)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    for letter, panel in zip("abcd", panels.values(), strict=True):
        fig.label(letter, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"energy_landscape{suffix}")
    print(f"wrote {OUT / 'energy_landscape.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
