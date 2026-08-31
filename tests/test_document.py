import pytest
from lxml import etree

from figforge import Figure
from figforge.core.document import SVGDocument, element_box
from figforge.core.element import SVG_NS
from figforge.core.units import to_px


def test_document_creation_and_group():
    document = SVGDocument("100mm", "50mm")
    document.group(id="panel", class_="figforge-panel")
    output = document.to_string()

    assert 'width="100mm"' in output
    assert 'height="50mm"' in output
    assert 'id="panel"' in output
    assert all(
        not isinstance(node.tag, str) or node.tag.startswith(f"{{{SVG_NS}}}")
        for node in document.root.iter()
    )


def test_import_svg_group():
    document = SVGDocument("100px", "100px")
    document.import_svg(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="x">Hi</text></svg>', id="imported"
    )

    output = document.to_string()
    assert 'id="imported"' in output
    assert 'id="x"' in output


def test_group_box_contains_its_painted_children():
    group = etree.fromstring(
        '<g xmlns="http://www.w3.org/2000/svg"><path d="M 20 30 L 60 30 L 60 80 L 20 80 z"/></g>'
    )

    assert element_box(group) == (20.0, 30.0, 40.0, 50.0)


def test_root_viewbox_binds_user_units_to_the_physical_canvas():
    """Elements are placed in px, so the mm canvas needs a px viewBox.

    Without it a renderer maps one user unit to one px at its own default 96 DPI
    while sizing the canvas from the physical attributes, so any export above
    96 DPI leaves the content in a corner at the wrong scale.
    """
    document = SVGDocument("120mm", "70mm")

    assert document.root.get("viewBox") is not None
    min_x, min_y, width, height = (
        float(value) for value in document.root.get("viewBox").split()
    )
    assert (min_x, min_y) == (0.0, 0.0)
    assert width == pytest.approx(to_px("120mm"))
    assert height == pytest.approx(to_px("70mm"))


def test_viewbox_aspect_matches_the_declared_canvas():
    """A mismatch would letterbox or stretch every panel in the figure."""
    document = SVGDocument("170mm", "72mm")
    _, _, width, height = (float(value) for value in document.root.get("viewBox").split())

    assert width / height == pytest.approx(170.0 / 72.0)


def test_px_canvas_viewbox_is_one_to_one():
    document = SVGDocument("640px", "480px")

    _, _, width, height = (float(value) for value in document.root.get("viewBox").split())
    assert (width, height) == (640.0, 480.0)


def test_panel_geometry_stays_inside_the_viewbox():
    """A panel specified in mm must land within the px user-unit space."""
    figure = Figure(width="170mm", height="76mm")
    panel = figure.panel("main", x="12mm", y="12mm", w="72mm", h="56mm")
    _, _, width, height = (
        float(value) for value in figure.document.root.get("viewBox").split()
    )

    assert 0 <= panel.x < panel.x + panel.w <= width
    assert 0 <= panel.y < panel.y + panel.h <= height
