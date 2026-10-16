"""Shocks in a production network: a chip collapse, the bullwhip effect, and hubs.

A Nature double-column figure. A VecView map of a twelve-sector economy --
sectors as towers in four tiers from raw materials to final goods, the largest
input flows as arrows on the floor, households at the end -- shows what a
collapse of chip productivity does to every sector's output: vermillion caps
are output lost, pale extensions output gained by the suppliers a crippled chip
sector now leans on harder. Beside it, three Matplotlib panels: the bullwhip
effect up a four-stage supply chain, the failure of Hulten's theorem for large
shocks when inputs are complements, and why idiosyncratic shocks stop averaging
out when a few suppliers are hubs. Vermillion is the chip shock throughout, and
the blue of each tier darkens upstream, in the map and in the supply chain alike.

Everything is computed here; nothing is measured. The economy is a CES
production network with one factor, labour (Baqaee and Farhi 2019): sector i
makes y_i from labour and the goods of other sectors with cost shares Omega_ij
and one elasticity of substitution sigma, so prices solve

    p_i = A_i^-1 [alpha_i + sum_j Omega_ij p_j^(1 - sigma)]^(1 / (1 - sigma)),

real GDP is one over the consumer price index, and Hulten's theorem gives its
first-order response, d log Y = lambda_i d log A_i, with lambda_i the sector's
sales over GDP (its Domar weight). The supply chain orders up to a moving-average
forecast (Chen et al. 2000); its demand is simulated with a fixed seed. The
volatility panel wires random economies whose suppliers are drawn with Zipf
weights (Acemoglu et al. 2012), also with a fixed seed.

Usage:
    python examples/production_network.py     # requires vecview and TeX
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
SHOCK = "#d55e00"  # Okabe-Ito vermillion: the chip shock
SHOCK_RAMP = ("#f0a875", "#e07b39", "#b34700")  # sigma = 0.5, 0.2, 0.1
TIERS = ("#0f3352", "#215f92", "#3e84bb", "#6aa5d3")  # upstream to downstream
NETWORKS = ("#a59d8f", "#6e675b", INK)  # balanced, then fatter-tailed
LABEL = "#6f6a61"
FLOOR = dict(fill="#f3f1ec", stroke="#d9d5cc", stroke_width=0.5)

# --- the economy ----------------------------------------------------------------

# Sectors by tier, upstream first; within a tier, from the back of the map to the front.
TIER_NAMES = ("Raw materials", "Components", "Manufacturing", "Final goods")
SECTORS = (
    ("mining", "energy", "chemicals"),
    ("metals", "chips", "plastics"),
    ("machinery", "vehicles", "electronics"),
    ("construction", "retail", "services"),
)
NAMES = [name for tier in SECTORS for name in tier]
# Cost shares of each sector's inputs; the rest of its costs is labour.
INPUTS = {
    "energy": {"mining": 0.15, "machinery": 0.05},
    "mining": {"energy": 0.15, "machinery": 0.10},
    "chemicals": {"energy": 0.20, "mining": 0.15},
    "metals": {"mining": 0.30, "energy": 0.15},
    "chips": {"chemicals": 0.20, "energy": 0.10, "machinery": 0.10, "metals": 0.05},
    "plastics": {"chemicals": 0.40, "energy": 0.10},
    "machinery": {"metals": 0.25, "chips": 0.10, "plastics": 0.05, "energy": 0.05},
    "electronics": {"chips": 0.30, "plastics": 0.10, "metals": 0.05, "energy": 0.03},
    "vehicles": {"metals": 0.20, "chips": 0.12, "plastics": 0.10, "electronics": 0.08},
    "construction": {"metals": 0.15, "machinery": 0.10, "plastics": 0.05, "energy": 0.05},
    "retail": {"vehicles": 0.25, "electronics": 0.20, "energy": 0.05},
    "services": {"electronics": 0.10, "energy": 0.05, "vehicles": 0.05},
}
FINAL = {"construction": 0.2, "retail": 0.35, "services": 0.35, "energy": 0.05, "vehicles": 0.05}

N = len(NAMES)
CHIPS = NAMES.index("chips")
OMEGA = np.array([[INPUTS[buyer].get(seller, 0.0) for seller in NAMES] for buyer in NAMES])
LABOUR = 1 - OMEGA.sum(axis=1)
CONSUMPTION = np.array([FINAL.get(name, 0.0) for name in NAMES])
DOMAR = CONSUMPTION @ np.linalg.inv(np.eye(N) - OMEGA)  # sales over GDP

SIGMAS = (0.5, 0.2, 0.1)
MAP_SIGMA, MAP_SHOCK = 0.2, 1.5  # the shock drawn in the map

# --- supply chain ---------------------------------------------------------------

LEAD, WINDOW = 1, 4  # weeks of lead time, weeks in the moving-average forecast
STAGES = ("Retailer", "Wholesaler", "Distributor", "Factory")

# --- volatility -----------------------------------------------------------------

ALPHA = 0.5  # labour share
SUPPLIERS = 4  # suppliers per sector
TAILS = (None, 1.5, 1.2)  # balanced, then Zipf tails


# --- economics ------------------------------------------------------------------


def prices(log_a: np.ndarray, sigma: float) -> np.ndarray:
    """Unit costs at productivities exp(log_a), the wage the numeraire."""
    if sigma == 1:
        return np.exp(np.linalg.solve(np.eye(N) - OMEGA, -log_a))
    p = np.ones(N)
    for _ in range(5000):  # a contraction: costs are monotone in input prices
        new = (LABOUR + OMEGA @ p ** (1 - sigma)) ** (1 / (1 - sigma)) * np.exp(-log_a)
        if np.max(np.abs(new - p)) < 1e-12:
            break
        p = new
    return new


def equilibrium(log_a: np.ndarray, sigma: float) -> tuple[float, np.ndarray]:
    """Real GDP and each sector's real gross output, both 1 and DOMAR without shocks.

    Consumers substitute with the same sigma; output meets final demand plus
    every sector's input demand, x_ki = Omega_ki (p_i / p_k)^-sigma A_k^(sigma - 1) y_k.
    """
    p = prices(log_a, sigma)
    if sigma == 1:
        index = np.exp(CONSUMPTION @ np.log(p))
    else:
        index = (CONSUMPTION @ p ** (1 - sigma)) ** (1 / (1 - sigma))
    gdp = 1 / index
    final = CONSUMPTION * (p / index) ** -sigma * gdp
    inputs = OMEGA * (p[None, :] / p[:, None]) ** -sigma * np.exp(log_a)[:, None] ** (sigma - 1)
    return gdp, np.linalg.solve(np.eye(N) - inputs.T, final)


def chip_shock(size: float) -> np.ndarray:
    log_a = np.zeros(N)
    log_a[CHIPS] = -size
    return log_a


def order_filter() -> np.ndarray:
    """One stage's orders as a filter of the demand it sees.

    Ordering up to LEAD times a WINDOW-week moving average gives
    q_t = d_t-1 + (LEAD / WINDOW)(d_t-1 - d_t-1-WINDOW).
    """
    h = np.zeros(WINDOW + 2)
    h[1] += 1 + LEAD / WINDOW
    h[WINDOW + 1] -= LEAD / WINDOW
    return h


def bullwhip(stages: int) -> tuple[np.ndarray, np.ndarray]:
    """Variance of each stage's orders over that of customer demand, white-noise demand.

    Without sharing, each stage forecasts from the orders it receives, so the
    filters compound; with shared point-of-sale data every stage forecasts
    customer demand over its total lead time (Chen et al. 2000).
    """
    h, chain, alone = order_filter(), np.array([1.0]), [1.0]
    for _ in range(stages):
        chain = np.convolve(chain, h)
        alone.append(float(chain @ chain))
    lead = LEAD * np.arange(stages + 1)
    shared = 1 + 2 * lead / WINDOW + 2 * lead**2 / WINDOW**2
    return np.array(alone), shared


def orders(weeks: int, rng: np.random.Generator) -> np.ndarray:
    """Customer demand, then the orders each stage passes upstream."""
    burn_in = 4 * (WINDOW + 1)
    chain = [100 + 8 * rng.standard_normal(weeks + burn_in)]
    for _ in STAGES:
        chain.append(np.convolve(chain[-1], order_filter())[: chain[-1].size])
    return np.array(chain)[:, burn_in:]


def zipf_weights(n: int, tail: float | None) -> np.ndarray:
    return np.ones(n) if tail is None else (np.arange(1, n + 1) / n) ** (-1 / tail)


def volatility(n: int, tail: float | None, rng: np.random.Generator) -> float:
    """Aggregate over sectoral volatility, ||v||, for one random economy of n sectors.

    Every sector buys equally from SUPPLIERS suppliers drawn with Zipf weights;
    the influence vector solves v = ALPHA / n + (1 - ALPHA) W^T v.
    """
    w = zipf_weights(n, tail)
    suppliers = rng.choice(n, (n, SUPPLIERS), p=w / w.sum()).ravel()
    v = np.full(n, ALPHA / n)
    for _ in range(60):  # converges as (1 - ALPHA)^k
        sales = np.bincount(suppliers, np.repeat(v, SUPPLIERS) / SUPPLIERS, minlength=n)
        v = ALPHA / n + (1 - ALPHA) * sales
    return float(np.linalg.norm(v))


def mean_field(n: np.ndarray, tail: float | None) -> np.ndarray:
    """||v|| when every sector buys from all suppliers in proportion to their weights."""
    out = []
    for size in n:
        w = zipf_weights(int(size), tail)
        out.append(np.linalg.norm(ALPHA / size + (1 - ALPHA) * w / w.sum()))
    return np.array(out)


# --- panel a: the map -----------------------------------------------------------


SPACING = 3.1  # between tiers
DEPTH = 2.6  # between the sectors of a tier
HEIGHT = 7.0  # world units per unit of Domar weight
RADIUS = 0.5
FLOW = "#bfb7a9"


def tier_of(name: str) -> int:
    return next(k for k, members in enumerate(SECTORS) if name in members)


def place(name: str, z: float = 0.0) -> np.ndarray:
    """Tiers run left to right, households last; each tier is three sectors deep."""
    if name == "households":
        return np.array([SPACING * len(SECTORS), 0.0, z])
    tier = tier_of(name)
    return np.array([SPACING * tier, DEPTH * (1 - SECTORS[tier].index(name)), z])


def shade(color: str, toward: str, t: float) -> str:
    a, b = (np.array([int(c[i : i + 2], 16) for i in (1, 3, 5)]) for c in (color, toward))
    return "#" + "".join(f"{round(x):02x}" for x in (1 - t) * a + t * b)


def solid(color: str) -> dict[str, str | float]:
    return dict(
        fill=color,
        highlight=shade(color, "#ffffff", 0.55),
        stroke=shade(color, "#000000", 0.45),
        stroke_width=0.6,
    )


def route(seller: str, buyer: str) -> np.ndarray:
    """The floor path of a flow: straight to the next tier, or along a lane between rows.

    A flow that skips a tier would run through the towers in between, so it
    bends into the open lane beside its rows, runs along it, and bends back out.
    """
    start, end = place(seller), place(buyer)
    if buyer == "households" or tier_of(buyer) == tier_of(seller) + 1:
        return np.array([start, end])
    lane = np.array([0, DEPTH / 2 if start[1] + end[1] >= 0 else -DEPTH / 2, 0])
    bend = np.array([SPACING / 2, 0, 0])
    controls = (start, start * (1, 0, 1) + lane + bend, end * (1, 0, 1) + lane - bend, end)
    t = np.linspace(0, 1, 80)[:, None]
    weights = ((1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t**2 * (1 - t), t**3)  # cubic Bézier
    return sum(w * c for w, c in zip(weights, controls, strict=True))


def trimmed(path: np.ndarray, start: float, end: float) -> np.ndarray:
    """``path`` with ``start`` and ``end`` of its length cut from its two ends."""
    run = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    keep = np.r_[start, run[(run > start) & (run < run[-1] - end)], run[-1] - end]
    return np.column_stack([np.interp(keep, run, path[:, i]) for i in range(3)])


def flow_arrow(scene: vecview.Scene, seller: str, buyer: str, flow: float, fill: str) -> None:
    """A flat arrow on the floor, footprint to footprint, as wide as the flow.

    The tip stops well short of the buyer, so the tower, which stands in front
    of the floor, does not hide the head of a flow arriving from behind it.
    """
    width = 0.08 + 2.2 * flow
    shape = dict(shaft_w=width, head_w=width + 0.42, head_len=0.5)
    path = trimmed(route(seller, buyer), start=1.3 * RADIUS, end=2.2 * RADIUS)
    arrow = vecview.path_arrow_shape(path, (0, 0, 1), **shape)
    scene.polygon(2, arrow, fill=fill, id=f"flow-{seller}-{buyer}", class_="flow")


def network_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """Towers as tall as each sector's output once chips collapse, with what changed shaded."""
    cam = vecview.OrthographicCamera(azim_deg=-72.0, elev_deg=28.0, scale=30.0)
    scene = vecview.Scene(cam, pad=2.0)
    scene.sort_by_depth(10)
    width, depth = SPACING * len(SECTORS) + 3.0, 2 * DEPTH + 2.4
    floor = vecview.box_faces((width / 2 - 1.5, 0.0, -0.08), (width, depth, 0.16))
    scene.faces(0, floor, cull=True, id="floor", **FLOOR)

    # The largest flows downstream, and what households buy.
    sales = OMEGA * DOMAR[:, None]  # from seller j to buyer i, over GDP
    for buyer, seller in zip(*np.nonzero(sales >= 0.015), strict=True):
        if tier_of(NAMES[buyer]) > tier_of(NAMES[seller]):
            fill = SHOCK if seller == CHIPS else FLOW
            flow_arrow(scene, NAMES[seller], NAMES[buyer], sales[buyer, seller], fill)
    for name in SECTORS[-1]:
        flow_arrow(scene, name, "households", CONSUMPTION[NAMES.index(name)], FLOW)

    _, after = equilibrium(chip_shock(MAP_SHOCK), MAP_SIGMA)
    for k, name in enumerate(NAMES):
        color = SHOCK if k == CHIPS else TIERS[tier_of(name)]
        low, high = sorted((HEIGHT * after[k], HEIGHT * DOMAR[k]))
        body = place(name), place(name, low)
        scene.cylinder(10, *body, RADIUS, id=f"sector-{name}", class_="sector", **solid(color))
        change = dict(fill_opacity=0.3, stroke_width=0.5)
        if after[k] < DOMAR[k]:
            change |= dict(id=f"lost-{name}", class_="lost", fill=SHOCK, stroke=SHOCK)
        else:
            change |= dict(id=f"gained-{name}", class_="gained", fill=color, stroke=color)
        scene.cylinder(10, place(name, low), place(name, high), RADIUS, **change)

    gable = np.array(
        [[-0.6, -0.6, 0], [0.6, -0.6, 0], [0.6, -0.6, 0.8], [0, -0.6, 1.3], [-0.6, -0.6, 0.8]]
    )
    house = vecview.extrude(gable + place("households"), (0, 1.2, 0))
    scene.faces(
        10, house, cull=True, id="households", fill="#ebe7de", stroke="#8d8576", stroke_width=0.6
    )

    def top(name: str) -> np.ndarray:
        k = NAMES.index(name)
        return place(name, HEIGHT * max(after[k], DOMAR[k]))

    front = -depth / 2 - 0.2
    slots = {f"tier-{k}": ((SPACING * k, front, 0), "north", 0, 0) for k in range(len(SECTORS))} | {
        "households": ((SPACING * len(SECTORS), front, 0), "north", 0, 0),
        "key": ((-1.5, depth / 2, 0), "southwest", 0, -4),
        "chips": (top("chips"), "south", 0, -6),
        "lost": (top("construction"), "west", 20, 0),
        "gained": (top("chemicals"), "east", -18, 0),
    }
    for name, (at, align, dx, dy) in slots.items():
        label = labels[name]
        w, h = label.width_px, label.height_px
        pin = dict(align=align, dx=dx, dy=dy, id=f"label-{name}")
        scene.slot(50, at, w, h, content=label.to_svg_py(), **pin)
    return scene


