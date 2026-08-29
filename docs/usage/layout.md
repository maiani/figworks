# Grid layout

Assemble many SVG panels into a single labelled figure with
:func:`figforge.layout_svgs`.

## Basic usage

```python
from figforge import layout_svgs

fig = layout_svgs(
    [svg_a, svg_b, svg_c, svg_d],
    labels=["a", "b", "c", "d"],
    outline=True,
    shape=(2, 2),          # optional; inferred otherwise
)
```

The returned object is a fully-populated :class:`figforge.Figure`, ready to be
saved or further annotated.

```python
fig.save("grid.svg")
fig.save("grid.pdf")
```

Each SVG cell is given equal space in a grid. By default the grid shape is
inferred to be as square as possible.

## Parameters

| Parameter | Meaning |
|-----------|---------|
| `svgs` | A list of SVG strings. |
| `labels` | Optional per-cell labels drawn above each cell. |
| `outline` | `True` for all cells, `False` for none, or a per-cell list of booleans. |
| `shape` | Optional `(nrows, ncols)`; must match the number of SVGs. |
| `cell` | `(width, height)` of each cell in points (default `(200.0, 140.0)`). |
| `gap` | Spacing between cells in points (default `20.0`). |
| `fontsize` | Label font size (default `"10pt"`). |

## Example

```python
import matplotlib.pyplot as plt
from figforge import layout_svgs
from figforge.backends.matplotlib import mpl_to_svg

panels = []
for i in range(6):
    f, ax = plt.subplots(figsize=(3, 2))
    ax.plot(range(5), [v**i for v in range(5)])
    panels.append(mpl_to_svg(f))

fig = layout_svgs(panels, labels=[chr(97 + i) for i in range(6)], outline=True)
fig.save("power_grid.svg")
```
