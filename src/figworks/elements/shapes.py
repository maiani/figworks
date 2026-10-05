"""Native SVG shape factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import svg

from figworks.core.element import svg_kwargs, svg_to_lxml
from figworks.core.units import fmt_px, px_decimal

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
            x1=px_decimal(x1),
            y1=px_decimal(y1),
            x2=px_decimal(x2),
            y2=px_decimal(y2),
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
            x=px_decimal(x),
            y=px_decimal(y),
            width=px_decimal(width),
            height=px_decimal(height),
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
        svg.Circle(cx=px_decimal(cx), cy=px_decimal(cy), r=px_decimal(r), **svg_kwargs(attrs))
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
            cx=px_decimal(cx),
            cy=px_decimal(cy),
            rx=px_decimal(rx),
            ry=px_decimal(ry),
            **svg_kwargs(attrs),
        )
    )


def polyline(
    points: list[tuple[str | int | float, str | int | float]] | str,
    **attrs: Any,
) -> etree._Element:
    if not isinstance(points, str):
        points = " ".join(f"{fmt_px(x)},{fmt_px(y)}" for x, y in points)
    return svg_to_lxml(svg.Polyline(**svg_kwargs(attrs)), raw={"points": points})


def path(d: str, **attrs: Any) -> etree._Element:
    return svg_to_lxml(svg.Path(**svg_kwargs(attrs)), raw={"d": d})