# --- panels b-d: the plots ------------------------------------------------------


def plot_bullwhip(axes: np.ndarray) -> None:
    """Orders swell upstream; shared sales data shrink the swell."""
    top, bottom = axes
    weeks = 52
    chain = orders(weeks, np.random.default_rng(2026))
    spacing = 110
    colors = (INK, *TIERS[::-1])
    for k, (series, color, name) in enumerate(
        zip(chain, colors, ("Customers", *STAGES), strict=True)
    ):
        offset = spacing * k
        top.axhline(offset, color=GREY, lw=0.4, ls=(0, (1, 1.5)), zorder=0)
        top.plot(np.arange(weeks), series - 100 + offset, color=color, lw=0.75)
        top.text(-1.5, offset, name, color=color, ha="right", va="center")
    top.plot([weeks - 0.5] * 2, [-80, -30], color=INK, lw=0.75, solid_capstyle="butt")
    top.text(weeks - 1.5, -55, "50 units", ha="right", va="center")
    top.set_xlim(0, weeks)
    top.set_ylim(-85, spacing * len(STAGES) + 75)
    top.set_yticks([])
    top.spines["left"].set_visible(False)
    top.set_xticks([0, 13, 26, 39, 52])
    top.set_xlabel("Week")

    alone, shared = bullwhip(len(STAGES))
    stage = np.arange(len(STAGES) + 1)
    bottom.plot(stage, shared, color=GREY, ls=(0, (3, 2)))
    bottom.plot(stage, alone, color=INK, zorder=2)
    bottom.scatter(stage, alone, s=14, c=colors, edgecolors="white", linewidths=0.5, zorder=3)
    bottom.text(3.75, alone[-1], f"{alone[-1]:.0f}" + r"$\times$", ha="right", va="center")
    bottom.text(2.75, 4.6, "own orders only", ha="right", va="bottom")
    bottom.text(3.95, shared[-1] / 2.1, "shared sales data", color=GREY, ha="right", va="top")
    bottom.set_yscale("log")
    bottom.set_ylim(0.8, 13)
    bottom.set_yticks([1, 2, 5, 10], ["1", "2", "5", "10"])
    bottom.minorticks_off()
    bottom.set_xticks(stage)
    bottom.set_xlim(-0.3, 4.3)
    bottom.set_xlabel("Stages upstream of customers")
    bottom.set_ylabel("Order variance ratio")


