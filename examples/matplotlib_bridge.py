"""Two-way Matplotlib <-> SVG workflows: placeholders/fill, grid layout, and
the SVG <-> Matplotlib bridge (SVG as a Matplotlib object and vice versa)."""

import matplotlib.pyplot as plt

from figforge import Figure, display_svg, layout_svgs
from figforge.matplotlib import connect, insert, mpl_to_svg, svg_to_image_artist


def make_plot(ylabel):
    mpl_fig, ax = plt.subplots(figsize=(3, 2))
    ax.plot([0, 1, 2], [0, 1, 0])
    ax.set_ylabel(ylabel)
    return mpl_fig


def panel_svg(ylabel):
    return mpl_to_svg(make_plot(ylabel))


# 1. Reserve a region in a FigForge figure, then fill it by id.
fig = Figure(width="160mm", height="80mm")
fig.placeholder("slot", x="10mm", y="10mm", w="70mm", h="55mm", label="shared slot")
fig.text("Fill a placeholder by id", x="10mm", y="72mm")
fig.fill("slot", make_plot("shared"))
fig.save("placeholder_fill.svg")

# 2. Assemble several panels into a single labelled grid figure.
grid = layout_svgs(
    [panel_svg("a"), panel_svg("b"), panel_svg("c"), panel_svg("d")],
    labels=["a", "b", "c", "d"],
    outline=True,
    shape=(2, 2),
)
grid.save("grid_layout.svg")

# 3. SVG as a Matplotlib object: place an SVG image artist in an axes.
mpl_fig, ax = plt.subplots()
artist = svg_to_image_artist(panel_svg("embedded"), gid="embedded-svg")
ax.add_artist(artist)

# 4. Reserve a placeholder in Matplotlib, then swap in vector SVG by id.
connect(ax, "slot", 0.1, 0.1, 0.7, 0.7)
assembled = insert({"slot": panel_svg("injected")}, fig=mpl_fig)
with open("matplotlib_insert.svg", "w", encoding="utf-8") as handle:
    handle.write(assembled)

# 5. Display a figure inline in a notebook (no-op without IPython).
display_svg(fig)

print("wrote placeholder_fill.svg, grid_layout.svg, matplotlib_insert.svg")
