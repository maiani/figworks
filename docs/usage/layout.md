# Grid layout

## Named panels

`Figure.grid` creates ordinary `Panel` objects from a rectangular matrix of
names. Repeat a name to span adjacent cells; use `None` for an empty cell.
Rows run from top to bottom and columns from left to right.

```python
from figworks import Figure

fig = Figure(width="180mm", height="110mm")
panels = fig.grid(
    [["device", "device"], ["spectrum", "response"]],
    width_ratios=(3, 2),
    height_ratios=(1, 2),
    margins=("8mm", "6mm", "12mm", "16mm"),
    gap=("16mm", "22mm"),
)

panels["device"].add(scene, id="device-scene")
mpl_fig, ax = panels["spectrum"].subplots()
ax.plot(x, y)
panels["spectrum"].add(mpl_fig, id="spectrum-plot", fit="axes")
fig.label("b", panels["spectrum"].nw)
```

The dictionary is ordered by each name's first appearance, scanning rows from
left to right. Its panels are also registered in `fig.panels`. Placement,
anchors, local text, and `Panel.subplots` work exactly as for manually placed
panels. Building the grid adds no SVG content; add sources and annotations
through the existing API, giving placed content explicit IDs as usual.

| Parameter | Meaning |
|-----------|---------|
| `layout` | Non-empty rectangular matrix of non-empty string IDs or `None`. |
| `width_ratios` | One positive, finite weight per column; defaults to equal widths. |
| `height_ratios` | One positive, finite weight per row; defaults to equal heights. |
| `margins` | One length for every edge, or `(top, right, bottom, left)`; default `0`. |
| `gap` | One length for both directions, or `(row_gap, column_gap)`; default `0`. |

Lengths accept the [usual units](units.md); bare numbers are **px**. Ratios
apply only to track space: margins and gaps are subtracted first. A spanning
panel covers its tracks and the gaps between them. For example, a panel
spanning all columns fills the full width between left and right margins.

Repeated names must fill a rectangle. L-shaped or disconnected spans, ragged
rows, invalid sizes, and IDs already in `fig.panels` raise before any new
panels are created. Empty cells still reserve their track space. Each call
uses the whole canvas; separate grids or manually placed panels may overlap.

With `fit="axes"`, plot labels extend into margins and gaps. Choose enough
room for them; the grid does not measure text or prevent label collisions.
Panels are resolved once to fixed coordinates. To change a figure's width,
create a new figure and apply the same grid specification: margins and gaps
keep their physical sizes while track widths change.

Run `python examples/panel_grid.py` for a complete figure with a spanning
device sketch and two unequal Matplotlib panels. It writes SVG, PDF, and PNG
to `examples/out/`.

## Equal cells from SVG sources

Assemble many SVG panels into a single labelled figure with
:func:`figworks.layout_svgs`.

### Basic usage

```python
from figworks import layout_svgs

fig = layout_svgs(
    [svg_a, svg_b, svg_c, svg_d],
    labels=["a", "b", "c", "d"],
    outline=True,
    shape=(2, 2),  # optional; inferred otherwise
)
```

The returned object is a fully-populated :class:`figworks.Figure`, ready to be
saved or further annotated.

```python
fig.save("grid.svg")
fig.save("grid.pdf")
```

Each SVG cell is given equal space in a grid. By default the grid shape is
inferred to be as square as possible.

### Parameters

| Parameter | Meaning |
|-----------|---------|
| `svgs` | A list of SVG strings. |
| `labels` | Optional per-cell labels drawn above each cell. |
| `outline` | `True` for all cells, `False` for none, or a per-cell list of booleans. |
| `shape` | Optional `(nrows, ncols)`; must match the number of SVGs. |
| `cell` | `(width, height)` of each cell in points (default `(200.0, 140.0)`). |
| `gap` | Spacing between cells in points (default `20.0`). |
| `fontsize` | Label font size (default `"10pt"`). |

### Example

```python
import matplotlib.pyplot as plt
from figworks import layout_svgs
from figworks.matplotlib import mpl_to_svg

panels = []
for i in range(6):
    f, ax = plt.subplots(figsize=(3, 2))
    ax.plot(range(5), [v**i for v in range(5)])
    panels.append(mpl_to_svg(f))

fig = layout_svgs(panels, labels=[chr(97 + i) for i in range(6)], outline=True)
fig.save("power_grid.svg")
```
