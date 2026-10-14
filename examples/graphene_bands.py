"""Graphene's Dirac electrons, from nearest-neighbour tight binding.

A Nature double-column figure in four panels: the honeycomb lattice with its
two-atom unit cell (a VecView scene), the two bands over the Brillouin zone,
touching in cones at its corners (a second scene), and two Matplotlib panels
sharing an energy axis: the bands along Gamma-K-M-Gamma and the density of
states. Every label in the scenes is a VecTeX fragment pinned upright at 7 pt.

Everything is computed here from the two-site Bloch Hamiltonian, whose
off-diagonal element is -t f(k), with t = 2.7 eV and a carbon-carbon distance
a = 1.42 Å: the bands exactly, the density of states by sampling the zone on a
fine grid and broadening each level by 60 meV. Near K the bands are the cones
E = ±ħv_F|q|, with ħv_F = 3ta/2, so v_F = 0.87e6 m/s. Nothing is measured.

Usage:
    python examples/graphene_bands.py     # requires vecview and TeX
"""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vectex
import vecview
from vecview import outlines

from figworks import Figure, load_theme
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

THEME = load_theme("nature")
plt.rcParams.update(theme_rc(THEME))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})

INK = "#262626"
GREY = "#8a9099"
CONDUCTION = ("#fbe3d3", "#d55e00")  # light near E = 0, dark at the band edge
VALENCE = ("#d6e6f3", "#0072b2")
SITES = {"A": ("#3a3f47", "#9aa1ab"), "B": ("#c9ced6", "#ffffff")}  # fill, highlight
CELL = "#009e73"
DASHED = dict(color=INK, lw=0.5, ls=(0, (3, 2)))
ATOM = dict(stroke="#30343a", stroke_width=0.5, class_="atom")
VECTOR = dict(normal=(0, 0, 1), shaft_w=0.08, head_w=0.3, head_len=0.38, fill=CELL)
UNIT_CELL = dict(
    fill=CELL, fill_opacity=0.16, stroke=CELL, stroke_width=0.6, stroke_dasharray="3 2"
)
MESH = dict(stroke_width=0.4, stroke_linejoin="round")
DROP = dict(stroke=GREY, stroke_width=0.5, stroke_dasharray="2 2")

T_HOP = 2.7  # eV
A_CC = 1.42  # Å
HBAR_VF = 1.5 * T_HOP * A_CC  # eV Å
NEIGHBOURS = A_CC * np.array([[1.0, 0.0], [-0.5, np.sqrt(3) / 2], [-0.5, -np.sqrt(3) / 2]])
LATTICE = A_CC * np.array([[1.5, np.sqrt(3) / 2], [1.5, -np.sqrt(3) / 2]])  # a1, a2
K_POINT = (2 * np.pi / (3 * A_CC)) * np.array([1.0, 1 / np.sqrt(3)])
M_POINT = (2 * np.pi / (3 * A_CC)) * np.array([1.0, 0.0])


# --- physics --------------------------------------------------------------------


def band_energy(k: np.ndarray) -> np.ndarray:
    """The upper band t |f(k)|, f = sum_j exp(i k . delta_j); the lower is its negative."""
    return T_HOP * np.abs(np.exp(1j * np.tensordot(k, NEIGHBOURS.T, axes=1)).sum(axis=-1))


def zone_corners() -> np.ndarray:
    """The six corners of the hexagonal Brillouin zone: K at 30 + 120n degrees, K' between."""
    return outlines.regular(6, np.linalg.norm(K_POINT), rotate_deg=30)


