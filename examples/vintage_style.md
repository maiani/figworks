---
base: paper
page:
  double: 178mm
font:
  family: TeX Gyre Adventor
  size: 6.5pt
  label: 6.5pt
  tick: 6.5pt
  title: 6.5pt
  legend: 6.5pt
  panel_label: 7.5pt
panel_label:
  format: "FIG. {}"
  weight: normal
  dx: 0mm
  dy: -2.5mm
line:
  data: 0.9pt
  frame: 0.9pt
  hairline: 0.3pt
marker: 3.2pt
arrow:
  head_length: 9
  head_width: 3
color:
  ink: "#1f1b16"
  paper: "#f6f1e3"
  rule: "#c3b596"
  neutral: "#6f6656"
cycle: [ink]
rcparams:
  axes.facecolor: none
  axes.grid: true
  axes.grid.which: both
  axes.axisbelow: true
  grid.color: "#c3b596"
  grid.linewidth: 0.5
  xtick.major.size: 0
  ytick.major.size: 0
  xtick.minor.size: 0
  ytick.minor.size: 0
  xtick.minor.visible: true
  ytick.minor.visible: true
  lines.solid_capstyle: round
  lines.dash_capstyle: round
---

# Vintage: the engineering handbook

The look of a mid-century tube manual or engineering text, when figures were
inked by hand on drafting film and graph paper and lettered with a template.

## Paper and ink

One ink, **ink**, a warm black, on **paper**, a cream page: put
`background=theme.color["paper"]` on the figure. There is no colour to carry
meaning, so meaning is carried as a draughtsman carried it: by line weight,
dash, and lettering beside the line. **rule** is the graph paper's printed
grid, faint so the inked curves stand on it; **neutral** is for what is
construction, not result.

## Lettering

TeX Gyre Adventor, a free Avant Garde clone, stands in for template lettering:
geometric, even-stroked, set in capitals for headings and axis titles, with
quantities as italic symbols. Panels are lettered FIG. 1, FIG. 2, as a plate
of figures was.

## Lines

Curves and outlines at 0.9 pt, the weight of a 0.35 mm technical pen, rules
and hatching at 0.3 pt. Arrowheads are long and slender, three times as long
as they are wide, as drafting templates drew them. Hidden edges are dashed,
centre lines are long dash and dot.

## Graphs

Graph paper, not tick marks: a fine rule at every minor division and a
heavier one at every major, ticks of zero length, numbers at the major rules
only. Label each curve on the curve, with the paper colour behind the
lettering so the rules stop short of it, rather than in a legend.
