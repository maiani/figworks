"""A hot Jupiter transiting a Sun-like star: geometry, light curve, and spectrum.

A Nature double-column figure in which three producers meet through
`Panel.add`: a VecView scene of the transit geometry with VecTeX labels pinned
upright into it, and three Matplotlib panels whose axes frames sit on the grid.
Star and planet keep their colours from the schematic into every plot.

Everything is computed here. The light curve is a quadratic limb-darkened disk
occulted by an opaque one, integrated numerically ring by ring; the planet's
radius in the photometer band is the band average of the transmission model.
The photometry (2-min cadence, six transits folded) and the spectrum's error
bars are simulated with seeded Gaussian noise. The schematic is not to scale.

Usage:
    python examples/exoplanet_transit.py     # requires vecview and TeX
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
GREY = "#a3a3a3"
STAR = "#e08a1e"  # the star and the photometer band
STAR_CORE = "#fff3c4"
PLANET = "#1d3f73"  # the planet and its data
ATMOSPHERE = "#3f8fcf"  # the planet's limb and its transmission spectrum
CONTACT_LABEL = dict(ha="center", va="bottom", color=PLANET)
DOUBLE_ARROW = dict(arrowstyle="<->", lw=0.5, color=INK, shrinkA=0, shrinkB=0)

# A hot Jupiter on a 3.5-day orbit around a Sun-like star.
PERIOD_H = 3.52 * 24
A_OVER_R = 9.8  # semi-major axis in stellar radii, from Kepler's third law
IMPACT = 0.45  # impact parameter b
LIMB = (0.40, 0.21)  # quadratic limb darkening, u1 and u2
BAND = (0.6, 1.0)  # photometer bandpass, um
NOISE_PPM = 1500.0  # per 2-min exposure

# The atmosphere: H = kT / (mu m_H g) = 330 km at 1100 K, mu = 2.3, g = 12 m/s^2.
SCALE_HEIGHT = 4.7e-4  # H / R_star
RADIUS_REF = 0.108  # planet radius where the atmosphere is opaque in the continuum
BANDS = {  # molecule: (centre um, width um, strength), relative to the continuum
    "H$_2$O": [(1.15, 0.05, 3.0), (1.40, 0.07, 8.0), (1.88, 0.09, 10.0), (2.75, 0.15, 24.0)],
    "CO$_2$": [(4.30, 0.12, 40.0)],
}


# --- physics --------------------------------------------------------------------


def intensity(r: np.ndarray) -> np.ndarray:
    """Quadratic limb darkening: surface brightness at radius r on the stellar disk."""
    mu = np.sqrt(np.clip(1 - r**2, 0, None))
    u1, u2 = LIMB
    return 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2


def occulted_flux(z: np.ndarray, p: float, rings: int = 1500) -> np.ndarray:
    """Relative flux with a disk of radius p at sky separation z (stellar radii).

    Each thin ring of the stellar disk loses the fraction of its circumference
    that lies inside the planet's disk.
    """
    r = (np.arange(rings) + 0.5) / rings
    zz, rr = np.atleast_1d(z)[:, None], r[None, :]
    cos_half = (rr**2 + zz**2 - p**2) / (2 * rr * np.maximum(zz, 1e-12))
    covered = np.arccos(np.clip(cos_half, -1, 1)) / np.pi
    covered = np.where(rr < p - zz, 1.0, covered)  # ring wholly behind the planet
    weight = intensity(r) * r
    return 1 - (covered * weight).sum(axis=1) / weight.sum()


def separation(t_h: np.ndarray) -> np.ndarray:
    """Sky-projected star-planet distance on a circular orbit, t in hours from mid-transit."""
    phase = 2 * np.pi * t_h / PERIOD_H
    cos_i = IMPACT / A_OVER_R
    return A_OVER_R * np.hypot(np.sin(phase), cos_i * np.cos(phase))


def contact_times(p: float) -> np.ndarray:
    """T1-T4 in hours: where the sky separation is 1 + p and 1 - p."""
    cos_i = IMPACT / A_OVER_R
    x = np.sqrt(np.array([1 + p, 1 - p]) ** 2 - IMPACT**2) / (A_OVER_R * np.sqrt(1 - cos_i**2))
    t = np.arcsin(x) * PERIOD_H / (2 * np.pi)
    return np.array([-t[0], -t[1], t[1], t[0]])


def transit_depth(wavelength: np.ndarray) -> np.ndarray:
    """(R_p/R_star)^2: the planet looks larger where its atmosphere absorbs.

    The apparent radius rises by one scale height per e-fold of opacity
    (Rayleigh scattering plus Gaussian molecular bands over a grey continuum).
    """
    opacity = 1 + 1.6 * wavelength**-4
    for bands in BANDS.values():
        for centre, width, strength in bands:
            opacity = opacity + strength * np.exp(-0.5 * ((wavelength - centre) / width) ** 2)
    return (RADIUS_REF + SCALE_HEIGHT * np.log(opacity)) ** 2


def band_radius() -> float:
    """The planet's radius as the photometer sees it: the band-averaged depth."""
    wavelength = np.linspace(*BAND, 200)
    return float(np.sqrt(transit_depth(wavelength).mean()))


