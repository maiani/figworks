"""Build the picture at the top of the README.

It is the ``transmon_figure`` example -- a VecView device, a VecWire circuit, and
two Matplotlib panels with VecTeX labels -- placed whole on a white canvas, so
it reads on a dark page too.  Needs VecView, VecWire, and a TeX installation,
as the example does.

Usage:
    python docs/readme_figure.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from transmon_figure import build_figure  # noqa: E402

from figworks import Figure  # noqa: E402

OUT = ROOT / "docs" / "images" / "readme.svg"

if __name__ == "__main__":
    figure = build_figure()
    page = Figure(width=figure.width, height=figure.height)
    page.rect(x=0, y=0, width=figure.width, height=figure.height, fill="#ffffff", id="background")
    # A FigWorks figure is an SVG document like any other source.
    page.panel("figure", x=0, y=0, w=figure.width, h=figure.height).add(
        figure.document.to_string(), id="transmon"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    page.save(OUT)
    print(f"wrote {OUT}")