def density_of_states(energy: np.ndarray, n: int = 600, width: float = 0.06) -> np.ndarray:
    """States per eV and unit cell, spin included, by sampling the zone on an n x n grid.

    A uniform grid over the reciprocal cell spanned by b1, b2 samples the zone
    exactly, up to translations; each level is broadened into a Gaussian.
    """
    s = (np.arange(n) + 0.5) / n
    k = np.stack(np.meshgrid(s, s), axis=-1) @ (2 * np.pi * np.linalg.inv(LATTICE).T)
    upper = band_energy(k).ravel()
    counts, _ = np.histogram(np.r_[upper, -upper], bins=energy.size, range=energy[[0, -1]])
    step = (energy[-1] - energy[0]) / energy.size
    kernel = np.exp(-0.5 * (np.arange(-4 * width, 4 * width + step, step) / width) ** 2)
    return 2 * np.convolve(counts, kernel / kernel.sum(), mode="same") / (n * n * step)


def linear_dos(energy: np.ndarray) -> np.ndarray:
    """The Dirac-cone density of states 2|E| A_c / (pi (hbar v_F)^2), per unit cell."""
    return 2 * np.abs(energy) * (3 * np.sqrt(3) / 2 * A_CC**2) / (np.pi * HBAR_VF**2)


# --- the scenes -----------------------------------------------------------------


def tex_slot(scene: vecview.Scene, label: vectex.VectexFragment, at, name: str, **place) -> None:
    """Reserve an upright slot the size of ``label`` at ``at``, for the figure to fill."""
    scene.slot(40, at, label.width_px, label.height_px, id=f"label-{name}", **place)


def honeycomb_flake(radius: float) -> dict[str, np.ndarray]:
    """A and B sites, in units of a, of the hexagons centred within ``radius`` of one."""
    a1, a2 = LATTICE / A_CC
    n = np.arange(-4, 5)
    centres = np.array([i * a1 + j * a2 + (2, 0) for i in n for j in n])
    centres = centres[np.linalg.norm(centres - (2, 0), axis=1) < radius]
    ring = np.exp(1j * np.radians(60 * np.arange(6)))
    sites = np.round(centres[:, None] + np.c_[ring.real, ring.imag], 6).reshape(-1, 2)
    sites = np.unique(sites, axis=0)
    cells = np.linalg.solve(np.c_[a1, a2], sites.T).T  # integer for the A sublattice
    on_a = np.all(np.isclose(cells, np.round(cells), atol=1e-4), axis=1)
    return {"A": sites[on_a], "B": sites[~on_a]}


def lattice_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """A honeycomb flake: A and B atoms, their bonds, and the unit cell spanned by a1, a2."""
    scene = vecview.Scene(vecview.OrthographicCamera(azim_deg=-90, elev_deg=42, scale=30), pad=2)
    scene.sort_by_depth(20)
    sites = honeycomb_flake(3.1)
    for i, p in enumerate(sites["A"]):
        for j, q in enumerate(sites["B"]):
            if np.linalg.norm(p - q) < 1.01:
                scene.cylinder(
                    20, (*p, 0), (*q, 0), 0.07, ends=False, fill="#b9bec6", id=f"bond-{i}-{j}"
                )
    for kind, (fill, highlight) in SITES.items():
        for i, p in enumerate(sites[kind]):
            scene.sphere(
                20, (*p, 0), 0.25, fill=fill, highlight=highlight, id=f"site-{kind}-{i}", **ATOM
            )

    a1, a2 = LATTICE / A_CC
    rhombus = [(0, 0, 0), (*a1, 0), (*(a1 + a2), 0), (*a2, 0)]
    scene.polygon(10, rhombus, id="unit-cell", **UNIT_CELL)
    for name, v in (("a1", a1), ("a2", a2)):
        scene.arrow(20, (0, 0, 0.12), (*v, 0), np.linalg.norm(v), id=f"vector-{name}", **VECTOR)
    # The cell's own two atoms, A at the origin and B one bond to its right.
    for name, at, place in (
        ("a1", (0.5, np.sqrt(3) / 2, 0.12), dict(align="center")),
        ("a2", (0.5, -np.sqrt(3) / 2, 0.12), dict(align="center")),
        ("A", (0, 0, 0), dict(align="east", dx=-10)),
        ("B", (1, 0, 0), dict(align="west", dx=10)),
    ):
        tex_slot(scene, labels[name], at, name, **place)
    return scene


