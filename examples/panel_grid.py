"""A spanning device sketch above unequal plot panels, with physical gutters."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import svg

from figworks import Figure
from figworks.matplotlib import theme_rc

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

fig = Figure(width="180mm", height="110mm")
panels = fig.grid(
    [["device", "device"], ["spectrum", "response"]],
    width_ratios=(3, 2),
    height_ratios=(1, 2),
    margins=("8mm", "6mm", "12mm", "16mm"),
    gap=("16mm", "22mm"),
)

sketch = svg.SVG(
    viewBox=svg.ViewBoxSpec(0, 0, 300, 45),
    elements=[
        svg.Line(x1=70, y1=22, x2=240, y2=22, stroke="#536474", stroke_width=2),
        *[
            svg.Rect(
                id=name.lower(),
                x=x,
                y=4,
                width=60,
                height=36,
                rx=4,
                fill=fill,
                stroke="#536474",
                stroke_width=1,
            )
            for name, x, fill in (
                ("Drive", 10, "#e4edf5"),
                ("Device", 120, "#d9e8e0"),
                ("Readout", 230, "#e4edf5"),
            )
        ],
        *[
            svg.Text(x=x, y=25, text=name, text_anchor="middle", font_size=10)
            for name, x in (("Drive", 40), ("Device", 150), ("Readout", 260))
        ],
    ],
)
panels["device"].add(str(sketch), id="device-sketch")

with plt.rc_context(theme_rc()):
    detuning = np.linspace(-3, 3, 200)
    for name in ("spectrum", "response"):
        plot, ax = panels[name].subplots()
        if name == "spectrum":
            ax.plot(detuning, 1 / (1 + detuning**2), color="#2675a5")
            ax.set_ylabel("Transmission")
        else:
            ax.plot(detuning, np.arctan(detuning), color="#518464")
            ax.set_ylabel("Phase (rad)")
        ax.set_xlabel("Detuning")
        ax.spines[["top", "right"]].set_visible(False)
        panels[name].add(plot, id=f"plot-{name}", fit="axes")
        plt.close(plot)

for name, label in zip(panels, ("a", "b", "c"), strict=True):
    fig.label(label, panels[name].nw, id=f"label-{name}")

for suffix in ("svg", "pdf", "png"):
    fig.save(OUT / f"panel_grid.{suffix}")
