"""One physical type scale across the suite: an LC resonator and its response.

Requires the sibling checkouts, figworks[plotly], Chrome, and TeX.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import vectex
import vecview
from vecwire import Circuit

from figworks import Figure, load_theme
from figworks.matplotlib import mpl_to_svg
from figworks.plotly import plotly_to_svg

OUT = Path(__file__).resolve().parent / "out"


def build() -> Figure:
    theme = load_theme(Path(__file__).with_suffix(".md"))
    figure = Figure("180mm", "130mm", theme=theme)
    figure.rect(x=0, y=0, width="180mm", height="130mm", fill="white", stroke="none")
    figure.text("One resonator, one typography", "10mm", "9mm", id="heading")

    scene = vecview.Scene(vecview.OrthographicCamera(azim_deg=30, elev_deg=25, scale=25), pad=8)
    scene.faces(
        1,
        vecview.box_faces(center=(0, 0, 0), size=(4, 2, 0.3)),
        cull=True,
        fill="#cbdcec",
        stroke=theme.color["ink"],
        stroke_width=theme.px("line.frame"),
        id="device",
    )
    scene.text(2, (0, 0, 1.5), "LC resonator", text_anchor="middle", **theme.vecview_text())
    figure.panel("device-panel", "10mm", "15mm", "70mm", "30mm").add(
        scene, id="device-scene", fit="none"
    )

    circuit = Circuit(140, 75, **theme.vecwire())
    circuit.node("tl", (25, 15))
    circuit.node("tr", (100, 15))
    circuit.node("bl", (25, 60))
    circuit.node("br", (100, 60))
    circuit.wire("tl", "tr")
    circuit.wire("bl", "br")
    circuit.capacitor("tl", "bl", id="capacitor")
    circuit.inductor("tr", "br", id="inductor")
    circuit.label("C", (10, 38), **theme.vecwire_label())
    circuit.label("L", (120, 38), **theme.vecwire_label())
    figure.panel("circuit-panel", "100mm", "15mm", "70mm", "30mm").add(
        circuit, id="lc-circuit", fit="none"
    )

    equation = vectex.render(r"$\omega_0 = 1/\sqrt{LC}$", **theme.vectex())
    figure.panel("equation-panel", "60mm", "46mm", "60mm", "8mm").add(
        equation, id="resonance", fit="none"
    )
    t = np.linspace(0, 3, 240)
    signal = np.cos(2 * np.pi * t)
    # Both plots retain their whole canvas at its natural physical size.
    with plt.rc_context(theme.rc()):
        mpl, ax = plt.subplots(figsize=(80 / 25.4, 58 / 25.4))
        mpl.subplots_adjust(left=0.19, right=0.96, bottom=0.22, top=0.85)
        ax.plot(t, signal)
        ax.set(xlabel="Time (s)", ylabel="Amplitude", title="Matplotlib")
        figure.panel("mpl-panel", "5mm", "60mm", "80mm", "58mm").add(
            mpl_to_svg(mpl, bbox_inches=None), id="mpl-response", fit="none"
        )
        plt.close(mpl)

    plot = go.Figure(go.Scatter(x=t, y=signal, mode="lines"))
    plot.update_layout(
        template=theme.plotly(),
        title={"text": "Plotly", "x": 0.5},
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        margin={"l": 50, "r": 12, "t": 32, "b": 48},
    )
    figure.panel("plotly-panel", "95mm", "60mm", "80mm", "58mm").add(
        plotly_to_svg(plot, width=302, height=219), id="plotly-response", fit="none"
    )
    figure.text("8 pt labels / 7 pt ticks — all sources placed at physical size", "10mm", "125mm")
    return figure


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    figure = build()
    for extension in ("svg", "pdf", "png"):
        figure.save(OUT / f"shared_typography.{extension}")
