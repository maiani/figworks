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

## Fonts

Text stays live `<text>` in the SVG, so labels remain editable in Inkscape. The
price is that how it looks depends on the fonts of the machine that renders it.
FigWorks keeps that under control in two ways.

**One typeface.** The theme's `font_family`, TeX Gyre Heros by default, is set
on the figure's root, so every source that names no font inherits it. Give
Matplotlib the same face, words and math alike, once at the top of a script:

```python
import matplotlib.pyplot as plt
from figworks.matplotlib import theme_rc

plt.rcParams.update(theme_rc())  # also sets the theme's base font size
```

Apply it globally rather than in an `rc_context` around the plotting code:
Matplotlib chooses math fonts when it draws the figure, which for FigWorks is
when the plot is placed. VecTeX equations are glyph outlines and need no font.
VecView's `text` defaults to DejaVu Sans; pass `font_family` to match.

TeX Gyre Heros is a free Helvetica clone. It ships with TeX Live, and on Debian
and Ubuntu as `fonts-texgyre`. To use another face, pass a `Theme`:

```python
from figworks import Figure, Theme

fig = Figure("170mm", "76mm", theme=Theme(font_family="Source Sans 3"))
```

**No silent substitution.** Before writing PDF or PNG, `save` checks every run
of text: that the first family of its `font-family` (the only one CairoSVG
uses), in its weight and style, resolves through fontconfig to a file of that
family, and that the file has a glyph for every character. Otherwise it raises
`FontError` naming each problem, and writes nothing:

```text
figworks.fonts.FontError: this figure would not render as written:
  TeX Gyre Heros:weight=regular:slant=roman: no glyph for 'ⱼ' U+2C7C in .../texgyreheros-regular.otf
  Nope Sans:weight=regular:slant=roman: not installed; it would render as Noto Sans (...)
```

A generic family such as `sans-serif` is reported too, since it renders as a
different font on every machine. The check needs fontconfig's `fc-match` and
`fc-query`, which come with fontconfig on Linux and with Homebrew's on macOS.
SVG output is not checked: its fonts are the viewer's concern.

If a font is installed but reported as rendering as something unrelated, the
fontconfig cache may be stale: `fc-cache -f` rebuilds it.

## Export an SVG string

```python
fig.document.to_string()
```

## Display inline (notebooks)

Render an SVG, a Matplotlib figure, or a FigWorks figure directly in a Jupyter
notebook.

```python
from figworks import display_svg

display_svg(fig)  # a figworks Figure
display_svg(mpl_fig)  # a Matplotlib figure
display_svg(svg_text)  # a raw SVG string
```

`display_svg` renders the SVG as an inline image. When IPython is not
available, it prints the SVG source to the terminal instead.
