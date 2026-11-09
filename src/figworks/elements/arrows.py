"""Arrow element factories."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import svg

from figworks.core.document import SVGDocument
from figworks.core.element import svg_kwargs, svg_to_lxml
from figworks.core.units import px_decimal

if TYPE_CHECKING:
    from lxml import etree


def ensure_arrow_marker(
    document: SVGDocument, stroke: str, *, length: float, width: float
) -> etree._Element:
    """The arrowhead for ``stroke``-coloured lines, defined once per colour and shape.

    ``length`` and ``width`` are in stroke widths, so the head scales with its
    line. The id is stable, such as ``figworks-arrowhead-c2185b-8x8``.
    """
    shape = f"{length:g}x{width:g}".replace(".", "_")
    marker_id = f"figworks-arrowhead-{re.sub(r'[^0-9A-Za-z]+', '', stroke) or 'none'}-{shape}"
    existing = document.root.find(f".//*[@id='{marker_id}']")
    if existing is not None:
        return existing
    marker = svg_to_lxml(
        svg.Marker(
            id=marker_id,
            markerWidth=px_decimal(length),
            markerHeight=px_decimal(width),
            refX=px_decimal(length - 1),  # the line's butt end stays hidden in the head
            refY=px_decimal(width / 2),
            orient="auto",
            markerUnits="strokeWidth",
        )
    )
    marker.append(
        svg_to_lxml(
            svg.Path(fill=stroke, class_=["figworks-arrowhead-path"]),
            raw={"d": f"M 0 0 L {length:g} {width / 2:g} L 0 {width:g} z"},
        )
    )
    document.defs().append(marker)
    return marker


def line_arrow(
    x1: str | int | float,
    y1: str | int | float,
    x2: str | int | float,
    y2: str | int | float,
    *,
    marker: str,
    **attrs: Any,
) -> etree._Element:
    """A line ending in the arrowhead with id ``marker``, from :func:`ensure_arrow_marker`."""
    attrs["marker_end"] = f"url(#{marker})"
    return svg_to_lxml(
        svg.Line(
            x1=px_decimal(x1),
            y1=px_decimal(y1),
            x2=px_decimal(x2),
            y2=px_decimal(y2),
            **svg_kwargs(attrs),
        )
    )
