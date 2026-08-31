"""Internal SVG export helpers."""

from __future__ import annotations

from pathlib import Path

import cairosvg


def svg_to_pdf(svg_string: str, path: str | Path) -> None:
    cairosvg.svg2pdf(bytestring=svg_string.encode("utf-8"), write_to=str(path))


def svg_to_png(svg_string: str, path: str | Path, dpi: int = 300) -> None:
    cairosvg.svg2png(bytestring=svg_string.encode("utf-8"), write_to=str(path), dpi=dpi)
