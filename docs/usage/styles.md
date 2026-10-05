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

## Other producers

VecView and VecWire know nothing about FigWorks, so a script hands them the
values: `theme.color["spin_up"]` for a colour, `theme.px("line.frame")` for a
weight in the px they draw in.

## What belongs in the prose

The body is the half code cannot read and people need most: what each colour
means, which weight is for what, the conventions that make figures in one paper
read as a set ("a curve's colour is its spin sector, never its data series").
Write it for a co-author or an agent opening the repository cold.
