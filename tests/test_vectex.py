"""VecTeX fragments placed for real: the one sibling FigWorks requires.

These render TeX, so they skip without ``pdflatex`` and ``dvisvgm``; the CI job
that installs TeX fails instead if either is missing.
"""

from __future__ import annotations

import io
import shutil
from collections.abc import Callable

import numpy as np
import pytest
from lxml import etree

from figworks import Figure
from figworks.core.element import SVG_NS

vectex = pytest.importorskip("vectex")

pytestmark = pytest.mark.skipif(
    not (shutil.which("pdflatex") and shutil.which("dvisvgm")),
    reason="rendering TeX needs pdflatex and dvisvgm",
)


def equation_figure() -> Figure:
    fig = Figure(width="40mm", height="20mm")
    fraction = vectex.render(r"$\frac{a}{b} = c$", size_pt=10, id_prefix="eq")
    fig.panel("p", 0, 0, "40mm", "20mm").add(fraction, id="equation")
    return fig


def painted(fig: Figure) -> set[tuple[int, int, int]]:
    """The opaque colours a render of the figure paints."""
    import cairosvg
    from PIL import Image

    png = cairosvg.svg2png(bytestring=fig.document.to_string().encode(), dpi=192)
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    return {(r, g, b) for r, g, b, a in image.get_flattened_data() if a == 255}


def test_a_placed_equation_keeps_its_ids_and_its_bytes() -> None:
    fig = equation_figure()
    assert len(fig.select("#eq-root")) == 1
    assert fig.document.to_string() == equation_figure().document.to_string()


@pytest.mark.parametrize(
    "recolour",
    [
        lambda selection: selection.set_attr("color", "#ff0000"),
        lambda selection: selection.set_style(color="#ff0000"),
    ],
    ids=["attribute", "style"],
)
def test_recolouring_reaches_the_glyphs_and_the_fraction_bar(
    recolour: Callable[..., object],
) -> None:
    """VecTeX paints in currentColor; the bar is a stroke, which `fill` would miss."""
    fig = equation_figure()
    recolour(fig.select("#eq-root"))
    colours = painted(fig)
    assert (255, 0, 0) in colours
    assert (0, 0, 0) not in colours


def test_a_label_in_a_slot_keeps_its_point_size(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    """The fragment's document must declare pt, or the label lands at 3/4 size."""
    label = vectex.render("$x$", size_pt=8, id_prefix="lab")
    fig = Figure(width=200, height=100)
    outer = fig.document.group(transform="scale(3)")
    fig.document.group(id="slot", transform="translate(10 10)", parent=outer)
    fig.fill_slot("slot", label)

    root = fig.document.root.find(f".//{{{SVG_NS}}}g[@id='lab-root']")
    assert root is not None
    x0, _, width, _ = label.view_box
    left, right = ctm(root) @ [x0, 0, 1], ctm(root) @ [x0 + width, 0, 1]
    assert right[0] - left[0] == pytest.approx(label.width_px, rel=1e-4)  # %g transforms


def test_an_equation_placed_without_fitting_keeps_its_point_size(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    equation = vectex.render(r"$E = mc^2$", size_pt=8, id_prefix="einstein")
    fig = Figure(width="80mm", height="40mm")
    fig.panel("p", 0, 0, "80mm", "40mm").add(equation, id="eq", fit="none", align="north")

    root = fig.document.root.find(f".//{{{SVG_NS}}}g[@id='einstein-root']")
    assert root is not None
    x0, y0, width, _ = equation.view_box
    left, right = ctm(root) @ [x0, y0, 1], ctm(root) @ [x0 + width, y0, 1]
    assert right[0] - left[0] == pytest.approx(equation.width_px, rel=1e-4)
    assert left[1] == pytest.approx(0.0, abs=1e-3)  # flush with the panel's top
