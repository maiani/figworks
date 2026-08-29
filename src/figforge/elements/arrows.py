"""Arrow element factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import svg

from figforge.core.document import SVGDocument, svg_kwargs, svg_to_lxml
from figforge.core.units import to_px

if TYPE_CHECKING:
    from lxml import etree


def ensure_arrow_marker(document: SVGDocument, stroke: str = "black") -> etree._Element:
    marker_id = "figforge-arrowhead"
    existing = document.root.xpath(f".//*[@id='{marker_id}']")
    if existing:
        return existing[0]
    marker = svg_to_lxml(
        svg.Marker(
            id=marker_id,
            markerWidth=8,
            markerHeight=8,
            refX=7,
            refY=4,
            orient="auto",
            markerUnits="strokeWidth",
            elements=[
                svg.Path(
                    d="M 0 0 L 8 4 L 0 8 z",
                    fill=stroke,
                    class_="figforge-arrowhead-path",
                )
            ],
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
    attrs.setdefault("marker_end", "url(#figforge-arrowhead)")
    return svg_to_lxml(
        svg.Line(
            x1=f"{to_px(x1):g}",
            y1=f"{to_px(y1):g}",
            x2=f"{to_px(x2):g}",
            y2=f"{to_px(y2):g}",
            **svg_kwargs(attrs),
        )
    )
