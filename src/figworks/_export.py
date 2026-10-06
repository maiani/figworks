"""Internal SVG export helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cairosvg
from cairosvg.surface import PDFSurface, cairo


class _ReproduciblePDF(PDFSurface):
    """CairoSVG's PDF surface without the creation date cairo stamps by default.

    The date makes every PDF differ from the last; an empty value omits it.
    """

    def _create_surface(self, width: float, height: float) -> tuple[Any, float, float]:
        surface, width, height = super()._create_surface(width, height)
        surface.set_metadata(cairo.PDF_METADATA_CREATE_DATE, "")
        return surface, width, height


def svg_to_pdf(svg_string: str, path: str | Path) -> None:
    _ReproduciblePDF.convert(bytestring=svg_string.encode("utf-8"), write_to=str(path))


def svg_to_png(svg_string: str, path: str | Path, dpi: int = 300) -> None:
    # cairosvg's `dpi` only converts physical units, leaving px lengths at one
    # pixel each. Resolving at the CSS 96 DPI and scaling rasterizes every unit
    # at `dpi`.
    cairosvg.svg2png(
        bytestring=svg_string.encode("utf-8"), write_to=str(path), dpi=96, scale=dpi / 96
    )
