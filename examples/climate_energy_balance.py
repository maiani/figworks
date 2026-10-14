"""Earth's energy balance, the ice-albedo feedback, and the response to CO2.

A Nature double-column figure. A VecView globe -- polar ice, a night side,
sunlight arriving and partly reflected, infrared leaving -- with VecTeX labels
pinned upright, beside three Matplotlib panels: the zonal energy budget and
temperature of a diffusive Budyko-Sellers model, the hysteresis of its ice edge
as the Sun brightens and dims, and the global warming of a two-layer ocean
model after a CO2 doubling. Orange is sunlight, vermillion infrared, blue ice.

Everything is computed here; nothing is measured. The energy-balance model is

    0 = (S0/4) s(x) (1 - alpha) - (A + B T) + D d/dx[(1 - x^2) dT/dx],  x = sin(lat),

solved by finite volumes for each ice-edge position, which gives the whole
branch of steady states, unstable ones included (North 1975). The ocean albedo
rises toward the poles with the sun's slant (its P2 term); A = 210 W m^-2
puts today's ice edge near 68 degrees for S0 = 1361 W m^-2. The two-layer
model (Held et al. 2010) uses typical CMIP5 parameters, stepped exactly
through the eigenmodes of its linear system.

Usage:
    python examples/climate_energy_balance.py     # requires vecview and TeX
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

INK = "#262626"
GREY = "#9a9a9a"
SUN = "#e69f00"  # Okabe-Ito orange: shortwave
INFRARED = "#d55e00"  # Okabe-Ito vermillion: longwave
ICE = "#3d8fc6"  # ice edge and ice-covered states
ICE_FILL = "#deedf8"
OCEAN = dict(fill="#2d5f8b", highlight="#8db9dc")
ARROW = dict(arrowstyle="-|>", lw=0.5, color=INK, mutation_scale=5, shrinkA=1, shrinkB=1)

# --- energy-balance model ---
S0 = 1361.0  # W m^-2
Q0 = S0 / 4
A, B = 210.0, 2.09  # OLR = A + B T, W m^-2 and W m^-2 K^-1, T in degrees C
D = 0.55  # W m^-2 K^-1
ALBEDO_ICE, ALBEDO_OCEAN, ALBEDO_SLANT = 0.62, 0.30, 0.078
T_ICE = -10.0  # C
N = 200
EDGES = np.linspace(0, 1, N + 1)
X = (EDGES[:-1] + EDGES[1:]) / 2  # cell centres in x = sin(latitude)
P2 = (3 * X**2 - 1) / 2

# --- two-layer model ---
F_2X = 5.35 * np.log(2)  # W m^-2
LAMBDA, GAMMA = 1.2, 0.73  # feedback and deep-ocean uptake, W m^-2 K^-1
C_MIX, C_DEEP = 7.3, 106.0  # heat capacities, W yr m^-2 K^-1
RESPONSE = np.array(
    [[-(LAMBDA + GAMMA) / C_MIX, GAMMA / C_MIX], [GAMMA / C_DEEP, -GAMMA / C_DEEP]]
)  # d/dt (T, T_deep) = RESPONSE (T, T_deep) + (F / C_MIX, 0)


# --- physics --------------------------------------------------------------------


def insolation() -> np.ndarray:
    """Annual-mean insolation over its global mean, s(x) = 1 - 0.482 P2(x)."""
    return 1 - 0.482 * P2


def coalbedo(edge: float) -> np.ndarray:
    """1 - albedo per cell, ice poleward of x = edge, cells cut by it averaged."""
    ice = np.clip((EDGES[1:] - edge) * N, 0, 1)
    return (1 - ALBEDO_OCEAN - ALBEDO_SLANT * P2) * (1 - ice) + (1 - ALBEDO_ICE) * ice


def inverse_operator() -> np.ndarray:
    """(B - D L)^-1, L the finite-volume d/dx (1 - x^2) d/dx with no flux at 0 and 1."""
    k = (1 - EDGES[1:-1] ** 2) * N**2
    i = np.arange(N - 1)
    lap = np.zeros((N, N))
    lap[i, i] -= k
    lap[i + 1, i + 1] -= k
    lap[i, i + 1] += k
    lap[i + 1, i] += k
    return np.linalg.inv(B * np.eye(N) - D * lap)


INV = inverse_operator()


def steady_state(edge: float) -> tuple[float, np.ndarray]:
    """The insolation Q at which the ice edge sits at x = edge, and the temperatures.

    T = Q u - v is linear in Q for a fixed albedo, so T(edge) = T_ICE fixes Q.
    """
    u, v = INV @ (insolation() * coalbedo(edge)), INV @ np.full(N, A)
    q = (T_ICE + np.interp(edge, X, v)) / np.interp(edge, X, u)
    return q, q * u - v


def present_edge() -> float:
    """The ice edge today, on the stable branch near the pole, by bisection."""
    lo, hi = 0.6, 0.97
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if steady_state(mid)[0] < Q0 else (lo, mid)
    return (lo + hi) / 2


def two_layer(forcing: np.ndarray, dt: float) -> np.ndarray:
    """Mixed-layer and deep-ocean temperatures, exact for forcing constant over each step."""
    rates, modes = (np.real(a) for a in np.linalg.eig(RESPONSE))  # both real and negative
    step = modes @ np.diag(np.exp(rates * dt)) @ np.linalg.inv(modes)
    kick = np.linalg.solve(RESPONSE, step - np.eye(2)) @ np.array([1 / C_MIX, 0.0])
    t = np.zeros((forcing.size + 1, 2))
    for n, f in enumerate(forcing):
        t[n + 1] = step @ t[n] + kick * f
    return t


def timescales() -> np.ndarray:
    """Fast and slow e-folding times of the two-layer model, in years."""
    return np.sort(-1 / np.real(np.linalg.eigvals(RESPONSE)))


# --- panel a: the globe ---------------------------------------------------------


def unit(v) -> np.ndarray:
    return np.asarray(v, dtype=float) / np.linalg.norm(v)


def night_side(view: np.ndarray, sun: np.ndarray) -> np.ndarray:
    """The visible night hemisphere: the front half of the terminator, back along the limb."""
    e = unit(np.cross(sun, view))
    front = np.cross(e, sun)
    front = front if front @ view > 0 else -front
    dark = np.cross(view, e)
    dark = dark if dark @ sun < 0 else -dark
    t = np.linspace(0, np.pi, 60)[:, None]
    terminator = np.cos(t) * e + np.sin(t) * front
    limb = np.cos(t[::-1]) * e + np.sin(t[::-1]) * dark
    return np.vstack([terminator, limb[1:-1]])


def globe_scene(labels: dict[str, vectex.VectexFragment], edge: float) -> vecview.Scene:
    """The Earth lit from the left: ice cap, night side, sunlight in and out, infrared out."""
    cam = vecview.OrthographicCamera(azim_deg=-60.0, elev_deg=32.0, scale=40.0)
    scene = vecview.Scene(cam, pad=2.0)
    view, z = np.asarray(cam.view, dtype=float), np.array([0.0, 0.0, 1.0])
    right, down = cam.screen_basis(view)
    sun = unit(-right + 0.45 * unit(view - (view @ z) * z))  # in the equatorial plane
    origin = np.zeros(3)

    scene.sphere(5, origin, 1.07, fill="#a9d0ee", opacity=0.45, id="atmosphere")
    scene.sphere(10, origin, 1.0, id="earth", **OCEAN)
    grid = dict(stroke="#ffffff", stroke_opacity=0.22, stroke_width=0.4)
    for lat in (-60, -30, 0, 30, 60):
        circle = vecview.circle_shape((0, 0, np.sin(np.radians(lat))), np.cos(np.radians(lat)), z)
        scene.sphere_curve(11, origin, circle, closed=True, id=f"latitude-{lat}", **grid)
    for lon in range(0, 180, 30):
        normal = (np.sin(np.radians(lon)), -np.cos(np.radians(lon)), 0)
        circle = vecview.circle_shape(origin, 1.0, normal, n=96)
        scene.sphere_curve(11, origin, circle, closed=True, id=f"meridian-{lon}", **grid)
    cap = vecview.circle_shape(edge * z, np.sqrt(1 - edge**2), z, n=120)
    scene.polygon(12, cap, fill="#f4f9fd", stroke="#b6d6ee", stroke_width=0.4, id="ice-cap")

    # A soft terminator: the night side darkened in steps, turning the sun a little each
    # time about the axis through the terminator's two ends on the limb.
    away = unit(np.cross(np.cross(sun, view), sun))  # from the day side across to the night
    for k, turn in enumerate(np.radians(np.arange(-15, 31, 2.5))):
        s = np.cos(turn) * sun + np.sin(turn) * away
        scene.polygon(14, night_side(view, s), fill="#0b1a2b", opacity=0.04, id=f"night-{k}")

    beam = dict(normal="camera", shaft_w=0.05, head_w=0.17, head_len=0.2, fill=SUN)
    hits = [h * z + np.sqrt(1 - h**2) * sun for h in (0.5, 0.0, -0.5)]
    for k, hit in enumerate(hits):
        scene.arrow(20, hit + 1.5 * sun, -sun, 1.47, id=f"sunlight-{k}", **beam)
    bounce = -sun + 2 * (sun @ hits[0]) * hits[0]
    scene.arrow(
        20, hits[0] + 0.05 * bounce, bounce, 0.95, id="reflected", fill_opacity=0.55, **beam
    )

    for k, angle in enumerate(np.radians([-35, 5, 45])):
        out = np.cos(angle) * right - np.sin(angle) * down
        side = np.cross(view, out)
        wave = vecview.sine_ribbon(1.12 * out, out, 0.75, side, 0.05, 0.19, n=120)
        scene.polyline(20, wave, stroke=INFRARED, stroke_width=1.0, id=f"infrared-{k}")
        head = dict(normal="camera", shaft_w=0.0, head_w=0.18, head_len=0.2, fill=INFRARED)
        scene.arrow(20, wave[-1], out, 0.2, id=f"infrared-head-{k}", **head)

    slots = {
        "sun": (hits[1] + 1.5 * sun, "east", -3, 0),
        "reflected": (hits[0] + bounce, "west", 3, 0),
        "olr": (2.1 * right, "west", 2, 0),
    }
    for name, (at, align, dx, dy) in slots.items():
        w, h = labels[name].width_px, labels[name].height_px
        scene.slot(50, at, w, h, align=align, dx=dx, dy=dy, id=f"label-{name}")
    return scene


# --- panels b-d: the plots ------------------------------------------------------


def latitude_axis(ax: plt.Axes) -> None:
    """x = sin(latitude), so equal widths are equal areas of the globe."""
    ax.set_xlim(0, 1)
    ax.set_xticks(np.sin(np.radians([0, 30, 60, 90])), ["0°", "30°", "60°", "90°"])


def plot_budget(axes: np.ndarray, edge: float, t: np.ndarray) -> None:
    """Absorbed sunlight and outgoing infrared by latitude, and the temperature they set."""
    top, bottom = axes
    absorbed, emitted = Q0 * insolation() * coalbedo(edge), A + B * t
    for ax in axes:
        ax.axvspan(edge, 1, color=ICE_FILL, lw=0, zorder=0)
        latitude_axis(ax)
    top.fill_between(X, absorbed, emitted, where=absorbed > emitted, color=SUN, alpha=0.2, lw=0)
    top.fill_between(
        X, absorbed, emitted, where=absorbed < emitted, color=INFRARED, alpha=0.2, lw=0
    )
    top.plot(X, absorbed, color=SUN)
    top.plot(X, emitted, color=INFRARED)
    top.text(0.03, 315, "absorbed solar", color=SUN, va="bottom")
    top.text(0.03, 250, "outgoing infrared", color=INFRARED, va="top")
    top.text(0.13, 290, "surplus", color=SUN, ha="center", va="center")
    top.text(0.82, 120, "deficit", color=INFRARED, ha="center", va="center")
    top.annotate("", (0.75, 150), (0.12, 150), arrowprops=ARROW)
    top.text(0.43, 155, "poleward transport", ha="center", va="bottom")
    top.set_ylim(60, 340)
    top.set_yticks([100, 200, 300])
    top.set_ylabel(r"Flux (W m$^{-2}$)")
    top.tick_params(labelbottom=False)

    bottom.plot(X, t, color=INK)
    bottom.axhline(T_ICE, color=ICE, lw=0.5, ls=(0, (3, 2)))
    bottom.text(0.03, T_ICE + 1, r"$T_i = -10$ °C", color=ICE, va="bottom")
    bottom.text(edge - 0.015, 26, "ice", color=ICE, ha="right", va="top")
    bottom.set_ylim(-22, 32)
    bottom.set_yticks([-20, 0, 20])
    bottom.set_xlabel("Latitude")
    bottom.set_ylabel("Temperature (°C)")


def plot_hysteresis(ax: plt.Axes) -> None:
    """Ice-edge latitude against insolation: the stable branches and the jumps between them."""
    edges = np.linspace(0.002, 0.998, 400)
    q = np.array([steady_state(e)[0] for e in edges]) / Q0
    lat = np.degrees(np.arcsin(edges))
    stable = np.gradient(q) > 0
    for mask, style in ((stable, dict(color=ICE)), (~stable, dict(color=GREY, ls=(0, (3, 2))))):
        grown = mask | np.roll(mask, 1) | np.roll(mask, -1)  # join the pieces where they meet
        ax.plot(np.where(grown, q, np.nan), lat, **style)
    q_snow, q_free = steady_state(0.0)[0] / Q0, steady_state(1.0)[0] / Q0
    i_min = np.argmin(q)
    ax.plot([0.85, q_snow], [0, 0], color=ICE)
    ax.plot([q_free, 1.4], [90, 90], color=ICE)
    jumps = [
        ((q[i_min], lat[i_min]), (q[i_min], 0)),
        ((q_snow, 0), (q_snow, 90)),
        (
            (q_free, 90),
            (q_free, np.interp(q_free, q[stable & (lat > 40)], lat[stable & (lat > 40)])),
        ),
    ]
    for start, end in jumps:
        ax.annotate("", end, start, arrowprops=dict(ARROW, ls=(0, (2, 1.5))))
    today = np.degrees(np.arcsin(present_edge()))
    ax.plot(1, today, "o", ms=4, color=ICE, mec="white", mew=0.5)
    ax.text(1.02, today - 3, "today", va="top")
    ax.text(0.94, 3, "snowball", color=ICE, va="bottom")
    ax.text(1.2, 87, "ice-free", color=ICE, va="top")
    ax.set_xlim(0.85, 1.4)
    ax.set_ylim(-3, 93)
    ax.spines["left"].set_bounds(0, 90)
    ax.set_yticks([0, 30, 60, 90], ["0°", "30°", "60°", "90°"])
    ax.set_xlabel(r"Insolation $S/S_0$")
    ax.set_ylabel("Ice-edge latitude")


def plot_warming(ax: plt.Axes) -> None:
    """Abrupt CO2 doubling and a 1 % per year rise held at doubling, on a log time axis."""
    dt, years = 0.05, 3000.0
    t = np.arange(0, years + dt / 2, dt)
    mid = t[:-1] + dt / 2
    t_double = np.log(2) / np.log(1.01)
    abrupt = two_layer(np.full(mid.size, F_2X), dt)
    ramp = two_layer(5.35 * np.log(1.01) * np.minimum(mid, t_double), dt)
    ecs = F_2X / LAMBDA
    tcr = np.interp(t_double, t, ramp[:, 0])

    ax.axhline(ecs, color=GREY, lw=0.5, ls=(0, (3, 2)))
    ax.text(6, ecs + 0.06, f"ECS = {ecs:.1f} K", va="bottom")
    fast, slow = timescales()
    for tau in (fast, slow):
        ax.axvline(tau, color=GREY, lw=0.5, ls=(0, (1, 1.5)), zorder=0)
    vertical = dict(color=GREY, rotation=90, va="bottom")
    ax.text(fast / 1.06, 1.45, rf"$\tau_\mathrm{{fast}}$ = {fast:.0f} yr", ha="right", **vertical)
    ax.text(slow * 1.06, 0.12, rf"$\tau_\mathrm{{slow}}$ = {slow:.0f} yr", ha="left", **vertical)
    ax.plot(t[1:], abrupt[1:, 0], color=INFRARED)
    ax.plot(t[1:], abrupt[1:, 1], color=INFRARED, lw=0.5, ls=(0, (3, 2)))
    ax.plot(t[1:], ramp[1:, 0], color=INK)
    ax.plot(t_double, tcr, "o", ms=3.5, color=INK, mec="white", mew=0.5)
    ax.text(6, 2.35, r"abrupt 2$\times$CO$_2$", color=INFRARED, va="bottom")
    ax.text(27, 0.95, "1% yr$^{-1}$", ha="right", va="top")
    leader = dict(arrowstyle="-", lw=0.5, color=INK, shrinkA=1, shrinkB=3)
    tcr_label = dict(ha="right", va="center", arrowprops=leader)
    ax.annotate(f"TCR\n{tcr:.1f} K", (t_double, tcr), (40, 1.5), **tcr_label)
    ax.text(600, 1.05, "deep\nocean", color=INFRARED, va="top")
    ax.set_xscale("log")
    ax.set_xlim(1, years)
    ax.set_xticks([1, 10, 100, 1000], ["1", "10", "100", "1,000"])
    ax.minorticks_off()
    ax.set_ylim(0, 3.5)
    ax.set_yticks([0, 1, 2, 3])
    ax.set_xlabel("Time after onset (yr)")
    ax.set_ylabel("Global warming (K)")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="118mm", theme=THEME)
    panels = fig.grid(
        [["globe", "globe", "budget"], ["hysteresis", "warming", "budget"]],
        width_ratios=(1, 1, 1.1),
        margins=("6mm", "3mm", "10mm", "12mm"),  # top, right, bottom, left
        gap=("14mm", "16mm"),  # between rows, between columns
    )
    edge = present_edge()
    _, temperature = steady_state(edge)

    tex = THEME.vectex()
    labels = {
        "sun": vectex.render(r"$S_0/4$", **tex | {"color": SUN}),
        "reflected": vectex.render(r"$\alpha S_0/4$", **tex | {"color": SUN}),
        "olr": vectex.render(r"$A + BT$", **tex | {"color": INFRARED}),
    }
    panels["globe"].add(globe_scene(labels, edge), id="globe-scene")
    for name, label in labels.items():
        fig.fill_slot(f"label-{name}", label)

    mpl_fig, axes = panels["budget"].subplots(2, 1, sharex=True, gridspec_kw=dict(hspace=0.1))
    plot_budget(axes, edge, temperature)
    panels["budget"].add(mpl_fig, id="budget-plot", fit="axes")
    for name, plot in (("hysteresis", plot_hysteresis), ("warming", plot_warming)):
        mpl_fig, ax = panels[name].subplots()
        plot(ax)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    fig.label("a", panels["globe"].nw)
    fig.label("b", panels["budget"].nw)
    fig.label("c", panels["hysteresis"].nw)
    fig.label("d", panels["warming"].nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"climate_energy_balance{suffix}")
    print(f"wrote {OUT / 'climate_energy_balance.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
