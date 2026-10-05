"""Build the picture at the top of the README.

It is the ``vecview_panel`` example -- a VecView scene and a Matplotlib plot
composed into one labelled figure -- on a white canvas, so it reads on a dark
page too.  Needs VecView installed, as the example does.

Usage:
    python docs/readme_figure.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from vecview_panel import build_figure  # noqa: E402

OUT = ROOT / "docs" / "images" / "readme.svg"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build_figure(background="#ffffff").save(OUT)
    print(f"wrote {OUT}")
