"""Native SVG text factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import svg

from figforge.core.document import svg_kwargs, svg_to_lxml
from figforge.core.units import to_px

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
                x=f"{to_px(x):g}",
                y=f"{to_px(y):g}",
                **svg_kwargs(attrs),
            )
        )

    tspans = [
        svg.TSpan(
            text=line,
            x=f"{to_px(x):g}",
            dy="0" if index == 0 else "1.2em",
        )
        for index, line in enumerate(lines)
    ]
    return svg_to_lxml(
        svg.Text(
            elements=tspans,
            x=f"{to_px(x):g}",
            y=f"{to_px(y):g}",
            **svg_kwargs(attrs),
        )
    )
