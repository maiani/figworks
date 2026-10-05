"""Two Matplotlib panels whose axes frames line up, whatever their labels.

Each plot is made with `Panel.subplots`, so its axes frame is exactly its panel,
and placed with `fit="axes"`, so it lands at 1:1: the frames sit on the panels,
tick labels hang outside into the gutters, and text keeps its nominal size.
The right panel's six-digit tick labels would push its frame inward and shrink
it if the plots were fitted by their content instead.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from figworks import Figure
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

# Plots use the figure's typeface, words and math alike.
plt.rcParams.update(theme_rc())

x = np.linspace(0, 2 * np.pi, 200)

fig = Figure(width="180mm", height="70mm", theme="paper")
# The panels are the axes frames; the margins around them hold the labels.
panel_a = fig.panel("panel-a", x="18mm", y="8mm", w="62mm", h="48mm")
panel_b = fig.panel("panel-b", x="112mm", y="8mm", w="62mm", h="48mm")

mpl_fig, ax = panel_a.subplots()
(line,) = ax.plot(x, np.sin(x))
line.set_gid("sine-line")
ax.set_xlabel(r"$\theta$")
ax.set_ylabel(r"$\sin\theta$")
panel_a.add(mpl_fig, id="sine-panel", fit="axes")

mpl_fig, ax = panel_b.subplots()
(line,) = ax.plot(x, 120_000 * np.cos(x) ** 2)
line.set_gid("power-line")
ax.ticklabel_format(axis="y", style="plain", useOffset=False)
ax.set_xlabel(r"$\theta$")
ax.set_ylabel("counts")
panel_b.add(mpl_fig, id="power-panel", fit="axes")

fig.label("a", anchor=panel_a.nw)
fig.label("b", anchor=panel_b.nw)

fig.save(OUT / "two_panel_figure.svg")
fig.save(OUT / "two_panel_figure.pdf")
fig.save(OUT / "two_panel_figure.png")
