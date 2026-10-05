# Placeholders & fill

Sometimes you want to reserve a region on a figure and decide what lives in it
later. FigForge lets you draw a lightweight placeholder and fill it with
imported SVG content by id.

## Create a placeholder

```python
from figforge import Figure

fig = Figure(width="200px", height="100px")
fig.placeholder("main-slot", x=10, y=10, w=160, h=70, label="reserved")
```

Placeholders render as a dashed outline so they remain visible while you
compose, and any label is drawn centered inside them.

## Fill a placeholder

Replace the placeholder's region with imported content. `fill` accepts a
Matplotlib figure, an SVG file path, or an SVG string:

```python
fig.fill("main-slot", mpl_fig)  # Matplotlib figure
fig.fill("main-slot", "panel.svg")  # SVG file
fig.fill("main-slot", svg_text)  # SVG string
```

The content is scaled to fit inside the placeholder's bounding box while
preserving aspect ratio by default. Pass `preserve_aspect_ratio=False` to
stretch it to fill the box.

By default, filling an element removes the placeholder outline. The returned
element is the wrapping `<g>` that holds the imported content.

## Under the hood

The document-level API mirrors this:

```python
fig.document.placeholder("main-slot", 10, 10, 80, 70, label="x")
fig.document.fill("main-slot", svg_text)
```

`fill` uses the same box placement logic as `FigForge`'s Matplotlib
integration, so a placeholder behaves consistently whether it lives in a
FigForge figure or a Matplotlib canvas.

!!! tip

    `fill` also works on *any* element that has a layout box (a `rect` or a
    `path`/`polyline`), not just placeholders — select it by id and fill it.
