"""Stretching one DNA molecule in dual-trap optical tweezers, as a Nature figure.

A VecView scene of the assay -- two beads in focused laser traps, a lambda-DNA
tether between them -- beside three Matplotlib panels: the trap stiffness found
twice from a bead's Brownian motion, and the molecule's force-extension curve.
Vermillion marks the trap, blue the molecule. Scene labels are pinned by slots,
upright at 7 pt: VecTeX for F and x, plain theme-font text for lambda-DNA.

All data are simulated with fixed seeds: the bead's motion is the exact
discretized Ornstein-Uhlenbeck process; the stretching data follow the extensible
worm-like chain (Marko-Siggia) plus a two-state overstretching transition.

Usage:
    python examples/optical_tweezers.py     # requires vecview and TeX
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
TRAP = "#d55e00"  # Okabe-Ito vermillion: laser, beads, calibration
DNA = "#0072b2"  # Okabe-Ito blue: the molecule and its stretching data
BEAD = dict(fill="#ece6e1", highlight="#ffffff", stroke="#a39a92", stroke_width=0.6)
BEAM = dict(fill=TRAP, highlight="#fff4ec", fill_opacity=0.28, stroke=TRAP, stroke_opacity=0.35)
X, Z = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
R_BEAD, X_TRAP = 1.0, 3.4  # bead radius and trap position, in scene units

KT = 4.11  # pN nm at 25 C
P, S, L0 = 50.0, 1200.0, 16.5  # persistence length (nm), stretch modulus (pN), contour (um)
F_OS, DL_OS = 65.0, 0.7  # overstretching force (pN) and relative length gained
GAMMA = 6 * np.pi * 0.89e-3 * 0.5e-6 * 1e3  # Stokes drag of a 1 um bead in water, pN s/nm
KAPPA = 0.05  # trap stiffness, pN/nm
FS = 100e3  # sampling rate, Hz


# --- physics --------------------------------------------------------------------


def extension(force: np.ndarray) -> np.ndarray:
    """Extension (um) at a force (pN): extensible WLC plus a two-state overstretching.

    The Marko-Siggia interpolation F P / kT = 1/(4(1-z)^2) - 1/4 + z is solved
    for the relative entropic extension z by bisection; enthalpic stretching
    adds F/S, and the transition to overstretched DNA adds DL_OS of length.
    """
    lo, hi = np.zeros_like(force), np.full_like(force, 1 - 1e-9)
    for _ in range(60):
        z = (lo + hi) / 2
        too_long = 1 / (4 * (1 - z) ** 2) - 0.25 + z > force * P / KT
        hi, lo = np.where(too_long, z, hi), np.where(too_long, lo, z)
    overstretched = 1 / (1 + np.exp(-(force - F_OS) / 0.8))
    return L0 * (z + force / S + DL_OS * overstretched)


def bead_trace(n: int, seed: int = 4) -> np.ndarray:
    """Position (nm) of a trapped bead sampled at FS, exact for the Langevin equation."""
    rng = np.random.default_rng(seed)
    decay = np.exp(-KAPPA / GAMMA / FS)
    kicks = np.sqrt(KT / KAPPA * (1 - decay**2)) * rng.standard_normal(n)
    x = np.empty(n)
    x[0] = kicks[0]
    for i in range(1, n):
        x[i] = decay * x[i - 1] + kicks[i]
    return x


def power_spectrum(x: np.ndarray, block: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    """One-sided PSD (nm^2/Hz) averaged over blocks, without the zero frequency."""
    blocks = x[: x.size // block * block].reshape(-1, block)
    psd = 2 / (FS * block) * np.mean(np.abs(np.fft.rfft(blocks, axis=1)) ** 2, axis=0)
    return np.fft.rfftfreq(block, 1 / FS)[1:], psd[1:]


def fit_lorentzian(f: np.ndarray, psd: np.ndarray) -> tuple[float, float]:
    """Corner frequency and diffusion constant, from 1/S = pi^2 (fc^2 + f^2) / D.

    Each block-averaged point has the same relative error, hence the weights.
    """
    slope, intercept = np.polyfit(f**2, 1 / psd, 1, w=psd)
    return np.sqrt(intercept / slope), np.pi**2 / slope


def lorentzian(f: np.ndarray, fc: float, d: float) -> np.ndarray:
    return d / (np.pi**2 * (fc**2 + f**2))


# --- panel a: the assay ---------------------------------------------------------


def tweezers_scene(boxes: dict[str, tuple[float, float]]) -> vecview.Scene:
    """Two beads in two laser foci, the DNA double helix tethered between them."""
    cam = vecview.OrthographicCamera(azim_deg=-90.0, elev_deg=22.0, scale=34.0)
    scene = vecview.Scene(cam, pad=2.0)
    centers = (-X_TRAP * X, X_TRAP * X)

    for k, c in enumerate(centers):  # each beam focused onto its bead: an hourglass
        for side in (-1, 1):
            name = f"beam-{k}-{'in' if side < 0 else 'out'}"
            scene.cone(5, c + 2.6 * side * Z, c, 1.25, end=False, id=name, class_="laser", **BEAM)
        scene.gaussian(6, c, X, Z, 1.5, 1.5, id=f"focus-{k}", color=TRAP, opacity=0.35)

    scene.sort_by_depth(10)
    for k, c in enumerate(centers):
        scene.sphere(10, c, R_BEAD, id=f"bead-{k}", class_="bead", **BEAD)
    start, end = centers[0] + 0.8 * R_BEAD * X, centers[1] - 0.8 * R_BEAD * X
    turns = np.linalg.norm(end - start) / 0.38
    for k, phase in enumerate((0.0, 150.0)):  # the minor groove is narrower than the major
        strand = vecview.helix(start, X, 0.13, 0.38, turns, n_per_turn=40, phase_deg=phase)
        scene.tube(
            10, strand, 0.04, chunk=2, fill=DNA, stroke="#00466e", stroke_width=0.4, id=f"dna-{k}"
        )

    pull = dict(shaft_r=0.06, head_r=0.17, head_len=0.38, fill=INK, class_="force")
    for k, sign in enumerate((-1, 1)):  # the pull on each bead, outward
        scene.arrow3d(
            30, centers[k] + sign * 1.15 * R_BEAD * X, sign * X, 1.1, id=f"force-{k}", **pull
        )

    # The extension, bead surface to bead surface, as a dimension line below.
    below = -1.4 * Z
    span = 2 * (X_TRAP - R_BEAD)
    ruler = vecview.double_arrow_shape(below, X, span, (0, 1, 0), 0.025, 0.16, 0.28)
    scene.polygon(30, ruler, fill=DNA, id="extension")

    for name, at, align, dx, dy in (
        ("F", centers[1] + 2.3 * R_BEAD * X, "west", 2, 0),
        ("x", below, "north", 0, 3),
        ("DNA", (start + end) / 2 + 0.2 * Z, "south", 0, -6),
    ):
        scene.slot(40, at, *boxes[name], align=align, dx=dx, dy=dy, id=f"label-{name}")
    return scene


# --- panels b-d: the plots ------------------------------------------------------


def plot_spectrum(ax: plt.Axes, f: np.ndarray, psd: np.ndarray, fc: float, d: float) -> None:
    """Log-binned PSD, the fitted Lorentzian, and the stiffness its corner gives."""
    bins = np.digitize(f, np.geomspace(f[0], f[-1], 40))
    counts = np.bincount(bins)
    f_mean, psd_mean = (np.bincount(bins, y)[counts > 0] / counts[counts > 0] for y in (f, psd))
    khz = 1e-3  # in kHz, so that log ticks read as plain numbers
    ax.plot(f_mean * khz, psd_mean / khz, "o", ms=2.2, color=TRAP, mec="none")
    # Sampling folds the spectrum about FS/2, so the model is summed over images.
    images = sum(lorentzian(f + k * FS, fc, d) for k in range(-20, 21))
    ax.plot(f * khz, images / khz, color=INK)
    ax.axvline(fc * khz, ymin=0.16, color=GREY, lw=0.5, ls="--")
    ax.text(fc * khz * 1.2, 300, rf"$f_c = {fc:.0f}$ Hz", va="top")
    kappa = rf"$\kappa = 2\pi\gamma f_c = {2 * np.pi * GAMMA * fc:.3f}$ pN nm$^{{-1}}$"
    ax.text(0.04, 0.04, kappa, transform=ax.transAxes)
    ax.set(xscale="log", yscale="log", xlim=(0.02, FS / 2 * khz), ylim=(0.01, 500))
    ax.set_xticks([0.1, 1, 10], ["0.1", "1", "10"])
    ax.set_yticks([0.01, 1, 100], ["0.01", "1", "100"])
    ax.set(xlabel="Frequency (kHz)", ylabel=r"PSD (nm$^2$ kHz$^{-1}$)")


def plot_histogram(ax: plt.Axes, x: np.ndarray) -> None:
    """Bead positions and the Boltzmann distribution of a harmonic well."""
    variance = x.var()
    grid = np.linspace(-30, 30, 200)
    boltzmann = np.exp(-(grid**2) / (2 * variance)) / np.sqrt(2 * np.pi * variance)
    bins = np.linspace(-30, 30, 41)
    ax.hist(x, bins=bins, density=True, histtype="stepfilled", color=TRAP, alpha=0.35, lw=0)
    ax.plot(grid, boltzmann, color=INK)
    kappa = rf"$\kappa = k_BT/\sigma_x^2 = {KT / variance:.3f}$ pN nm$^{{-1}}$"
    ax.text(0.5, 0.97, kappa, transform=ax.transAxes, ha="center", va="top")
    ax.set(xlim=(-30, 30), ylim=(0, boltzmann.max() * 1.45), xticks=[-25, 0, 25])
    ax.set_yticks([0, 0.02, 0.04], ["0", "0.02", "0.04"])
    ax.set(xlabel="Bead position (nm)", ylabel=r"Probability density (nm$^{-1}$)")


def plot_stretching(ax: plt.Axes) -> None:
    """Measured force-extension points and the eWLC model, regimes named in place."""
    force = np.linspace(0.05, 75, 4000)
    x = extension(force)
    rng = np.random.default_rng(16)
    xs = np.linspace(10.5, 27.5, 140)
    fs = np.interp(xs, x, force) + rng.normal(0, 0.6, xs.size)
    xs = xs + rng.normal(0, 0.04, xs.size)
    ax.plot(xs, fs, "o", ms=2.2, color=DNA, mec="none", label="λ-DNA")
    ax.plot(x, force, color=INK, label=f"eWLC, $P$ = {P:.0f} nm, $S$ = {S:,.0f} pN")
    ax.axvline(L0, color=GREY, lw=0.5, ls="--")
    ax.text(L0 - 0.3, 78, r"$L_0$", ha="right", va="top", color=GREY)
    ax.text(12.5, 5, "entropic", ha="center")
    ax.text(L0 + 0.5, 35, "enthalpic", ha="left")
    ax.text(22.0, F_OS + 3, "overstretching", ha="center", va="bottom")
    ax.legend(loc="lower right", frameon=False, handlelength=1.2)
    ax.set(xlim=(10, 28), ylim=(0, 80), yticks=[0, 20, 40, 60, 80])
    ax.set(xlabel=r"Extension $x$ (µm)", ylabel=r"Force $F$ (pN)")


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="122mm", theme=THEME)
    panels = fig.grid(
        [["assay", "assay", "spectrum"], ["stretching", "stretching", "histogram"]],
        margins=("8mm", "3mm", "10mm", "12mm"),  # top, right, bottom, left
        gap=("14mm", "16mm"),  # between rows, between columns
    )

    tex = THEME.vectex()
    labels = {
        "F": vectex.render(r"$F$", **tex),
        "x": vectex.render(r"$x$", **tex | {"color": DNA}),
    }
    boxes = {name: (label.width_px, label.height_px) for name, label in labels.items()}
    # Plain text, not TeX, so that its lambda is the same Heros glyph as in panel c.
    labels["DNA"] = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="30pt" height="7pt" viewBox="0 0 30 7">'
        f'<text x="15" y="5.6" font-family="{THEME.font.family}" font-size="7" fill="{DNA}"'
        ' text-anchor="middle">λ-DNA</text></svg>'
    )
    boxes["DNA"] = (40.0, 28 / 3)  # 30 pt by 7 pt, in px
    panels["assay"].add(tweezers_scene(boxes), id="assay-scene")
    for name, label in labels.items():
        fig.fill_slot(f"label-{name}", label)

    x = bead_trace(64 * 4096)
    f, psd = power_spectrum(x)
    fc, d = fit_lorentzian(f[f < 5e3], psd[f < 5e3])

    for name, plot in (
        ("spectrum", lambda ax: plot_spectrum(ax, f, psd, fc, d)),
        ("stretching", plot_stretching),
        ("histogram", lambda ax: plot_histogram(ax, x)),
    ):
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
        fig.save(OUT / f"optical_tweezers{suffix}")
    print(f"wrote {OUT / 'optical_tweezers.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