def plot_hulten(ax: plt.Axes) -> None:
    """GDP lost to a chip-productivity collapse: Hulten's line, and complementarity's curves."""
    shocks = np.linspace(0, 2.5, 101)
    hulten = 100 * DOMAR[CHIPS] * shocks
    ax.plot(shocks, hulten, color=INK, lw=0.75, ls=(0, (3, 2)))
    for sigma, color in zip(SIGMAS, SHOCK_RAMP, strict=True):
        loss = [-100 * np.log(equilibrium(chip_shock(s), sigma)[0]) for s in shocks]
        ax.plot(shocks, loss, color=color)
        ax.text(2.55, loss[-1], rf"$\sigma = {sigma:g}$", color=color, va="center")
    gdp, _ = equilibrium(chip_shock(MAP_SHOCK), MAP_SIGMA)
    ax.plot(MAP_SHOCK, -100 * np.log(gdp), "o", ms=4, color=SHOCK, mec="white", mew=0.5)
    ax.text(MAP_SHOCK - 0.08, -100 * np.log(gdp) + 1, "map in a", ha="right", va="bottom")
    ax.text(2.55, hulten[-1], "Hulten,\n" + r"$\sigma = 1$", va="center")
    slope = rf"slope $\lambda_\mathrm{{chips}} = {DOMAR[CHIPS]:.3f}$"
    ax.text(1.4, 100 * DOMAR[CHIPS] * 1.4 - 2.5, slope, ha="left", va="top")
    ax.set_xlim(0, 2.5)
    ax.set_ylim(0, 50)
    ax.set_xlabel(r"Chip productivity shock $-\Delta\log A$")
    ax.set_ylabel(r"GDP loss $-\Delta\log Y$ (%)")


