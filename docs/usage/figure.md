# Figure, Panel & anchors

## Figure

`Figure` is the top-level SVG canvas and assembly API.

```python
from figworks import Figure

fig = Figure(width="180mm", height="100mm", theme="paper")
```

* `width`, `height` — physical dimensions using any supported unit.
* `theme` — one of `"paper"` or `"presentation"`, or a `Theme` instance.

Themes control default fonts, font sizes, stroke widths, and colors.

### Adding content

`Figure` offers convenience methods that append native SVG elements to the
document, apply the active theme, and accept unit-aware coordinates:

```python
fig.text("Some text", x="10mm", y="5mm", id="caption")
fig.rect(x=5, y=5, width=20, height=10, id="box")
fig.line(x1=0, y1=0, x2=10, y2=10)
fig.circle(cx=5, cy=5, r=2)
fig.ellipse(cx=5, cy=5, rx=3, ry=2)
fig.polyline([(0, 0), (5, 5), (10, 0)])
fig.path("M 0 0 L 10 10")
```

### Labels and arrows

```python
fig.label("a", anchor=panel.nw)
fig.arrow(id="callout", start=("45mm", "58mm"), end=("70mm", "40mm"))
```

## Panel

`Panel` is a rectangular, labelled region of the figure with its own anchors.

```python
panel = fig.panel("main", x="10mm", y="10mm", w="80mm", h="60mm")
```

Panels track their own `x`, `y`, `w`, `h` in pixels. They host imported
Matplotlib plots and panel-local annotations:

```python
panel.add(mpl_fig, id="plot")
panel.text("subtitle", x="5mm", y="5mm")
```

## Anchor

`Anchor` is a named absolute point. Every panel exposes nine anchors:

* Corners: `nw`, `ne`, `sw`, `se`
* Edges: `north`, `south`, `east`, `west`
* `center`

```python
fig.label("a", anchor=panel.nw)
fig.arrow(id="link", start=panel.south, end=panel.east)
```

You can also pass raw `(x, y)` tuples anywhere an anchor is accepted; unit-aware
values (`"5mm"`) are resolved automatically.
