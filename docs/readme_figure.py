"""Build the picture at the top of the README.

It is the ``transmon_figure`` example -- a VecView device, a VecWire circuit, and
two Matplotlib panels with VecTeX labels -- whose white page lets it read on a
dark page too.  Needs VecView, VecWire, and a TeX installation,
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

OUT = ROOT / "docs" / "images" / "readme.svg"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build_figure().save(OUT)
    print(f"wrote {OUT}")
