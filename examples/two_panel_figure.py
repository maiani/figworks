import matplotlib.pyplot as plt
import numpy as np

from figforge import Figure


def make_plot(yfunc, gid):
    x = np.linspace(0, 2 * np.pi, 200)
    mpl_fig, ax = plt.subplots(figsize=(2.5, 2))
    (line,) = ax.plot(x, yfunc(x))
    line.set_gid(gid)
    ax.set_xlabel("x")
    return mpl_fig


fig = Figure(width="180mm", height="80mm", theme="paper")
panel_a = fig.panel("panel-a", x="10mm", y="10mm", w="70mm", h="50mm")
panel_b = fig.panel("panel-b", x="100mm", y="10mm", w="70mm", h="50mm")

panel_a.add(make_plot(np.sin, "sine-line"), id="sine-panel")
panel_b.add(make_plot(np.cos, "cosine-line"), id="cosine-panel")

fig.label("a", anchor=panel_a.nw)
fig.label("b", anchor=panel_b.nw)
fig.arrow(id="connector", start=panel_a.east, end=panel_b.west)

fig.save("two_panel_figure.svg")
fig.save("two_panel_figure.pdf")
fig.save("two_panel_figure.png")
