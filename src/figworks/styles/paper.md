---
# The root of every style chain: every token is set here, so a style built on
# it states only what differs.
base: null
font:
  family: TeX Gyre Heros
  size: 8pt
  label: 8pt
  tick: 7pt
  title: 8pt
  legend: 7pt
  panel_label: 10pt
line:
  data: 1pt
  frame: 0.5pt
  hairline: 0.25pt
marker: 3pt
color:
  ink: "#000000"
  neutral: "#737373"
rcparams:
  legend.frameon: false
---

# Paper

The default style: figures for a journal column, printed at their final size.

## Type

One face for everything, words and math alike: TeX Gyre Heros, a free Helvetica
clone that sits well beside Computer Modern equations from VecTeX. 8 pt is the
body size, used for axis labels and annotations; tick labels and legends drop to
7 pt; panel letters are 10 pt bold.

## Lines

Three weights. Data curves are 1 pt and should be the heaviest thing on the page.
Axes frames and ticks are 0.5 pt, so they hold the plot without competing with
it. Grids and minor ticks are 0.25 pt hairlines, and better left out.

## Colour

Black ink for text, frames, and annotations; a neutral grey for secondary
elements. The plot colour cycle is Matplotlib's: a publication should name its
own colours by meaning in its own style.
