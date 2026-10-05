"""Arrow element factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import svg

from figworks.core.document import SVGDocument
from figworks.core.element import svg_kwargs, svg_to_lxml
from figworks.core.units import px_decimal

if TYPE_CHECKING:
    from lxml import etree


def ensure_arrow_marker(document: SVGDocument, stroke: str = "black") -> etree._Element:
    marker_id = "figworks-arrowhead"
    existing = document.root.find(f".//*[@id='{marker_id}']")
    if existing is not None:
        return existing
    marker = svg_to_lxml(
        svg.Marker(
            id=marker_id,
            markerWidth=8,
            markerHeight=8,
            refX=7,
            refY=4,
            orient="auto",
            markerUnits="strokeWidth",
        )
    )
    marker.append(
        svg_to_lxml(
            svg.Path(fill=stroke, class_=["figworks-arrowhead-path"]),
            raw={"d": "M 0 0 L 8 4 L 0 8 z"},
        )
    )
    document.defs().append(marker)
    return marker


def line_arrow(
    x1: str | int | float,
    y1: str | int | float,
    x2: str | int | float,
    y2: str | int | float,
    **attrs: Any,
) -> etree._Element:
    attrs.setdefault("marker_end", "url(#figworks-arrowhead)")
    return svg_to_lxml(
        svg.Line(
            x1=px_decimal(x1),
            y1=px_decimal(y1),
            x2=px_decimal(x2),
            y2=px_decimal(y2),
            **svg_kwargs(attrs),
        )
    )
