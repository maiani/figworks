"""Placing content in a box: scaled to fit, or at its own size, and where in the box."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest
from lxml import etree

from figworks import Figure
from figworks.core.element import SVG_NS

# 12 pt x 6 pt is 16 px x 8 px; the viewBox is deliberately offset and in other units.
LABEL = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="12pt" height="6pt" viewBox="5 5 24 12">'
    '<rect id="mark" x="5" y="5" width="24" height="12"/></svg>'
)


def placed(
    figure: Figure, ctm: Callable[[etree._Element], np.ndarray]
) -> tuple[float, float, float, float]:
    """Document-px (left, top, width, height) of the label's rect."""
    rect = figure.document.root.find(f".//{{{SVG_NS}}}rect[@id='mark']")
    assert rect is not None
    m = ctm(rect)
    (x0, y0, _), (x1, y1, _) = m @ [5, 5, 1], m @ [29, 17, 1]
    return x0, y0, x1 - x0, y1 - y0


@pytest.mark.parametrize(
    ("align", "corner"),
    [
        ("center", (42.0, 26.0)),
        ("northwest", (10.0, 20.0)),
        ("south", (42.0, 32.0)),
        ("east", (74.0, 26.0)),
    ],
)
def test_fit_none_keeps_the_declared_size_at_the_aligned_point(
    align: str, corner: tuple[float, float], ctm: Callable[[etree._Element], np.ndarray]
) -> None:
    figure = Figure(width=100, height=60)
    panel = figure.panel("p", x=10, y=20, w=80, h=20)
    panel.add(LABEL, id="label", fit="none", align=align)
    assert placed(figure, ctm) == pytest.approx((*corner, 16.0, 8.0))


def test_fit_none_lets_large_content_overhang(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    figure = Figure(width=100, height=60)
    figure.panel("p", x=40, y=30, w=4, h=4).add(LABEL, id="label", fit="none")
    assert placed(figure, ctm) == pytest.approx((34.0, 28.0, 16.0, 8.0))


def test_fit_content_places_the_scaled_content_by_align(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    figure = Figure(width=100, height=60)
    panel = figure.panel("p", x=10, y=20, w=80, h=20)
    panel.add(LABEL, id="label", align="west")  # scaled to 40 x 20, flush left
    assert placed(figure, ctm) == pytest.approx((10.0, 20.0, 40.0, 20.0), abs=1e-3)  # %g scale


def test_stretching_honours_a_viewbox_that_does_not_start_at_the_origin(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    """VecView fits a scene's viewBox to its content, so its origin is rarely 0, 0."""
    figure = Figure(width=100, height=60)
    panel = figure.panel("p", x=10, y=20, w=48, h=36)
    panel.add(LABEL, id="label", preserve_aspect_ratio=False)  # 24 x 12 stretched 2 x 3
    assert placed(figure, ctm) == pytest.approx((10.0, 20.0, 48.0, 36.0))


def test_an_unknown_alignment_is_refused() -> None:
    figure = Figure(width=100, height=60)
    panel = figure.panel("p", x=0, y=0, w=10, h=10)
    with pytest.raises(ValueError, match="align must be one of"):
        panel.add(LABEL, fit="none", align="top-left")
