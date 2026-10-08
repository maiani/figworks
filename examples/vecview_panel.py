"""Place a VecView scene beside a Matplotlib plot in one composed figure.

The point of the example is that no adapter is involved: `vecview.Scene` exposes
`to_svg_document()`, which is the whole protocol `Panel.add` needs, so FigWorks
treats a 3D schematic exactly as it treats a Matplotlib figure or a VecTeX
equation.

Usage:
    python examples/vecview_panel.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vecview

from figworks import Figure
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"

# Plots use the figure's typeface, words and math alike.
plt.rcParams.update(theme_rc())

SLAB = dict(center=(0.0, 0.0, -0.45), size=(11.0, 9.0, 0.9))
PHI_Q = 22.5
COLORS = dict(top="#eef1f5", side="#cfd6e0", edge="#8b96a6", texture="#2f6fb0", twist="#1a8f4c")


def build_scene() -> vecview.Scene:
    """A slab with an in-plane spin texture and its modulation direction.

    `background` is left transparent and `pad` kept small: a white rectangle would
    cover a neighbouring panel's overhang, and padding shrinks the drawing inside
    its panel because FigWorks scales the scene to fit.
    """
    cam = vecview.OrthographicCamera(azim_deg=35.0, elev_deg=24.0, scale=62.0)
    scene = vecview.Scene(cam, pad=6.0)

    # `cull=True` keeps only the walls this camera can see, and keeps doing so if
    # the scene is later reprojected. The top is styled separately so the texture
    # beneath it reads through.
    box = vecview.box_faces(**SLAB)
    edge = dict(stroke=COLORS["edge"], stroke_width=1.6, stroke_linejoin="round")
    scene.faces(
        10,
        [f for f in box if f.name == "+z"],
        cull=True,
        fill=COLORS["top"],
        fill_opacity=0.86,
        id="slab",
        **edge,
    )
    # `faces` suffixes an id per face, so the walls get slab-px / slab-py.
    scene.faces(
        11, [f for f in box if f.name != "+z"], cull=True, fill=COLORS["side"], id="slab", **edge
    )

    # A sparse spin texture: flat in-plane arrows, so they foreshorten with the slab.
    q = vecview.in_plane_dir(PHI_Q)
    x, y = np.meshgrid(np.linspace(-4.4, 4.4, 9), np.linspace(-3.5, 3.5, 7))
    phase = 0.7 * (q[0] * x + q[1] * y)
    for j in range(y.shape[0]):
        for i in range(x.shape[1]):
            scene.polygon(
                15,
                vecview.arrow_shape(
                    (x[j, i], y[j, i], 0.01),
                    (np.cos(phase[j, i]), np.sin(phase[j, i]), 0.0),
                    0.7,
                    normal=(0, 0, 1),
                    shaft_w=0.08,
                    head_w=0.26,
                    head_len=0.26,
                    pivot="mid",
                ),
                fill=COLORS["texture"],
                fill_opacity=0.6,
            )

    # The modulation direction, given an id so it stays selectable after placement.
    scene.polygon(
        20,
        vecview.arrow_shape(
            -q * 1.9 + np.array([0.0, 0.0, 0.03]),
            q,
            3.9,
            normal=(0, 0, 1),
            shaft_w=0.10,
            head_w=0.40,
            head_len=0.48,
        ),
        fill=COLORS["twist"],
        id="twist-arrow",
    )
    return scene


def build_plot() -> plt.Figure:
    """A stand-in spectrum, so the figure has something to compose the scene against."""
    omega = np.linspace(0.05, 1.2, 400)
    theta = 90.0 - PHI_Q * (1.0 + np.tanh((omega - 0.55) / 0.08)) / 2.0 * 2.0
    mpl_fig, ax = plt.subplots(figsize=(3.0, 2.4))
    ax.plot(omega, 90.0 - theta, color="#6a2fb5")
    ax.axvline(0.55, color="#8b96a6", linestyle="--", linewidth=0.9)
    ax.set_xlabel(r"$\omega$")
    ax.set_ylabel(r"$\theta_+$ (deg)")
    mpl_fig.tight_layout()
    return mpl_fig


def build_figure() -> Figure:
    """The composed figure: the scene in panel a, the plot in panel b."""
    fig = Figure(width="170mm", height="76mm")
    # Panels start below and right of the margin so `label`'s default -3mm/-2mm
    # offset leaves the panel letters on the canvas.
    geometry = fig.panel("geometry", x="12mm", y="12mm", w="72mm", h="56mm")
    geometry.add(build_scene(), id="slab-scene")

    spectrum = fig.panel("spectrum", x="92mm", y="12mm", w="70mm", h="56mm")
    spectrum.add(build_plot(), id="spectrum-plot")

    fig.label("a", anchor=geometry.nw)
    fig.label("b", anchor=spectrum.nw)

    # Ids given inside the scene survive placement, so restyling reaches through.
    fig.select("#twist-arrow").set_style(fill="#c2185b")
    return fig


def main() -> None:
    OUT.mkdir(exist_ok=True)
    fig = build_figure()
    for suffix in (".svg", ".png"):
        fig.save(OUT / f"vecview_panel{suffix}")
    print(f"wrote {OUT / 'vecview_panel.svg'} and PNG")


if __name__ == "__main__":
    main()