def photometry(p: float, transits: int = 6) -> tuple[np.ndarray, np.ndarray]:
    """Phase-folded 2-min photometry: times in hours and noisy relative fluxes."""
    rng = np.random.default_rng(1995)
    cadence = 2 / 60
    starts = rng.uniform(0, cadence, transits)  # each transit sampled at its own phase
    t = np.sort((np.arange(-3.2, 3.2, cadence)[:, None] + starts).ravel())
    return t, occulted_flux(separation(t), p) + rng.normal(0, NOISE_PPM * 1e-6, t.size)


def binned(t: np.ndarray, y: np.ndarray, width: float) -> tuple[np.ndarray, np.ndarray]:
    """Means of y in bins of the given width in t."""
    index = np.floor((t - t.min()) / width).astype(int)
    count = np.bincount(index)
    keep = count > 0
    return (np.bincount(index, t)[keep] / count[keep], np.bincount(index, y)[keep] / count[keep])


# --- panel a: the geometry ------------------------------------------------------


def orbit_point(theta: float, radius: float) -> np.ndarray:
    """A point of the orbit; theta = 0 is mid-transit, nearest the observer (+x)."""
    cos_i = IMPACT / radius  # keeps the impact parameter whatever the drawn radius
    e1 = np.array([np.sqrt(1 - cos_i**2), 0.0, cos_i])
    return radius * (np.cos(theta) * e1 + np.sin(theta) * np.array([0.0, 1.0, 0.0]))


def geometry_scene(labels: dict[str, vectex.VectexFragment], p: float) -> vecview.Scene:
    """The star, the band of its light that reaches the observer, and the planet crossing it.

    The camera sits a little above and beside the line of sight, so the planet
    at mid-transit is seen against the stellar disk, as the observer sees it.
    """
    cam = vecview.OrthographicCamera(azim_deg=-16.0, elev_deg=30.0, scale=40.0)
    scene = vecview.Scene(cam, pad=2.0)
    orbit_r, planet_r = 2.0, 1.6 * p  # not to scale
    origin, toward_observer = np.zeros(3), np.array([1.0, 0.0, 0.0])

    # The orbit, split where it passes behind the star.
    ring = np.array([orbit_point(t, orbit_r) for t in np.linspace(-np.pi, np.pi, 360, False)])
    behind = cam.depth(ring) < 0
    ring = np.roll(ring, -int(np.argmax(behind & ~np.roll(behind, 1))), axis=0)
    far = int(behind.sum())  # now the first `far` points
    leftmost = ring[np.argmin(cam.project(ring)[:, 0])]
    line = dict(stroke=INK, stroke_width=0.5, fill="none")
    scene.polyline(10, ring[: far + 1], id="orbit-back", **line)
    scene.polyline(30, np.vstack([ring[far:], ring[:1]]), id="orbit-front", **line)

    # The star, limb-darkened: a bright core fading to its orange rim, with a soft
    # glow; behind it, the band of its light that reaches the observer.
    face_u, face_v = cam.screen_basis(cam.view)
    scene.gaussian(12, origin, face_u, face_v, 0.8, 0.8, id="glow", color=STAR, opacity=0.3)
    band_end = 1.5 * orbit_r * toward_observer
    # An open cylinder of one stellar radius: outlined along its sides only.
    light = dict(fill=STAR, fill_opacity=0.07, stroke=STAR, stroke_width=0.4)
    scene.cylinder(13, origin, band_end, 1.0, ends=False, id="band", **light)
    scene.sphere(20, origin, 1.0, fill=STAR, stroke="none", id="star")
    core = dict(extent=1.24, id="star-core", color=STAR_CORE)
    scene.gaussian(21, origin, face_u, face_v, 0.8, 0.8, **core)

    # The planet mid-transit, and outlines where it enters and leaves the band (T1, T4).
    ingress = np.arcsin(np.sqrt((1 + planet_r) ** 2 - IMPACT**2) / orbit_r)
    for name, t in (("ingress", -ingress), ("egress", ingress)):
        outline = dict(fill="none", stroke=PLANET, stroke_width=0.5)
        scene.sphere(40, orbit_point(t, orbit_r), planet_r, id=f"planet-{name}", **outline)
    mid = orbit_point(0.0, orbit_r)
    scene.sphere(41, mid, planet_r * 1.3, fill=ATMOSPHERE, opacity=0.9, id="atmosphere")
    scene.sphere(42, mid, planet_r, fill=PLANET, highlight="#7d9cc9", id="planet")

    arrow = dict(normal="camera", shaft_w=0.03, head_w=0.16, head_len=0.26, fill=INK)
    scene.arrow(45, band_end, toward_observer, 1.2, **arrow, id="line-of-sight")

    # The stellar radius, drawn on the disk toward its upper left.
    up_left = -0.6 * face_u - 0.8 * face_v
    scene.polyline(43, [origin, up_left], stroke=INK, stroke_width=0.5, id="radius-star")

    slots = {
        "Rstar": (0.5 * up_left, "northeast", -2, 2),
        "Rp": (mid, "northwest", 6, 4),
        "observer": (band_end + 1.2 * toward_observer, "west", 4, -3),
        "orbit": (leftmost, "east", -3, 0),
    }
    for name, (at, align, dx, dy) in slots.items():
        w, h = labels[name].width_px, labels[name].height_px
        scene.slot(50, at, w, h, align=align, dx=dx, dy=dy, id=f"label-{name}")
    return scene


