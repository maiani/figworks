"""Helpers for displaying SVG output in notebooks and terminals."""

from __future__ import annotations

import base64


def display_svg(source: object) -> None:
    """Render an SVG as an inline image in a Jupyter notebook.

    Accepts an SVG string, a matplotlib figure, or a :class:`figworks.Figure`.
    Falls back gracefully when IPython is not available.
    """
    svg = _to_svg(source)
    try:
        from IPython.display import HTML, display
    except ImportError:
        print(svg)
        return
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    display(HTML(f'<img src="data:image/svg+xml;base64,{data}" alt="FigWorks SVG"/>'))


def _to_svg(source: object) -> str:
    from matplotlib.figure import Figure as MplFigure

    if isinstance(source, str):
        return source
    if isinstance(source, MplFigure):
        from figworks.matplotlib import mpl_to_svg

        return mpl_to_svg(source)
    to_string = getattr(getattr(source, "document", None), "to_string", None)
    if callable(to_string):
        svg = to_string()
        if isinstance(svg, str):
            return svg
    raise TypeError("Expected an SVG string, a matplotlib Figure, or a FigWorks Figure")
