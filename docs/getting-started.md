# Getting started

## Install

Install the package with its dev tooling into a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Quick start

```python
import numpy as np
import matplotlib.pyplot as plt

from figforge import Figure

x = np.linspace(0, 2 * np.pi, 200)
y = np.sin(x)

mpl_fig, ax = plt.subplots(figsize=(3, 2))
(line,) = ax.plot(x, y)
line.set_gid("sine-line")
ax.set_xlabel("x")
ax.set_ylabel("sin(x)")

fig = Figure(width="120mm", height="70mm", theme="paper")
panel = fig.panel("main", x="10mm", y="10mm", w="90mm", h="45mm")
panel.add(mpl_fig, id="sine-panel")

fig.label("a", anchor=panel.nw)
fig.text("A Matplotlib SVG panel", x="10mm", y="62mm", id="caption")
fig.arrow(id="caption-arrow", start=("45mm", "58mm"), end=("70mm", "40mm"))

fig.save("example.svg")
fig.save("example.pdf")
fig.save("example.png")
```

This writes `example.svg`, `example.pdf`, and `example.png` to the current
directory.

## Run the examples

```bash
python examples/minimal_svg.py
python examples/matplotlib_panel.py
python examples/two_panel_figure.py
```

Each example writes its figures to `examples/out/`.

## Units

FigForge understands physical units everywhere coordinates and sizes are
accepted: `px`, `pt`, `mm`, `cm`, and `in`. Bare numbers are treated as pixels.

```python
to_px("25.4mm")  # 96.0
to_px("1in")  # 96.0
```