# --- panels b-d: the plots ------------------------------------------------------


def disk_colour(r: float) -> tuple[float, float, float]:
    """The schematic's star colours, mapped onto the limb-darkening profile."""
    limb = intensity(np.array([1.0]))[0]
    shade = (intensity(np.array([r]))[0] - limb) / (1 - limb)
    rgb = [np.array(matplotlib.colors.to_rgb(c)) for c in (STAR, STAR_CORE)]
    return tuple((1 - shade) * rgb[0] + shade * rgb[1])


def plot_sky(ax: plt.Axes, p: float) -> None:
    """The stellar disk as the observer sees it, with the transit chord and T1-T4."""
    for r in np.linspace(1, 0, 48, endpoint=False):
        ax.add_patch(plt.Circle((0, 0), r, color=disk_colour(r), lw=0))
    x1, x2 = np.sqrt(np.array([1 + p, 1 - p]) ** 2 - IMPACT**2)
    ax.plot([-1.35, 1.35], [IMPACT, IMPACT], color=INK, lw=0.5, ls=(0, (3, 2)))
    for x in (-x1, -x2, x2, x1):
        ax.add_patch(plt.Circle((x, IMPACT), p, fill=False, ec=PLANET, lw=0.5))
    # T1 and T4 outside the limb, above the chord; T2 and T3 inside it, below.
    below = -p - 0.04
    places = [
        (-x1 - p, p, "right"),
        (-x2, below, "center"),
        (x2, below, "center"),
        (x1 + p, p, "left"),
    ]
    for k, (x, dy, ha) in enumerate(places):
        va = "bottom" if dy > 0 else "top"
        ax.text(x, IMPACT + dy, f"T$_{k + 1}$", **dict(CONTACT_LABEL, ha=ha, va=va))
    ax.add_patch(plt.Circle((0, IMPACT), p * 1.3, color=ATMOSPHERE, alpha=0.9, lw=0))
    ax.add_patch(plt.Circle((0, IMPACT), p, color=PLANET, lw=0))
    ax.annotate("", (0.0, 0.0), (0.0, IMPACT - 1.3 * p), arrowprops=DOUBLE_ARROW)
    ax.text(0.06, 0.18, "$b$", va="center")
    ax.plot([0, -0.6], [0, -0.8], color=INK, lw=0.5)
    ax.text(-0.42, -0.34, r"$R_*$", ha="right", va="center")
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect("equal")
    ax.set_axis_off()


