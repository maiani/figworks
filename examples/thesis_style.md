---
base: aps
color:
  level_minus: "#1f6fd1"
  level_plus: "#d62828"
  approx: "#737373"
  full: "#1a1a1a"
cycle: [level_minus, level_plus, approx, full]
---

# Thesis figures

Built on the APS style, since the chapters become Physical Review papers: 8.6 cm
columns, 8 pt labels, nothing thinner than 0.5 pt.

## Colour

Colours carry meaning and are named for it, not for their hue:

- **level_minus** (blue) and **level_plus** (red): the two levels at ∓ε. The pair
  keeps its colours in every figure, so a reader who has learned them once can
  read any plot.
- **approx** (grey) for an approximation and **full** (near-black) for the full
  treatment, so the reference result always reads as the strongest line.

Use the cycle order above for anything without a meaning of its own.

## Layout

Draw nothing a caption can say: no titles, legends only where curves cannot be
labelled directly.
