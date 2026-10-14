# Styles

A publication's look belongs in one document. A `style.md` holds the design
tokens in its YAML frontmatter and the style guide in its Markdown body: the
numbers for the code, the reasons for the people and agents making figures.

```markdown
---
base: aps
page:
  column: 86mm
color:
  spin_up: "#d62828"
  spin_down: "#1f6fd1"
cycle: [spin_up, spin_down]
rcparams:
  axes.grid: false
---

# Altermagnetic dot figures

Red is always s = +1 and blue s = -1, in every figure ...
```

Use it wherever FigWorks takes a theme:

```python
from figworks import Figure, FigureCollection, load_theme
from figworks.matplotlib import theme_rc

theme = load_theme("style.md")
plt.rcParams.update(theme_rc(theme))  # Matplotlib, words and math alike
fig = Figure(width=theme.page["column"], height="60mm", theme=theme)
FigureCollection(outdir=HERE / "figures", style=HERE / "style.md")
```

## Bases

A style states only what differs from its `base`, which is a built-in name or
the path of another `style.md`, relative to the file naming it. Chains are fine:
a journal style, a thesis built on it, a chapter built on the thesis. Every
chain ends at `paper`, which sets every token.

| Built-in | For | Column | Body / ticks | Face |
| --- | --- | --- | --- | --- |
| `paper` | the default: any journal column | (none) | 8 / 7 pt | TeX Gyre Heros |
| `presentation` | slides | (none) | 11 / 10 pt | TeX Gyre Heros |
| `nature` | Nature and its research journals | 89 mm, 183 mm | 7 / 6 pt | TeX Gyre Heros |
| `aps` | Physical Review, PRL, PRX | 86 mm, 178 mm | 8 / 7 pt | TeX Gyre Heros |
| `ieee` | IEEE transactions and proceedings | 88.9 mm, 182 mm | 8 / 8 pt | TeX Gyre Termes |

The journal styles follow each journal's published figure guidelines, cited in
their own prose (`src/figworks/styles/*.md`). Check the current guidelines
before submission; journals revise them.

## Tokens

| Key | Holds | Example |
| --- | --- | --- |
| `font` | `family`, and sizes `size`, `label`, `tick`, `title`, `legend`, `panel_label` | `size: 8pt` |
| `line` | weights: `data` curves, axes `frame` and ticks, `hairline` grids | `frame: 0.5pt` |
| `color` | colours named by meaning; `ink` is required | `spin_up: "#d62828"` |
| `cycle` | the plot colour cycle, by colour name or literal colour | `[spin_up, spin_down]` |
| `marker` | marker size | `3pt` |
| `page` | named lengths, kept as written | `column: 86mm` |
| `matplotlib` | Matplotlib styles or `.mplstyle` files layered underneath | `./cosmetics.mplstyle` |
| `rcparams` | raw Matplotlib settings, applied last | `axes.grid: true` |

Lengths take `pt`, `mm`, `cm`, `in`, or `px`; a bare number is points. Nested
keys merge with the base key by key; lists and values replace it.

## Matplotlib settings

`theme.rc()`, which `theme_rc` returns, layers three things over Matplotlib's
defaults:

1. the `matplotlib` styles of the whole chain, base first;
2. the settings the tokens imply: font family and math fonts, the size scale,
   line weights, marker size, ink for text, frames, and ticks, and the cycle;
3. `rcparams`, the escape hatch for anything the tokens do not cover.

A misspelt setting is reported when the style is loaded, not halfway through a
build.

## Shared typography and physical sizing

The theme returns plain dictionaries for the producers' own APIs. No sibling
imports FigWorks, and loading these settings does not import optional packages.
Each call returns fresh settings; editing them does not change the theme.

```python
theme = load_theme("aps")
plt.rcParams.update(theme.rc())
plot.update_layout(template=theme.plotly())
equation = vectex.render(r"$E = mc^2$", **theme.vectex())
scene.text(20, (0, 0, 1), "Device", **theme.vecview_text())
circuit = Circuit(100, 60, **theme.vecwire())
circuit.label("Capacitance", (50, 20), **theme.vecwire_label())
```

| Method | Destination | Size units |
| --- | --- | --- |
| `theme.rc()` | Matplotlib rc settings | points |
| `theme.plotly()` | Plotly `template` dictionary | CSS pixels |
| `theme.vectex(role="size")` | VecTeX `render` / `render_many` options | points |
| `theme.vecview_text(role="size")` | VecView `text` / `text2d` keywords | screen pixels |
| `theme.vecwire(unit="pt")` | VecWire `Circuit` keywords | selected circuit unit |
| `theme.vecwire_label(role="size", unit="pt")` | VecWire plain-text `label` keywords | selected circuit unit |

Roles are `size`, `label`, `tick`, `title`, `legend`, and `panel_label`. Use
`theme.length("line.frame", unit="mm")` for a token in `pt`, `px`, or `mm`, or
`theme.px("line.frame")` for pixels. For VecWire, use the **same unit** for the
circuit and its label settings; the new font setting requires the current
VecWire checkout. Fragment labels retain their own rendered typography.

Plotly templates set fonts, Cartesian axes, legend, color cycle (when specified),
and scatter line/marker sizes. Explicit plot settings override template values.
They do not restyle existing figures forcibly or cover every Plotly trace type.
Matplotlib `rcparams` overrides apply only to Matplotlib.

### TeX fonts

The built-in Heros setup uses `tgheros` and `sansmath` with pdfLaTeX. Termes uses
`tgtermes` and `mathptmx`. These pair text with a compatible TeX math setup;
math glyphs are not promised to match Matplotlib mathtext glyphs exactly.
The TeX packages must be installed (`tex-gyre`, `texlive-fonts-recommended`,
and `texlive-latex-recommended` on Debian/Ubuntu; rendering also needs the
standalone class from `texlive-latex-extra`). For other families, specify a complete preamble
and, if needed, an engine in the same `style.md`:

```yaml
font:
  family: TeX Gyre Termes
tex:
  engine: lualatex
  preamble: |
    \documentclass[10pt,border=0pt]{standalone}
    \usepackage{fontspec}
    \usepackage{unicode-math}
    \setmainfont{TeX Gyre Termes}
    \setmathfont{TeX Gyre Termes Math}
```

Custom preambles are trusted TeX source. They take precedence over the built-in
font setup, so keeping their font choices consistent with `font.family` is the
author's responsibility. An unrecognized family without a preamble raises an
error. Existing `vectex.render(...)` calls keep their existing defaults; theme
settings are opt-in.

### Preserve the final type size

A theme selects sizes **before placement**. `fit="content"` scales an entire
source, including its typography and strokes. Use `fit="none"` to retain its
physical dimensions. For Matplotlib, `panel.subplots()` with `fit="axes"`
also preserves the intended size; keep its theme active during creation and
export, because mathtext selects fonts at draw time. For Plotly, choose the
export canvas dimensions in pixels (96 px = 1 inch), then place it unscaled.
For VecView, choose camera scale to size geometry and place the document with
`fit="none"`; its text sizes and stroke widths are screen pixels.

`examples/transmon_figure.py` combines a VecView device, a VecWire circuit,
VecTeX labels, and Matplotlib panels under one theme, with every label at 8 pt.
The other [gallery](../gallery/index.md) figures do the same with `nature`.

## What belongs in the prose

The body is the half code cannot read and people need most: what each colour
means, which weight is for what, the conventions that make figures in one paper
read as a set ("a curve's colour is its spin sector, never its data series").
Write it for a co-author or an agent opening the repository cold.