def plot_photometry(axes: np.ndarray, p: float) -> None:
    """Folded light curve with the limb-darkened model, and the residuals in ppm."""
    t, flux = photometry(p)
    model_t = np.linspace(-3.2, 3.2, 801)
    residual = (flux - occulted_flux(separation(t), p)) * 1e6
    bin_t, bin_flux = binned(t, flux, 1 / 3)
    _, bin_residual = binned(t, residual, 1 / 3)
    top, bottom = axes

    dots = dict(s=1.0, color=GREY, alpha=0.6, linewidths=0)
    binned_dots = dict(ms=2.4, color=PLANET, mec="white", mew=0.3)
    top.scatter(t, flux, **dots)
    top.plot(model_t, occulted_flux(separation(model_t), p), color=STAR)
    top.plot(bin_t, bin_flux, "o", **binned_dots)
    for k, tc in enumerate(contact_times(p)):
        for ax in axes:
            ax.axvline(tc, color=GREY, lw=0.5, ls=(0, (2, 2)), zorder=0)
        top.text(tc, 1.0042, f"T$_{k + 1}$", **CONTACT_LABEL)
    top.annotate("", (-2.87, 1 - p**2), (-2.87, 1.0), arrowprops=DOUBLE_ARROW)
    top.text(-2.79, 1 - p**2 / 2, r"$(R_p/R_*)^2$", ha="left", va="center")
    top.set_ylim(0.9845, 1.0042)
    top.set_yticks([0.985, 0.99, 0.995, 1.0])
    top.set_ylabel("Relative flux")
    top.tick_params(labelbottom=False)

    bottom.scatter(t, residual, **dots)
    bottom.plot(bin_t, bin_residual, "o", **binned_dots)
    bottom.axhline(0, color=STAR)
    bottom.set_ylim(-5000, 5000)
    bottom.set_yticks([-4000, 0, 4000])
    bottom.set_ylabel("Residual\n(ppm)")
    bottom.set_xlabel("Time from mid-transit (h)")
    bottom.set_xlim(-3.2, 3.2)


def plot_spectrum(ax: plt.Axes, p: float) -> None:
    """Simulated transmission spectrum over the model, with its absorbers marked."""
    rng = np.random.default_rng(107)
    wavelength = np.geomspace(0.58, 5.3, 1200)
    centres = np.geomspace(0.62, 5.0, 44)
    error = 40 + 25 * (centres < 1) + 20 * (centres > 4)
    observed = transit_depth(centres) * 1e6 + rng.normal(0, error)

    ax.axvspan(*BAND, color=STAR, alpha=0.15, lw=0)
    ax.text(np.sqrt(np.prod(BAND)), 12230, "Photometer\nband", ha="center", va="top", color=STAR)
    ax.plot(BAND, [p**2 * 1e6] * 2, color=STAR, lw=1.2)
    ax.plot(wavelength, transit_depth(wavelength) * 1e6, color=ATMOSPHERE)
    ax.errorbar(centres, observed, error, fmt="o", ms=2.2, color=PLANET, elinewidth=0.5, capsize=0)
    for molecule, bands in BANDS.items():
        for centre, _, _ in bands:
            peak = transit_depth(np.array([centre]))[0] * 1e6
            ax.text(centre, peak + 100, molecule, ha="center", va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(0.58, 5.3)
    ax.set_xticks([0.6, 1, 2, 3, 4, 5], ["0.6", "1", "2", "3", "4", "5"])
    ax.minorticks_off()
    ax.set_ylim(11550, 12250)
    ax.set_yticks([11600, 11800, 12000, 12200])
    ax.set_xlabel(r"Wavelength ($\mu$m)")
    ax.set_ylabel(r"$(R_p/R_*)^2$ (ppm)")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="116mm", theme=THEME, background="white")
    panels = fig.grid(
        [["orbit", "orbit", "photometry"], ["sky", "spectrum", "spectrum"]],
        width_ratios=(40, 34, 64),
        height_ratios=(1.45, 1),
        margins=("8mm", "3mm", "10mm", "13mm"),  # top, right, bottom, left
        gap=("13mm", "14mm"),  # between rows, between columns
    )
    p = band_radius()

    tex = THEME.vectex()
    labels = {
        "Rstar": vectex.render(r"$R_*$", **tex),
        "Rp": vectex.render(r"$R_p$", **tex | {"color": PLANET}),
        "observer": vectex.render("to observer", **tex),
        "orbit": vectex.render(rf"$a = {A_OVER_R:g}\,R_*$", **tex),
    }
    panels["orbit"].add(geometry_scene(labels, p), id="geometry-scene")
    for name, label in labels.items():
        fig.fill_slot(f"label-{name}", label)

    mpl_fig, axes = panels["photometry"].subplots(
        2, 1, sharex=True, gridspec_kw=dict(height_ratios=(3, 1), hspace=0.08)
    )
    plot_photometry(axes, p)
    panels["photometry"].add(mpl_fig, id="light-curve", fit="axes")

    mpl_fig, ax = panels["sky"].subplots()
    plot_sky(ax, p)
    panels["sky"].add(mpl_fig, id="sky-view", fit="axes")

    mpl_fig, ax = panels["spectrum"].subplots()
    plot_spectrum(ax, p)
    panels["spectrum"].add(mpl_fig, id="transmission-spectrum", fit="axes")

    for letter, panel in zip("abcd", panels.values(), strict=True):
        fig.label(letter, panel.nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"exoplanet_transit{suffix}")
    print(f"wrote {OUT / 'exoplanet_transit.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
