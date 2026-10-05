# Matplotlib integration

FigWorks connects Matplotlib and SVG **in both directions**.

## Simple SVG insertion

The package root provides direct composition without the higher-level `Figure`
interface or manual placeholders:

```python
import figworks
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
svg = figworks.compose({ax: "annotation.svg"}, fig=fig)
```

`compose` maps axes to SVG strings and paths, Matplotlib figures, or VecTeX
fragments. The lower-level `connect`, `insert`, `box_artist`, and
`svg_to_image_artist` helpers remain available from
`figworks.matplotlib` for custom placement workflows.

## Direction 1: Matplotlib embedded as SVG

Export any Matplotlib figure to a vector SVG string, then embed it inside a
FigWorks figure as an editable panel.

```python
from figworks.matplotlib import mpl_to_svg
from figworks import Figure

svg = mpl_to_svg(mpl_fig)  # figure -> SVG string

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
from figworks.matplotlib import set_gid

line = ax.plot(x, y)[0]
set_gid(line, "sine-line")

# after embedding:
fig.select("#sine-line").set_style(stroke_width="2pt")
```

## Aligning axes across panels

`Panel.add` fits a plot's drawn content into the panel by default. For a row of
plots that misaligns the axes frames: a plot with wider tick labels has its
frame pushed further in and scaled differently, and fitting rescales its text
away from the nominal size.

Make each plot with `Panel.subplots` and place it with `fit="axes"` instead:

```python
panel = fig.panel("spectrum", x="18mm", y="8mm", w="62mm", h="48mm")
mpl_fig, ax = panel.subplots()  # a figure whose axes frame is the panel
ax.plot(x, y)
panel.add(mpl_fig, id="spectrum-plot", fit="axes")
```

- `Panel.subplots` returns a Matplotlib figure exactly the panel's physical size,
  with its axes grid filling it edge to edge. It takes the arguments of
  `plt.subplots` (`nrows`, `ncols`, `sharex`, `gridspec_kw={"wspace": ...}`, …),
  but sets the figure size, the grid's outer edges, and no layout engine itself,
  since those would move the frame.
- `fit="axes"` maps the figure's *axes frame*, the union of its axes, onto the
  panel, and lets tick and axis labels hang outside it. A figure from
  `Panel.subplots` lands at exactly 1:1, so 8 pt stays 8 pt.
- Panels in a row with the same `y` and `h` then have frames whose tops and
  bottoms coincide, whatever their labels. Leave room for the labels around the
  panels when laying them out: the panel is the frame, not the whole plot.

`fit="axes"` also accepts an ordinary figure, made with any `figsize` and layout
engine. Its frame is then fitted into the panel, scaled uniformly and centred,
which aligns frames but rescales text. `examples/two_panel_figure.py` shows two
aligned panels with very different tick labels.

## Direction 2: SVG imported as a Matplotlib object

Import an SVG string as a Matplotlib artist so it can be placed directly into a
Matplotlib figure or axes.

```python
from figworks.matplotlib import svg_to_image_artist, box_artist, connect

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
from figworks.matplotlib import insert, connect

connect(ax, "slot", 0.2, 0.2, 0.6, 0.6)

result = insert(
    {
        "slot": mpl_fig,  # figure
        # "slot": "panel.svg",  # or a file path
        # "slot": svg_string,   # or an SVG string
    },
    fig=mpl_fig,  # the base figure (or pass svg=...)
    preserve_aspect_ratio=True,
)
```

The returned string is the assembled SVG with each placeholder replaced by its
vector content, scaled and positioned to fit the original placeholder box.
