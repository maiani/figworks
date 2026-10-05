# Export & display

## Save to a file

`Figure.save` infers the format from the file extension: `.svg`, `.pdf`, or
`.png`.

```python
fig.save("figure.svg")
fig.save("figure.pdf")
fig.save("figure.png", dpi=300)
```

* SVG is written directly as text.
* PDF and PNG are rendered by CairoSVG.
* `dpi` controls raster resolution for PNG (default `300`), whatever unit the
  figure size was given in: a px is 1/96 in, so a 96 px wide figure saved at
  `dpi=600` is 600 pixels wide.

Unsupported extensions raise a clear `ValueError`:

```python
fig.save("figure.gif")  # ValueError: Unsupported export format: .gif
```

## Export an SVG string

```python
fig.document.to_string()
```

## Display inline (notebooks)

Render an SVG, a Matplotlib figure, or a FigForge figure directly in a Jupyter
notebook.

```python
from figforge import display_svg

display_svg(fig)  # a figforge Figure
display_svg(mpl_fig)  # a Matplotlib figure
display_svg(svg_text)  # a raw SVG string
```

`display_svg` renders the SVG as an inline image. When IPython is not
available, it prints the SVG source to the terminal instead.