def plot_volatility(ax: plt.Axes) -> None:
    """Aggregate volatility falls as n^-1/2 only if no supplier stands out."""
    rng = np.random.default_rng(12)
    sizes = np.unique(np.logspace(1, 4.5, 15).astype(int))
    dense = np.logspace(1, 4.5, 60)
    ax.axhline(1 - ALPHA, color=GREY, lw=0.5, ls=(0, (3, 2)))
    ax.text(12, 0.55, "one hub supplies all", color=GREY, va="bottom")
    names = (r"balanced, $n^{-1/2}$", r"Zipf, $\beta = 1.5$", r"$\beta = 1.2$")
    for tail, color, name in zip(TAILS, NETWORKS, names, strict=True):
        draws = [np.median([volatility(n, tail, rng) for _ in range(8)]) for n in sizes]
        line = mean_field(dense, tail)
        ax.plot(dense, line, color=color, lw=0.75)
        ax.plot(sizes, draws, "o", ms=3, color=color, mec="white", mew=0.4)
        ax.text(dense[-1] * 1.4, line[-1], name, color=color, va="center")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(8, 1e6)
    ax.set_xticks([1e1, 1e2, 1e3, 1e4])
    ax.minorticks_off()
    ax.spines["bottom"].set_bounds(8, 4e4)
    ax.set_ylim(3e-3, 1)
    ax.set_yticks([0.01, 0.1, 1], ["0.01", "0.1", "1"])
    ax.set_xlabel("Number of sectors $n$")
    ax.set_ylabel(r"Aggregate volatility $\sigma_Y / \sigma_\varepsilon$")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="118mm", theme=THEME, background="white")
    panels = fig.grid(
        [["network", "network", "bullwhip"], ["hulten", "volatility", "bullwhip"]],
        width_ratios=(1, 1, 1.1),
        margins=("6mm", "3mm", "10mm", "12mm"),  # top, right, bottom, left
        gap=("14mm", "20mm"),  # between rows, between columns
    )

    tex = THEME.vectex()
    names = {f"tier-{k}": name for k, name in enumerate(TIER_NAMES)} | {"households": "Households"}
    labels = {slot: vectex.render(name, **tex | {"color": LABEL}) for slot, name in names.items()}
    labels["chips"] = vectex.render("Chips", **tex | {"color": SHOCK})
    labels["lost"] = vectex.render("output lost", **tex | {"color": SHOCK})
    labels["gained"] = vectex.render("gained", **tex | {"color": TIERS[0]})
    labels["key"] = vectex.render("Height: output after a chip shock", **tex | {"color": LABEL})
    panels["network"].add(network_scene(labels), id="network-scene")

    grid = dict(height_ratios=(1.6, 1), hspace=0.5)
    mpl_fig, axes = panels["bullwhip"].subplots(2, 1, gridspec_kw=grid)
    plot_bullwhip(axes)
    panels["bullwhip"].add(mpl_fig, id="bullwhip-plot", fit="axes")
    for name, plot in (("hulten", plot_hulten), ("volatility", plot_volatility)):
        mpl_fig, ax = panels[name].subplots()
        plot(ax)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    fig.label("a", panels["network"].nw)
    fig.label("b", panels["bullwhip"].nw)
    fig.label("c", panels["hulten"].nw)
    fig.label("d", panels["volatility"].nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"production_network{suffix}")
    print(f"wrote {OUT / 'production_network.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
