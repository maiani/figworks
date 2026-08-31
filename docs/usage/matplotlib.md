# Matplotlib integration

FigForge connects Matplotlib and SVG **in both directions**.

## Simple SVG insertion

The package root provides direct composition without the higher-level `Figure`
interface or manual placeholders:

```python
import figforge
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
svg = figforge.compose({ax: "annotation.svg"}, fig=fig)
```

`compose` maps axes to SVG strings and paths, Matplotlib figures, or Vectex
fragments. The lower-level `connect`, `insert`, `box_artist`, and
`svg_to_image_artist` helpers remain available from
`figforge.matplotlib` for custom placement workflows.

## Direction 1: Matplotlib embedded as SVG

Export any Matplotlib figure to a vector SVG string, then embed it inside a
FigForge figure as an editable panel.

```python
from figforge.matplotlib import mpl_to_svg
from figforge import Figure

svg = mpl_to_svg(mpl_fig)                # figure -> SVG string

fig = Figure(width="120mm", height="70mm")
panel = fig.panel("main", x="10mm", y="10mm", w="90mm", h="45mm")
panel.add(mpl_fig, id="sine-panel")  # embed directly
```

`mpl_to_svg` preserves text as real SVG text (rather than paths) via an
internal `svg.fonttype = "none"` context, so fonts stay editable.

### Setting semantic ids on artists

Give Matplotlib artists a gid up front; it survives export and lets you select,
style, or delete them later.

```python
from figforge.matplotlib import set_gid

line = ax.plot(x, y)[0]
set_gid(line, "sine-line")

# after embedding:
fig.select("#sine-line").set_style(stroke_width="2pt")
```

## Direction 2: SVG imported as a Matplotlib object

Import an SVG string as a Matplotlib artist so it can be placed directly into a
Matplotlib figure or axes.

```python
from figforge.matplotlib import svg_to_image_artist, box_artist, connect

# A raster preview artist you can add to an axes / offsetbox:
artist = svg_to_image_artist(svg_text, gid="my-svg")

# A replaceable drawing area placeholder:
area = box_artist(50, 30, "region")

# Or add a labelled placeholder rectangle straight onto an axes:
connect(ax, "region", 0.1, 0.1, 0.6, 0.6)
```

## Replacing placeholders by id (`insert`)

Place placeholder artists in a Matplotlib figure, export to SVG, then swap in
real vector SVG content by id. The replacement may be a Matplotlib figure, an
SVG file path, or an SVG string.

```python
from figforge.matplotlib import insert, connect

connect(ax, "slot", 0.2, 0.2, 0.6, 0.6)

result = insert(
    {
        "slot": mpl_fig,      # figure
        # "slot": "panel.svg",  # or a file path
        # "slot": svg_string,   # or an SVG string
    },
    fig=mpl_fig,             # the base figure (or pass svg=...)
    preserve_aspect_ratio=True,
)
```

The returned string is the assembled SVG with each placeholder replaced by its
vector content, scaled and positioned to fit the original placeholder box.
