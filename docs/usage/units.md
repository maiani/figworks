# Units and sizes

A figure meets several unit systems at once: millimetres for the page, pixels
for placement, points for TeX and Matplotlib, world units for a 3D scene. Each
boundary between them uses one rule, listed here. Most sizing surprises come
from assuming a different rule at one of these boundaries.

## The canvas

```python
fig = Figure(width="170mm", height="76mm")
```

- `width` and `height` accept `px`, `pt`, `mm`, `cm`, and `in`. A bare number is
  **px**.
- One px is **1/96 in**, as in CSS. So `25.4mm`, `1in`, `72pt`, and `96` are the
  same length.
- Inside the figure, every coordinate is in **px**. The root `viewBox` is the
  canvas size in px, which is what binds the two: `170mm` wide is a viewBox
  642.5 px wide.
- Panel and element positions accept the same units and are converted to px:
  `x="12mm"` is 45.35 px.

## What a source declares

Every source hands FigWorks an SVG document whose root has a `width`, a
`height`, and a `viewBox`. In all four producers, one viewBox unit is one unit
of the declared size, so the document's physical size is unambiguous:

| Source | Declared size | One user unit |
| --- | --- | --- |
| Matplotlib | `width="216pt"`: the tight bounding box, in pt | 1 pt |
| VecTeX fragment | `width="4.56pt"` | 1 pt (TeX's output unit) |
| VecView scene | `width="904.0"` (unitless) | 1 px; `cam.scale` px per world unit |
| VecWire circuit | `width="86pt"` from `Circuit(86, 118)` | 1 pt |

A unitless length is px. A source without `width`/`height` is taken to be its
viewBox size in px.

## Placing content

How the source's declared size is used depends on the operation:

| Operation | Size it ends up at | Declared size |
| --- | --- | --- |
| `Panel.add`, `Figure.add` | fitted into the box, uniform scale, centred | ignored |
| `Figure.fill` (placeholder) | fitted into the placeholder's box | ignored |
| `Figure.fill_plane` | stretched onto the plane's unit square | ignored |
| `Figure.fill_slot` | its declared physical size | **honoured** |

Fitting reads only the viewBox: a Matplotlib figure about 3 in wide, placed in a
40 mm wide panel, is drawn 40 mm wide, and its 10 pt tick labels shrink by the
same factor. To keep type at its nominal size, make the panel the source's
physical size, or size the source to the panel.

`fill_slot` is the one operation that keeps the source at its own size. An 8 pt
VecTeX label stays 8 pt however its scene was scaled to fit, because FigWorks
divides out every scale between the slot and the page. The slot's anchor still
moves with the scene. This relies on the source declaring its size with units;
VecTeX before 0.2 wrote unitless lengths, so its labels came out at 3/4 size.

## VecView scenes at 1:1

A scene's `pad`, slot reservations (`Scene.slot(..., w, h)`), and stroke widths
are in its own user units, px. They come out at their nominal size only when the
scene is placed at 1:1, that is, when the panel is exactly as large as the scene:

```python
lo, hi = scene.bbox()
# The document rounds its size to 0.1 px; match it exactly.
w, h = (round(float(v), 1) for v in hi - lo + 2 * scene.pad)
fig = Figure(width=float(w), height=float(h))
fig.panel("scene", x=0, y=0, w=float(w), h=float(h)).add(scene, id="scene")
```

To print a scene at a chosen scale, pick `cam.scale` in px per world unit: with
`scale=9.6`, one world unit is 9.6 px, or 2.54 mm. At any other placement scale,
a slot's label keeps its own size while the room reserved for it scales, so the
margin around the label grows or shrinks. See
[Matching line weights](scenes-3d.md#matching-line-weights-across-panels) for
keeping strokes consistent between panels.

## Export

| Format | Size |
| --- | --- |
| `.svg` | the canvas as declared (`170mm` × `76mm`), viewBox in px |
| `.pdf` | the declared physical size |
| `.png` | `dpi` pixels per inch, default 300; a px is 1/96 in |

PNG resolution follows `dpi` whatever unit the figure was given in: a 96 px
wide figure saved at `dpi=600` is 600 pixels wide, as is a `1in` wide one.

## For producers

A new source integrates through `to_svg_document()` alone, and these rules keep
its size unambiguous:

- Declare `width` and `height`, with a unit unless you mean px.
- Make the `viewBox` extents equal those numbers, so one user unit is one
  declared unit.
- Let the viewBox origin be anything: placement compensates for `min_x` and
  `min_y`.
