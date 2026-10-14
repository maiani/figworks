"""Static Plotly SVG composition; requires figworks[plotly] and Chrome."""

from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from figworks import Figure, load_theme
from figworks.plotly import plotly_to_svg

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

theme = load_theme()

t = np.linspace(0, 6, 240)
plot = go.Figure()
plot.add_scatter(x=t, y=np.exp(-t / 3) * np.cos(2 * np.pi * t), name="Displacement")
plot.add_scatter(x=t, y=np.exp(-t / 3), name="Decay envelope", line={"dash": "dash"})
plot.update_layout(
    template=theme.plotly(),
    xaxis_title="Time (s)",
    yaxis_title="Displacement (a.u.)",
    margin={"l": 80, "r": 20, "t": 25, "b": 65},
    legend={"x": 1, "y": 1, "xanchor": "right"},
)

figure = Figure("160mm", "100mm")
figure.rect(x=0, y=0, width="160mm", height="100mm", fill="white", stroke="none")
panel = figure.panel("main", "10mm", "10mm", "140mm", "75mm")
panel.add(
    plotly_to_svg(plot, width=round(panel.w), height=round(panel.h)),
    id="oscillation",
    fit="none",
)
figure.label("a", anchor=panel.nw)
figure.text("Damped harmonic motion", x="10mm", y="94mm", id="caption")
for extension in ("svg", "pdf", "png"):
    figure.save(OUT / f"plotly_panel.{extension}")
