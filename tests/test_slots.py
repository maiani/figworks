"""Filling anchor groups with content kept at its own physical size."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest
from lxml import etree

from figworks import Figure
from figworks.core.element import SVG_NS, accumulated_scale, svg_physical_size

# 12 pt x 6 pt is 16 px x 8 px; the viewBox is deliberately in other units.
LABEL = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="12pt" height="6pt" viewBox="5 5 24 12">'
    '<rect id="mark" x="5" y="5" width="24" height="12"/></svg>'
)


def placed_box(
    figure: Figure, ctm: Callable[[etree._Element], np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """Document-px corners of the label's rect."""
    rect = figure.document.root.find(f".//{{{SVG_NS}}}rect[@id='mark']")
    assert rect is not None
    m = ctm(rect)
    lo = m @ [5, 5, 1]
    hi = m @ [29, 17, 1]
    return lo[:2], hi[:2]


def figure_with_slot(scale: float = 3.0, align: str | None = "west") -> Figure:
    """A slot anchored at document (40, 30) inside a group scaled by ``scale``."""
    figure = Figure(width=200, height=100)
    outer = figure.document.group(transform=f"translate(10 0) scale({scale:g})")
    slot = figure.document.group(
        id="slot", transform=f"translate({30 / scale:g} {30 / scale:g})", parent=outer
    )
    if align is not None:
        slot.set("data-align", align)
    return figure


def test_physical_size_honours_units() -> None:
    assert svg_physical_size(LABEL) == pytest.approx((16.0, 8.0))


def test_physical_size_falls_back_to_the_viewbox() -> None:
    sizeless = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"/>'
    assert svg_physical_size(sizeless) == (30.0, 20.0)


def test_accumulated_scale_multiplies_through_ancestors() -> None:
    figure = Figure(width=100, height=100)
    outer = figure.document.group(transform="translate(5 5) scale(2)")
    inner = figure.document.group(transform="matrix(3 0 0 3 1 1)", parent=outer)
    assert accumulated_scale(inner) == pytest.approx(6.0)


@pytest.mark.parametrize("scale", [0.5, 1.0, 3.0])
def test_content_keeps_its_physical_size_whatever_the_scale(
    scale: float, ctm: Callable[[etree._Element], np.ndarray]
) -> None:
    figure = figure_with_slot(scale=scale)
    figure.fill_slot("slot", LABEL)
    lo, hi = placed_box(figure, ctm)
    assert hi - lo == pytest.approx([16.0, 8.0])


@pytest.mark.parametrize(
    ("align", "corner"),
    [
        ("west", (40.0, 26.0)),
        ("center", (32.0, 26.0)),
        ("east", (24.0, 26.0)),
        ("north", (32.0, 30.0)),
        ("southeast", (24.0, 22.0)),
    ],
)
def test_alignment_puts_that_point_of_the_box_on_the_anchor(
    align: str, corner: tuple[float, float], ctm: Callable[[etree._Element], np.ndarray]
) -> None:
    figure = figure_with_slot(align=align)
    figure.fill_slot("slot", LABEL)
    lo, _ = placed_box(figure, ctm)
    assert lo == pytest.approx(corner)


def test_alignment_defaults_to_center(ctm: Callable[[etree._Element], np.ndarray]) -> None:
    figure = figure_with_slot(align=None)
    figure.fill_slot("slot", LABEL)
    lo, _ = placed_box(figure, ctm)
    assert lo == pytest.approx((32.0, 26.0))


def test_content_lands_inside_the_slot_group() -> None:
    figure = figure_with_slot()
    wrapper = figure.fill_slot("slot", LABEL)
    assert wrapper.getparent().get("id") == "slot"


def test_unknown_alignment_is_reported() -> None:
    figure = figure_with_slot(align="left")
    with pytest.raises(ValueError, match="data-align"):
        figure.fill_slot("slot", LABEL)


def test_missing_target_is_reported() -> None:
    with pytest.raises(KeyError, match="nope"):
        figure_with_slot().fill_slot("nope", LABEL)


def test_content_without_intrinsic_size_is_rejected() -> None:
    sizeless = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 0 0"><g/></svg>'
    with pytest.raises(ValueError, match="intrinsic size"):
        figure_with_slot().fill_slot("slot", sizeless)


# A 100 x 50 source whose slot at (40, 20) already holds a 16 x 8 rect, aligned west.
HELD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 100 50">'
    '<rect id="ground" width="100" height="50" fill="none"/>'
    '<g id="pin" data-align="west" transform="translate(40 20)">'
    '<g transform="translate(0 -4)"><rect id="held" width="16" height="8"/></g></g></svg>'
)


def held_box(
    figure: Figure, ctm: Callable[[etree._Element], np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    """Document-px corners of the held rect."""
    rect = figure.document.root.find(f".//{{{SVG_NS}}}rect[@id='held']")
    assert rect is not None
    m = ctm(rect)
    return (m @ [0, 0, 1])[:2], (m @ [16, 8, 1])[:2]


@pytest.mark.parametrize("scale", [0.5, 1.0, 2.0])
def test_held_content_keeps_its_size_while_the_source_scales(
    scale: float, ctm: Callable[[etree._Element], np.ndarray]
) -> None:
    figure = Figure(width=300, height=150)
    figure.add(HELD, x=0, y=0, w=100 * scale, h=50 * scale, id="scene")
    lo, hi = held_box(figure, ctm)
    assert hi - lo == pytest.approx([16.0, 8.0])
    # The anchor still moves with the scene; the content's west edge sits on it.
    assert lo == pytest.approx([40 * scale, 20 * scale - 4])


def test_held_content_keeps_its_size_in_a_filled_placeholder(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    figure = Figure(width=300, height=150)
    figure.placeholder("box", x=0, y=0, w=50, h=25)
    figure.fill("box", HELD)
    lo, hi = held_box(figure, ctm)
    assert hi - lo == pytest.approx([16.0, 8.0])


def test_a_placed_figure_does_not_shrink_its_held_content_twice(
    ctm: Callable[[etree._Element], np.ndarray],
) -> None:
    inner = Figure(width=300, height=150)
    inner.add(HELD, x=0, y=0, w=50, h=25, id="scene")
    outer = Figure(width=300, height=150)
    outer.add(inner.document.to_string(), x=0, y=0, w=150, h=75, id="figure")
    lo, hi = held_box(outer, ctm)
    assert hi - lo == pytest.approx([16.0, 8.0])


def test_an_empty_slot_is_left_for_fill_slot(ctm: Callable[[etree._Element], np.ndarray]) -> None:
    empty = HELD.replace(
        '<g transform="translate(0 -4)"><rect id="held" width="16" height="8"/></g>', ""
    )
    figure = Figure(width=300, height=150)
    figure.add(empty, x=0, y=0, w=50, h=25, id="scene")
    pin = figure.document.root.find(f".//{{{SVG_NS}}}g[@id='pin']")
    assert pin is not None and len(pin) == 0
    figure.fill_slot("pin", LABEL)
    lo, hi = placed_box(figure, ctm)
    assert hi - lo == pytest.approx([16.0, 8.0])