def mix(a: str, b: str, t: float) -> str:
    """The colour a fraction ``t`` of the way from hex ``a`` to hex ``b``."""
    ca, cb = ([int(c[i : i + 2], 16) for i in (1, 3, 5)] for c in (a, b))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb, strict=True))


def zone_patches(cone_radius: float) -> list[np.ndarray]:
    """Grids of k, in units of 1/a, covering the zone plus a whole disk at each corner.

    The zone is six triangles fanning out from Gamma; each corner adds the two
    thirds of a disk that lie outside the zone, so every Dirac cone is whole.
    """
    corners = zone_corners() * A_CC
    s = np.linspace(0, 1, 15)[:, None, None]
    u = np.linspace(0, 1, 11)[None, :, None]
    rho = np.linspace(0, cone_radius, 7)[:, None, None]
    patches = []
    for corner, following in zip(corners, np.roll(corners, -1, axis=0), strict=True):
        patches.append(s * (corner + u * (following - corner)))
        phi = np.arctan2(corner[1], corner[0]) + np.radians(np.linspace(-120, 120, 33))
        patches.append(corner + rho * np.stack([np.cos(phi), np.sin(phi)], axis=-1))
    return patches


def band_scene(labels: dict[str, vectex.VectexFragment]) -> vecview.Scene:
    """Both bands over the zone, coloured by |E|, touching in a cone at every corner."""
    scene = vecview.Scene(vecview.OrthographicCamera(azim_deg=-62, elev_deg=20, scale=50), pad=2)
    scene.sort_by_depth(20)
    height = 0.5 / T_HOP  # scene units per eV; momentum in units of 1/a

    for p, k in enumerate(zone_patches(0.3 * np.linalg.norm(K_POINT) * A_CC)):
        energy = height * band_energy(k / A_CC)
        for sign, (light, dark), name in ((1, CONDUCTION, "conduction"), (-1, VALENCE, "valence")):
            for face in vecview.surface_faces(k[..., 0], k[..., 1], sign * energy):
                if np.ptp(face.points[:, :2], axis=0).max() < 1e-9:
                    continue  # the collapsed quads at the apex of a fan
                fill = mix(light, dark, abs(face.points[:, 2].mean()) / (3 * T_HOP * height))
                edge = mix(fill, "#000000", 0.18)
                scene.polygon(
                    20,
                    face.points,
                    fill=fill,
                    stroke=edge,
                    id=f"{name}-{p}-{face.name}",
                    class_=["band", name],
                    **MESH,
                )

    floor = -4.2 * T_HOP * height
    corners = zone_corners() * A_CC
    zone = np.column_stack([corners, np.full(6, floor)])
    scene.polygon(10, zone, fill="#eef0f3", stroke=GREY, stroke_width=0.6, id="brillouin-zone")
    for i, (x, y) in enumerate(corners):
        scene.polyline(20, [(x, y, floor), (x, y, 0)], id=f"dirac-drop-{i}", **DROP)
    tex_slot(scene, labels["Gamma"], (0, 0, floor), "Gamma", align="center")
    for name, i in (("K", 4), ("Kp", 5)):
        tex_slot(scene, labels[name], (*corners[i], floor), name, align="north", dy=3)
    return scene


# --- the plots ------------------------------------------------------------------


def energy_axis(ax: plt.Axes, labelled: bool) -> None:
    ax.set_ylim(-9, 9)
    ax.set_yticks([-8, -4, 0, 4, 8], None if labelled else [])


