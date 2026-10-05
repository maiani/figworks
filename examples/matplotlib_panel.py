from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from figforge import Figure

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

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

fig.save(OUT / "matplotlib_panel.svg")
fig.save(OUT / "matplotlib_panel.pdf")
fig.save(OUT / "matplotlib_panel.png")
