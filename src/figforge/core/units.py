"""Small physical-unit parser for SVG layout."""

from __future__ import annotations

import re
from decimal import Decimal

_UNIT_TO_PX = {
    "px": 1.0,
    "pt": 96.0 / 72.0,
    "mm": 96.0 / 25.4,
    "cm": 96.0 / 2.54,
    "in": 96.0,
}

_UNIT_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(px|pt|mm|cm|in)?\s*$")


def to_px(value: str | float) -> float:
    """Convert a supported unit value to CSS/SVG pixels."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        raise TypeError(f"Expected a string or number, got {type(value).__name__}")

    match = _UNIT_RE.match(value)
    if not match:
        raise ValueError(f"Unsupported unit value: {value!r}")

    magnitude = float(match.group(1))
    unit = match.group(2) or "px"
    return magnitude * _UNIT_TO_PX[unit]


def svg_length(value: str | float) -> str:
    """Return a value suitable for an SVG length attribute."""

    if not isinstance(value, str):
        return f"{float(value):g}px"
    to_px(value)
    return value.strip()


def fmt_px(value: str | float) -> str:
    """Format a numeric value as an SVG-friendly pixel number."""

    return f"{to_px(value):g}"


def px_decimal(value: str | float) -> Decimal:
    """Return a pixel value as a ``Decimal`` that svg.py serializes like :func:`fmt_px`.

    svg.py writes floats with ``repr`` (``10.0``); a ``Decimal`` built from the
    ``%g`` string keeps the short form (``10``).
    """

    return Decimal(fmt_px(value))
