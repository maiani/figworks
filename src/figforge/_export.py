"""Internal SVG export helpers."""

from __future__ import annotations

from pathlib import Path

import cairosvg


def svg_to_pdf(svg_string: str, path: str | Path) -> None:
    cairosvg.svg2pdf(bytestring=svg_string.encode("utf-8"), write_to=str(path))


def svg_to_png(svg_string: str, path: str | Path, dpi: int = 300) -> None:
    # cairosvg's `dpi` only converts physical units, leaving px lengths at one
    # pixel each. Resolving at the CSS 96 DPI and scaling rasterizes every unit
    # at `dpi`.
    cairosvg.svg2png(
        bytestring=svg_string.encode("utf-8"), write_to=str(path), dpi=96, scale=dpi / 96
    )
