# FigForge

FigForge is a thin assembly layer for publication-quality figures built from
Matplotlib plots, Vectex equations, vecview schematics, and native SVG elements.

The canonical output is SVG. PDF and PNG export are supported through CairoSVG.

FigForge is designed as an editable assembly layer between plotting code and final publication graphics. It does not try to replace Matplotlib, Inkscape, Illustrator, or LaTeX.

## The suite

FigForge is the composition layer of three projects developed together, each
independently useful:

| Project | Produces |
| --- | --- |
| **FigForge** | composed, exported multi-panel figures |
| [Vectex](https://github.com/maiani/vectex) | editable TeX equations as SVG fragments |
| [vecview](https://github.com/maiani/vecview) | layered 3D schematics as SVG documents |

All three emit vector SVG with stable ids and deterministic output, so a figure
can be regenerated from code, diffed in version control, and still hand-tuned in
Inkscape. Vectex and vecview know nothing about FigForge: both simply expose
`to_svg_document()`, and FigForge places anything that does — no adapter here, no
import in either direction.

The dependency edges are uneven by design: Vectex is a runtime requirement,
vecview is optional and installed from a checkout, and neither depends on
FigForge. [`AGENTS.md`](AGENTS.md#the-suite) records why the three are built
apart but in step.

## Status

This repository is an early MVP scaffold. The public API is intentionally small and unstable while the core figure model is being built.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Quick Start

For the common case of placing SVG in Matplotlib axes, use `compose`. No
`figforge.Figure` or manual placeholder is involved:

```python
import figforge
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
svg = figforge.compose({ax: "logo.svg"}, fig=fig)
with open("figure.svg", "w", encoding="utf-8") as output:
    output.write(svg)
```

Use `Figure` when you need explicit panels, physical layout, selectors, and
annotations:

```python
import numpy as np
import matplotlib.pyplot as plt

from figforge import Figure

x = np.linspace(0, 2 * np.pi, 200)
y = np.sin(x)

mpl_fig, ax = plt.subplots(figsize=(3, 2))
line, = ax.plot(x, y)
line.set_gid("sine-line")
ax.set_xlabel("x")
ax.set_ylabel("sin(x)")

fig = Figure(width="120mm", height="70mm", theme="paper")
panel = fig.panel("main", x="10mm", y="10mm", w="90mm", h="45mm")
panel.add(mpl_fig, id="sine-panel")

fig.label("a", anchor=panel.nw)
fig.text("A Matplotlib SVG panel", x="10mm", y="62mm", id="caption")
fig.arrow(id="caption-arrow", start=("45mm", "58mm"), end=("70mm", "40mm"))

fig.save("example.svg")
fig.save("example.pdf")
fig.save("example.png")
```

## Current API

The root package exposes:

- `compose`
- `Figure`
- `Panel`
- `Anchor`
- `Theme`
- `layout_svgs`
- `display_svg`

Supported MVP operations include:

- creating an SVG canvas with physical dimensions,
- adding rectangular panels,
- placing Matplotlib figures, Vectex fragments, vecview scenes, and SVG documents through one API,
- importing SVG as Matplotlib artists and swapping placeholders by id (SVG embedded as Matplotlib),
- adding native text, labels, rectangles, lines, and arrows,
- drawing placeholders and filling them by id with SVG content,
- laying out many SVG panels into a labelled grid,
- selecting elements by `#id`, `.class`, or tag name,
- deleting selected elements,
- setting inline style on selected elements,
- saving to `.svg`, `.pdf`, and `.png`,
- displaying figures inline in notebooks.

## Matplotlib integration

FigForge bridges Matplotlib and SVG in both directions:

```python
from figforge.matplotlib import mpl_to_svg, connect, insert

svg = mpl_to_svg(mpl_fig)                 # Matplotlib -> SVG
connect(ax, "slot", 0.2, 0.2, 0.6, 0.6)   # reserve a placeholder in Matplotlib
result = insert({"slot": panel_fig}, fig=mpl_fig)  # swap in vector SVG by id
```

## Vectex integration

Vectex fragments implement FigForge's small SVG-document protocol, so no
adapter or manual serialization is needed:

```python
import vectex

equation = vectex.render(r"\[E = mc^2\]", id_prefix="equation")
panel.add(equation, id="equation-panel")
fig.select("#equation-root").set_attr("fill", "navy")
```

## 3D scene integration

[vecview](https://github.com/maiani/vecview) scenes implement the same SVG-document
protocol, so a 3D schematic places like any other panel source:

```python
import vecview

cam = vecview.OrthographicCamera(azim_deg=35, elev_deg=24, scale=62)
scene = vecview.Scene(cam, pad=6)
scene.faces(10, cam.visible(vecview.box_faces((0, 0, -0.45), (11, 9, 0.9))), fill="#cfd6e0")

panel.add(scene, id="slab-scene")
```

A plot can also be placed *in* a plane of the scene instead of its own panel:
`scene.plane(...)` reserves the rectangle and `fig.fill_plane(id, mpl_fig)` fills
it, so the plot lies on the slab, foreshortened with the geometry.

vecview is not a FigForge dependency; install it from a checkout. See
`docs/usage/scenes-3d.md`.

## Grid layout

```python
from figforge import layout_svgs

fig = layout_svgs([svg_a, svg_b, svg_c], labels=["a", "b", "c"], outline=True)
```

## Placeholders

```python
fig.placeholder("main-slot", x="10mm", y="10mm", w="80mm", h="60mm", label="x")
fig.fill("main-slot", mpl_fig)   # accept a figure, file path, or SVG string
```

## Examples

Run examples from the repository root:

```bash
python examples/minimal_svg.py
python examples/matplotlib_panel.py
python examples/two_panel_figure.py
python examples/vecview_panel.py     # requires vecview
```

Each example writes SVG, PDF, and PNG files.

## Development

```bash
source .venv/bin/activate
pytest
ruff check .
```

## Documentation

The docs are built with [Zensical](https://zensical.org):

```bash
python -m pip install zensical
zensical serve    # preview at http://localhost:8000
zensical build    # static build into site/
```

The implementation uses a modern `src/` layout. `lxml` is the internal SVG document representation. Matplotlib figures are exported to SVG strings and imported as editable SVG groups. CairoSVG handles PDF and PNG export.

## Non-Goals For The MVP

FigForge is not currently attempting to provide:

- a GUI,
- a full SVG path editor,
- an Inkscape replacement,
- declarative YAML figure specs,
- automatic AI editing,
- a complete CSS selector engine.

## License

MIT
