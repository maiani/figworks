# 3D scenes

[VecView](https://github.com/maiani/vecview) draws layered 3D schematics — a slab, a
beam, a crystal lattice, an optical bench — as a single SVG document. Like VecTeX
fragments, an `vecview.Scene` implements FigWorks's SVG-document protocol, so it
needs no adapter:

```python
import figworks
import vecview

cam = vecview.OrthographicCamera(azim_deg=35, elev_deg=24, scale=62)
scene = vecview.Scene(cam, pad=8)

slab = vecview.box_faces(center=(0, 0, -0.45), size=(11, 9, 0.9))
scene.faces(10, cam.visible(slab), fill="#cfd6e0", stroke="#8b96a6", stroke_width=1.6)

fig = figworks.Figure(width="170mm", height="80mm")
geometry = fig.panel("geometry", x="8mm", y="8mm", w="72mm", h="64mm")
geometry.add(scene, id="slab-scene")

spectrum = fig.panel("spectrum", x="90mm", y="8mm", w="72mm", h="64mm")
spectrum.add(mpl_fig, id="spectrum-plot")

fig.label("a", anchor=geometry.nw)
fig.label("b", anchor=spectrum.nw)
fig.save("figure.pdf")
```

`Panel.add` reads the scene's intrinsic size from its `viewBox`, scales it
uniformly, and centres it in the panel.

## Install

`vecview` is **not on PyPI** yet, so install it from a checkout:

```bash
python -m pip install -e /path/to/vecview
```

It is deliberately not a FigWorks dependency. FigWorks places any object exposing
`to_svg_document()`, so the integration costs nothing when `vecview` is absent.

## Settings that matter when composing

Configure `pad` and `background` on the `Scene` constructor, not at a `render`
call — FigWorks invokes `to_svg_document()` with no arguments:

- **`pad`** is in scene units and survives into the panel as margin. Because the
  scene is scaled to fit, padding shrinks the drawing within its panel. Use a
  small value, or `0`, when the panel layout already provides spacing.
- **`background`** should stay `None`. A white rectangle behind one scene covers a
  neighbouring panel's overhang and defeats a figure meant for a coloured page.
- **`scale`** does not affect fit, since FigWorks normalizes it away. It does set
  stroke widths and font sizes *relative* to the geometry, so keep it consistent
  across scenes that share a figure — otherwise one panel's labels come out
  visibly heavier than another's.

## Matching line weights across panels

A scene and a Matplotlib panel are scaled independently to fit their panels, so
equal stroke widths in the sources do not arrive equal on the page. If the
schematic's lines look heavier or lighter than the plot's, adjust the scene's
stroke widths against the ratio of its `viewBox` width to its panel width, or
select and restyle after placement:

```python
fig.select("#slab-scene").set_style(stroke_width="0.8")
```

## Selecting inside a placed scene

Give elements ids as you build the scene, and they remain selectable afterwards:

```python
scene.polygon(20, axis_marker, id="absorption-axis", fill="#d62828")
...
fig.select("#absorption-axis").set_style(fill="navy")
```

Panel placement wraps the scene in a group but does not rewrite ids, so `#id`
selectors reach through.

!!! warning "Definition ids are not namespaced"

    A scene's `<defs>` children — gradients, markers, clip paths — are hoisted
    into the figure's `<defs>` **verbatim**. If two placed scenes use the same
    def id, both survive and `url(#id)` resolves to the first, so the second
    scene silently takes the first one's gradient.

    Until FigWorks rewrites ids on import, give each scene distinct def ids:

    ```python
    scene.add_def(svg.RadialGradient(id=f"glow-{panel_name}", ...))
    ```

    This affects any SVG source with `<defs>`, not just `vecview`. Matplotlib
    happens to avoid it by hashing its clip-path ids.

## Choosing a projection

VecView ships five, all parallel projections:

```python
vecview.OrthographicCamera(35, 24, 62)  # trimetric, the general case
vecview.OrthographicCamera.isometric(62)  # all axes equal
vecview.OrthographicCamera.dimetric(62)  # 1:1:0.5, the drafting standard
vecview.ObliqueCamera.cavalier(62)  # front face true, full depth
vecview.ObliqueCamera.cabinet(62)  # front face true, half depth
```

A finished scene re-renders under any of them with `Scene.with_camera`, so a
figure can carry the same geometry in two projections without building it twice:

```python
scene = build_scene(vecview.OrthographicCamera.isometric(62))
left.add(scene, id="iso")
right.add(scene.with_camera(vecview.ObliqueCamera.cabinet(62)), id="cabinet")
```

## Placing a plot *in* the scene

A Matplotlib plot can lie in a plane of the scene rather than in its own panel.
The scene reserves the rectangle, and `Figure.fill_plane` normalizes the plot onto
it:

```python
# world +y projects rightward at this azimuth, world +x downward, which is what
# keeps the plot's labels upright rather than mirrored or rotated
scene.plane(
    15,
    origin=(-4.2, -2.9, 0.01),
    u_edge=(0.0, 8.4, 0.0),
    v_edge=(5.8, 0.0, 0.0),
    id="plot-plane",
)

panel.add(scene, id="geometry")
fig.fill_plane("plot-plane", mpl_fig)
```

The embedding is exact rather than approximate: a parallel projection is affine,
so restricted to a plane it stays affine, which is precisely what an SVG `matrix`
expresses. (A perspective camera would give a homography, which `matrix` cannot
represent.)

Two things to get right:

- **Match the aspect ratio.** `fill_plane` normalizes content onto the unit
  square, so shape the rectangle to the plot: `|u_edge| / |v_edge|` should equal
  the figure's `width / height`, or the plot comes out stretched.
- **Keep the content upright.** Content is unmirrored and right-way-up exactly
  when the plane matrix has `a > 0` and `d > 0` — its `+x` projects rightward and
  its `+y` downward. A positive determinant is *not* enough: a 180° rotation has
  one too, which is the easy way to get every label upside down.

Give the plot a transparent background (`mpl_fig.patch.set_alpha(0)`) so the
surface it lies on shows through, and remember it joins the layer stack — a beam
drawn at a higher layer crosses over it.

`examples/vecview_plane_plot.py` renders this, flat on a slab and upright on a
back wall.

## Pinning a label to the scene

Labels usually should *not* lie in a plane: they read best upright, at the
document's font size. A slot pins upright content to a world point instead:

```python
label = vectex.render(r"$x$", size_pt=8)
pt = 96 / 72  # px per pt; the label's room is reserved in scene units
scene.slot(45, axis_tip, label.width * pt, label.height * pt, align="west", dx=1.6, id="label-x")

panel.add(scene, id="device")
fig.fill_slot("label-x", label)
```

The scene reserves an empty group at the projected point, offset by `dx`/`dy` in
screen units, and records which point of the label's box sits there
(`align="west"` puts the anchor at the middle of its left edge). `fill_slot`
places the content at the size its own document declares, so an 8 pt label stays
8 pt however the scene is scaled to fit the panel. The anchor moves with the
scene, and with the camera under `Scene.with_camera`.

Only the label's *room* is in scene units: the `w` by `h` box the scene reserves
grows the fitted viewBox so the label is not clipped. It matches the label
exactly when the scene is placed at 1:1 — one scene unit per px — and leaves a
proportionally different margin otherwise.

Because the slot sits in the layer stack, a lead drawn on a higher layer can
still cross in front of its label.

## Rasterization caveat

A **gradient-filled `<mask>` does not survive CairoSVG** — the effect vanishes
silently, with no warning, in both PDF and PNG export. Where a scene would use a
masked shape, use a gradient *fill* on a plain rectangle instead.

## The stack

| Package | Produces |
| --- | --- |
| Matplotlib | scientific plots as vector SVG |
| [VecTeX](https://github.com/maiani/vectex) | editable TeX equations as SVG fragments |
| [VecView](https://github.com/maiani/vecview) | layered 3D schematics as SVG documents |
| VecWire | editable circuit schematics as SVG documents |
| FigWorks | the composed, exported figure |
