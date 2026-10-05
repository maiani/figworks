---
icon: lucide/rocket
---

# FigWorks

FigWorks is an SVG-first Python framework for assembling **publication-quality
scientific figures** from Matplotlib plots, native SVG elements, annotations,
and semantic figure structure.

The canonical output is **SVG**. PDF and PNG export are supported through
CairoSVG. Every element, panel, and role carries a stable identifier so the
final graphic stays editable programmatically.

## The suite

FigWorks is the composition layer of a four-project suite:
[VecTeX](https://github.com/maiani/vectex) renders TeX equations to SVG
fragments, [VecView](https://github.com/maiani/vecview) draws layered 3D
schematics as SVG documents, and VecWire draws editable circuit schematics as
SVG documents. Each is developed independently and usable alone.

All three producers integrate through one method, `to_svg_document()`, so
FigWorks needs no adapter for any of them and none imports FigWorks.

## Why FigWorks?

* **SVG-native assembly** — build figures from real vector elements.
* **Matplotlib integration** — embed Matplotlib figures as SVG, and import SVG
  back into Matplotlib, in both directions.
* **Semantic selectors** — address any element by `#id`, `.class`, or tag name.
* **Physical units** — lay out in `px`, `pt`, `mm`, `cm`, or `in`.
* **Export anywhere** — save to `.svg`, `.pdf`, and `.png`.

!!! note

    FigWorks is designed as an *editable assembly layer* between your plotting
    code and the final publication graphic. It does not try to replace
    Matplotlib, Inkscape, Illustrator, or LaTeX.

## Feature overview

| Area | What you can do |
|------|-----------------|
| Figure | Create an SVG canvas with physical dimensions and a theme. |
| Panels | Define rectangular regions with anchors. |
| Matplotlib | Export figures to SVG, embed them as panels, or import SVG as Matplotlib artists. |
| Placeholders | Reserve a region and fill it with SVG content later by id. |
| Layout | Assemble many SVG panels into a labelled grid. |
| Selectors | Select, style, and delete elements by id, class, or tag. |
| Elements | Add text, labels, rects, lines, circles, ellipses, polylines, paths, and arrows. |
| Export | Save to SVG, PDF, and PNG; display inline in notebooks. |

## Empty project quick start

```bash
python -m pip install -e ".[dev]"
```

## Full API

| Symbol | Purpose |
|--------|---------|
| `Figure` | Top-level SVG figure and assembly API. |
| `Panel` | A labelled, anchored rectangular region of a figure. |
| `Anchor` | A named absolute point (panel corners, edges, center). |
| `Theme` | Default styling (fonts, strokes, label sizes). |
| `layout_svgs` | Assemble multiple SVGs into a labelled grid. |
| `display_svg` | Render an SVG / figure inline in a notebook. |
