"""Project a Matplotlib plot onto a plane inside a 3D scene.

`Scene.plane` reserves a rectangle of a world plane as an empty group carrying
the affine transform that maps content coordinates in [0,1]^2 onto that
rectangle. `Figure.fill_plane` then normalizes a Matplotlib figure onto the unit
square, so the plot ends up lying *in* the plane -- foreshortened and sheared
with the geometry -- instead of flat on top of the picture.

This is exact rather than approximate because an orthographic projection is an
affine map of world space; restricted to a plane it stays affine, which is
precisely what an SVG `matrix` expresses. A perspective camera would give a
homography instead, which `matrix` cannot represent.

Usage:
    python examples/vecview_plane_plot.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import vecview

from figforge import Figure

OUT = Path(__file__).resolve().parent / "out"

AZIM, ELEV, SCALE = 35.0, 26.0, 62.0
LX, LY, THICK = 12.0, 10.0, 0.7

# The plot's own aspect. The plane rectangle is sized to match it, since
# fill_plane normalizes onto the unit square and would otherwise stretch it.
FIG_W, FIG_H = 3.2, 2.2
PLOT_W = 8.4
PLOT_H = PLOT_W * FIG_H / FIG_W

COLORS = dict(top="#eef1f5", side="#cfd6e0", edge="#8b96a6", wall="#e8ecf2", beam="#d62828")


def build_plot() -> plt.Figure:
    """A plot with a transparent background, so the slab shows through it."""
    x = np.linspace(0.0, 1.2, 400)
    mpl_fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.plot(x, np.tanh((x - 0.55) / 0.09) * 0.5 + 0.5, color="#6a2fb5", linewidth=2.0)
    ax.axvline(0.55, color="#8b96a6", linestyle="--", linewidth=1.0)
    ax.set_xlabel(r"$\omega$")
    ax.set_ylabel("transmission")
    ax.set_ylim(-0.05, 1.05)
    mpl_fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.75)
    mpl_fig.tight_layout(pad=0.4)
    return mpl_fig


def build_scene() -> vecview.Scene:
    cam = vecview.OrthographicCamera(azim_deg=AZIM, elev_deg=ELEV, scale=SCALE)
    scene = vecview.Scene(cam, pad=6.0)

    # The slab, with only its camera-facing walls.
    box = vecview.box_faces(center=(0, 0, -THICK / 2), size=(LX, LY, THICK))
    edge = dict(stroke=COLORS["edge"], stroke_width=1.4, stroke_linejoin="round")
    scene.faces(
        10, [f for f in box if f.name == "+z"], cull=True, fill=COLORS["top"], id="slab", **edge
    )
    scene.faces(
        11, [f for f in box if f.name != "+z"], cull=True, fill=COLORS["side"], id="slab", **edge
    )

    # Plane A: the plot lying flat on the slab's top face.
    #
    # Which world directions to use for the content's axes is a real choice.
    # The content stays upright and unmirrored exactly when its +x projects
    # rightward and its +y projects downward -- i.e. the matrix has a > 0 and
    # d > 0. A positive determinant alone is not enough: a 180-degree rotation
    # has one too, which is how an earlier version of this example ended up
    # with every label upside down.
    #
    # At this azimuth world +y projects rightward and world +x downward, so
    # those are the content axes. Using `cam.screen_basis()` here would also be
    # readable, but its edges project to *pure* screen axes by construction, so
    # the plot would land as an upright rectangle with no foreshortening -- in
    # the plane geometrically, yet visually pasted on.
    u_hat = np.array([0.0, 1.0, 0.0])  # content +x  -> world +y (rightward)
    v_hat = np.array([1.0, 0.0, 0.0])  # content +y  -> world +x (downward)
    scene.plane(
        15,
        origin=-(u_hat * PLOT_W + v_hat * PLOT_H) / 2 + np.array([0.0, 0.0, 0.01]),
        u_edge=u_hat * PLOT_W,
        v_edge=v_hat * PLOT_H,
        id="plot-flat",
    )

    # Plane B: the same plot upright on a back wall, to show any plane works.
    # Same rule, applied in the x-z plane: world -x projects rightward here and
    # world -z downward.
    wall_w = 6.2
    wall_h = wall_w * FIG_H / FIG_W
    wu = np.array([-1.0, 0.0, 0.0])
    wv = np.array([0.0, 0.0, -1.0])
    # Lifted clear of the slab. The wall stands behind and above it, but the
    # slab's nearer half still overlaps it in projection, and the slab is drawn
    # at a higher layer -- so anything less than this gets its bottom edge cut.
    wall_centre = np.array([0.0, LY / 2, wall_h / 2 + 3.4])
    scene.polygon(
        8,
        vecview.rect_shape(wall_centre, wu, wv, wall_w * 1.34, wall_h * 1.26),
        fill=COLORS["wall"],
        stroke=COLORS["edge"],
        stroke_width=1.2,
    )
    scene.plane(
        9,
        origin=wall_centre
        - (wu * wall_w + wv * wall_h) / 2
        - np.array([0.0, 0.01, 0.0]),
        u_edge=wu * wall_w,
        v_edge=wv * wall_h,
        id="plot-upright",
    )

    # A beam crossing the flat plot, drawn at a higher layer -- the point of
    # `plane` participating in the layer stack rather than being pasted on top.
    scene.polyline(
        20,
        np.array([[2.0, -1.0, 5.0], [2.0, -1.0, -THICK - 3.0]]),
        stroke=COLORS["beam"],
        stroke_width=2.6,
        stroke_opacity=0.9,
    )
    return scene


def main() -> None:
    OUT.mkdir(exist_ok=True)
    plot = build_plot()

    fig = Figure(width="150mm", height="110mm")
    panel = fig.panel("scene", x="5mm", y="5mm", w="140mm", h="100mm")
    panel.add(build_scene(), id="scene-3d")

    # Both planes take the same plot; each is normalized onto its own unit square.
    fig.fill_plane("plot-flat", plot)
    fig.fill_plane("plot-upright", plot)

    for suffix in (".svg", ".png"):
        fig.save(OUT / f"vecview_plane_plot{suffix}")
    print(f"wrote {OUT / 'vecview_plane_plot.svg'} and PNG")


if __name__ == "__main__":
    main()
