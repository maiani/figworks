"""Optional Plotly static SVG export for the ordinary placement API."""

from __future__ import annotations

import re
from typing import Any

from lxml import etree

from figworks.core.element import _rewrite_references, parse_svg


def plotly_to_svg(figure: Any, *, width: int | None = None, height: int | None = None) -> str:
    """Export a Plotly figure or figure dictionary as a complete SVG document.

    Requires ``figworks[plotly]`` and Chrome/Chromium for Kaleido. Dimensions
    are CSS pixels; omitted dimensions follow Plotly's layout/export defaults.
    Place the returned string with ``Figure.add`` or ``Panel.add``. Export is
    static, and WebGL traces may contain raster images. Plotly's generated ids
    and trace classes are normalized for repeatable output in a fixed renderer
    environment. The input figure and global Plotly defaults are not modified.
    """
    for name, value in (("width", width), ("height", height)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
        ):
            raise ValueError(f"{name} must be a positive integer in pixels")
    try:
        import kaleido  # noqa: F401
        import plotly.io as pio
    except ImportError as exc:
        raise ImportError('Plotly SVG export requires: pip install "figworks[plotly]"') from exc

    svg = pio.to_image(figure, format="svg", width=width, height=height, scale=1)
    root = parse_svg(svg.decode("utf-8"), recover=False)
    ids = [old for node in root.iter() if (old := node.get("id"))]
    renamed = {old: f"plotly-{index}" for index, old in enumerate(ids)}
    trace_uids: dict[str, str] = {}

    def stable_class(match: re.Match[str]) -> str:
        prefix, uid, suffix = match.groups()
        stable = trace_uids.setdefault(uid, f"uid{len(trace_uids)}")
        return f"{prefix}{stable}{suffix or ''}"

    for node in root.iter():
        if old := node.get("id"):
            node.set("id", renamed[old])
        # Trace uids also appear in colorbar and colorbar tick classes.
        if classes := node.get("class"):
            node.set(
                "class",
                re.sub(r"(?<!\S)(trace|[xy]?cb)([0-9a-f]{6})(tick)?(?!\S)", stable_class, classes),
            )
    _rewrite_references(root, renamed)
    return etree.tostring(root, encoding="unicode")
