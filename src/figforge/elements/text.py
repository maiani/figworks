"""Native SVG text factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import svg

from figforge.core.element import svg_kwargs, svg_to_lxml
from figforge.core.units import px_decimal

if TYPE_CHECKING:
    from lxml import etree


def text_element(
    value: str,
    x: str | int | float,
    y: str | int | float,
    **attrs: Any,
) -> etree._Element:
    lines = value.splitlines() or [""]
    if len(lines) == 1:
        return svg_to_lxml(
            svg.Text(
                text=lines[0],
                x=px_decimal(x),
                y=px_decimal(y),
                **svg_kwargs(attrs),
            )
        )

    tspans: list[svg.Element] = [
        svg.TSpan(
            text=line,
            x=px_decimal(x),
            dy=0 if index == 0 else svg.Length(1.2, "em"),
        )
        for index, line in enumerate(lines)
    ]
    return svg_to_lxml(
        svg.Text(
            elements=tspans,
            x=px_decimal(x),
            y=px_decimal(y),
            **svg_kwargs(attrs),
        )
    )
