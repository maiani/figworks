"""Native SVG shape factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import svg

from figforge.core.document import svg_kwargs, svg_to_lxml
from figforge.core.units import to_px

if TYPE_CHECKING:
    from lxml import etree


def line(
    x1: str | int | float,
    y1: str | int | float,
    x2: str | int | float,
    y2: str | int | float,
    **attrs: Any,
) -> etree._Element:
    return svg_to_lxml(
        svg.Line(
            x1=f"{to_px(x1):g}",
            y1=f"{to_px(y1):g}",
            x2=f"{to_px(x2):g}",
            y2=f"{to_px(y2):g}",
            **svg_kwargs(attrs),
        )
    )


def rect(
    x: str | int | float,
    y: str | int | float,
    width: str | int | float,
    height: str | int | float,
    **attrs: Any,
) -> etree._Element:
    return svg_to_lxml(
        svg.Rect(
            x=f"{to_px(x):g}",
            y=f"{to_px(y):g}",
            width=f"{to_px(width):g}",
            height=f"{to_px(height):g}",
            **svg_kwargs(attrs),
        )
    )


def circle(
    cx: str | int | float,
    cy: str | int | float,
    r: str | int | float,
    **attrs: Any,
) -> etree._Element:
    return svg_to_lxml(
        svg.Circle(cx=f"{to_px(cx):g}", cy=f"{to_px(cy):g}", r=f"{to_px(r):g}", **svg_kwargs(attrs))
    )


def ellipse(
    cx: str | int | float,
    cy: str | int | float,
    rx: str | int | float,
    ry: str | int | float,
    **attrs: Any,
) -> etree._Element:
    return svg_to_lxml(
        svg.Ellipse(
            cx=f"{to_px(cx):g}",
            cy=f"{to_px(cy):g}",
            rx=f"{to_px(rx):g}",
            ry=f"{to_px(ry):g}",
            **svg_kwargs(attrs),
        )
    )


def polyline(
    points: list[tuple[str | int | float, str | int | float]] | str,
    **attrs: Any,
) -> etree._Element:
    if not isinstance(points, str):
        points = " ".join(f"{to_px(x):g},{to_px(y):g}" for x, y in points)
    return svg_to_lxml(svg.Polyline(points=points, **svg_kwargs(attrs)))


def path(d: str, **attrs: Any) -> etree._Element:
    return svg_to_lxml(svg.Path(d=d, **svg_kwargs(attrs)))
