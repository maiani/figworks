# Figure collections

A thesis, a paper, or a talk has a set of figures that share a style, an output
directory, and formats. `FigureCollection` regenerates the set, or one figure of
it, from a single command:

```python
from pathlib import Path

import matplotlib.pyplot as plt

from figworks import Figure, FigureCollection

HERE = Path(__file__).resolve().parent

THESIS = FigureCollection(
    outdir=HERE / "figures",
    theme="paper",  # typeface and base size
    style_file=HERE / "thesis.mplstyle",  # optional: lines, colours
)


@THESIS.figure("ldos")
def ldos() -> plt.Figure:
    """Local density of states near the gap edge."""
    fig, ax = plt.subplots(figsize=(3.2, 2.2))
    ...
    return fig


@THESIS.figure("device")
def device() -> Figure:
    """The composed device figure."""
    fig = Figure("170mm", "76mm")
    ...
    return fig


if __name__ == "__main__":
    THESIS.main()
```

```bash
python thesis_figures.py --list        # registered figures and their summaries
python thesis_figures.py --all         # regenerate everything
python thesis_figures.py ldos device   # just these
python thesis_figures.py --all --outdir /tmp/preview
```

## What a builder returns

A builder takes no arguments and returns the finished figure: a Matplotlib
figure or a FigWorks `Figure`. It knows nothing about file paths; the
collection saves each figure once per format and closes it.

- A FigWorks `Figure` is saved with `Figure.save`, so it stays vector in SVG and
  PDF, keeps its ids, and has its fonts checked.
- A Matplotlib figure is saved with `figworks.matplotlib.save_figure`, which
  does the same for plots: fonts checked, SVG ids pinned, dates dropped.

Either way, rebuilding an unchanged figure writes identical bytes in every
format, so version control shows only the figures that really changed.

## Style

Each build starts from Matplotlib's defaults, so a run never inherits settings
from an earlier import or notebook session. The style sheet comes next, for plot
cosmetics such as line widths, the colour cycle, and legend frames. The theme's
typeface and base size go on top, through `theme_rc`, so every figure in the set
uses one face, words and math alike. Fonts set in the style sheet are therefore
overridden by the theme.

`build` restores Matplotlib's previous settings when it finishes, so calling it
from a notebook leaves the notebook's style alone.

## Options

| Argument | Default | |
| --- | --- | --- |
| `outdir` | required | where files are written, one per figure and format |
| `theme` | `"paper"` | typeface and base size, as a name or a `Theme` |
| `style_file` | `None` | a Matplotlib style sheet for plot cosmetics |
| `formats` | `("pdf", "svg", "png")` | any of `svg`, `pdf`, `png` |
| `dpi` | `300` | resolution of PNG output |

Each collection has its own registry, so a second one, slides with the
`"presentation"` theme for instance, can live beside the first without mixing
figures. Only `main` switches Matplotlib to its headless backend; importing
FigWorks never changes the backend. The command prints the git revision it ran
at, but does not write it into the files, which would make every file change
with every commit.

`examples/thesis_plots.py` is a complete collection with plots and a composed
figure.