def plot_bands(ax: plt.Axes) -> None:
    """Both bands along Gamma-K-M-Gamma, with the Dirac cone dashed near K."""
    corners = [np.zeros(2), K_POINT, M_POINT, np.zeros(2)]
    k = np.concatenate([np.linspace(p, q, 200) for p, q in pairwise(corners)])
    x = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(k, axis=0), axis=1))]
    stops = x[[0, 200, 400, -1]]  # Gamma, K, M, Gamma
    energy = band_energy(k)
    ax.plot(x, energy, color=CONDUCTION[1], gid="conduction-band")
    ax.plot(x, -energy, color=VALENCE[1], gid="valence-band")
    ax.text(0.12, 6.4, r"$\pi^*$", color=CONDUCTION[1], va="top")
    ax.text(0.12, -6.4, r"$\pi$", color=VALENCE[1], va="bottom")

    q = np.array([-0.5, 0.0, 0.5])  # 1/Å from K
    for sign in (1, -1):
        ax.plot(stops[1] + q, sign * HBAR_VF * np.abs(q), **DASHED)
    ax.text(stops[1] + 0.52, HBAR_VF * 0.5, r"$E = \pm\hbar v_F|q|$", va="bottom")
    for d in stops[1:-1]:
        ax.axvline(d, color=GREY, lw=0.25, zorder=0)
    ax.axhline(0, color=GREY, lw=0.25, zorder=0)
    ax.set_xticks(stops, [r"$\Gamma$", "K", "M", r"$\Gamma$"])
    ax.set_xlim(stops[0], stops[-1])
    ax.set_ylabel("Energy (eV)")
    energy_axis(ax, labelled=True)


def plot_dos(ax: plt.Axes) -> None:
    """The density of states, with its linear Dirac-cone onset dashed."""
    energy = np.linspace(-9.0, 9.0, 1801)
    dos = density_of_states(energy)
    for sign, color in ((1, CONDUCTION[1]), (-1, VALENCE[1])):
        side = sign * energy >= 0
        ax.fill_betweenx(energy[side], dos[side], color=color, alpha=0.18, lw=0)
        ax.plot(dos[side], energy[side], color=color)
    low = np.abs(energy) < 3.5
    ax.plot(linear_dos(energy[low]), energy[low], **DASHED)
    ax.set_xlim(0, 0.75)
    ax.set_xticks([0, 0.3, 0.6], ["0", "0.3", "0.6"])
    ax.set_xlabel(r"DOS (eV$^{-1}$ cell$^{-1}$)")
    energy_axis(ax, labelled=False)


# --- the figure -----------------------------------------------------------------


def build_figure() -> Figure:
    fig = Figure(width=THEME.page["double"], height="121mm", theme=THEME)
    # Two rows of their own, so c and d can sit closer than a and b; margins: t, r, b, l.
    panels = fig.grid(
        [["lattice", "zone"]],
        width_ratios=(1, 1.15),
        margins=("7mm", "3mm", "60mm", "6mm"),
        gap="8mm",
    )
    panels |= fig.grid(
        [["bands", "dos"]], width_ratios=(3, 1), margins=("71mm", "6mm", "10mm", "14mm"), gap="4mm"
    )

    tex = {"a1": r"$\mathbf{a}_1$", "a2": r"$\mathbf{a}_2$", "A": "A", "B": "B"}
    tex |= {"Gamma": r"$\mathrm{\Gamma}$", "K": "K", "Kp": "K$'$"}
    style = THEME.vectex()
    labels = {
        name: vectex.render(source, **style | {"color": CELL if name[0] == "a" else INK})
        for name, source in tex.items()
    }
    panels["lattice"].add(lattice_scene(labels), id="lattice-scene")
    panels["zone"].add(band_scene(labels), id="band-scene")
    for name, label in labels.items():
        fig.fill_slot(f"label-{name}", label)

    for name, plot in (("bands", plot_bands), ("dos", plot_dos)):
        mpl_fig, ax = panels[name].subplots()
        plot(ax)
        panels[name].add(mpl_fig, id=f"{name}-plot", fit="axes")

    fig.label("a", panels["lattice"].nw)
    fig.label("b", panels["zone"].nw)
    fig.label("c", (panels["lattice"].x, panels["bands"].y))  # in line with a
    fig.label("d", panels["dos"].nw)
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    print(fig.check().summary())
    for suffix in (".svg", ".pdf", ".png"):
        fig.save(OUT / f"graphene_bands{suffix}")
    print(f"wrote {OUT / 'graphene_bands.svg'}, PDF, and PNG")


if __name__ == "__main__":
    main()
